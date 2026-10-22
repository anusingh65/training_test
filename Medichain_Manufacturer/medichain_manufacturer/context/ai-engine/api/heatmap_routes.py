"""
Geographic Heatmap Routes for MediChain AI Engine.

Endpoints:
  GET /api/heatmap-data      -- Compute and return heatmap data points for the
                                frontend visualisation layer.
  GET /api/heatmap-zone-risk -- Assess the risk level at a specific GPS
                                coordinate.
  GET /api/heatmap-stats     -- Return summary statistics about the heatmap
                                data store (event counts, active hotspots, etc.).
  POST /api/heatmap-event    -- Manually inject a heatmap event (for testing
                                or external integrations).

The HeatmapEngine uses DBSCAN clustering on flagged scan events with
exponential time decay to generate geographic risk intensities.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Response models                                                            #
# --------------------------------------------------------------------------- #

class HeatmapPoint(BaseModel):
    """A single heatmap data point for frontend rendering."""
    lat: float
    lng: float
    intensity: float = Field(..., ge=0.0, le=1.0)
    severity: Optional[str] = None
    label: Optional[str] = None
    event_count: Optional[int] = None


class HeatmapDataResponse(BaseModel):
    """Full heatmap response including data points, clusters, and stats."""
    heatmap_points: List[List[float]] = Field(
        ..., description="Array of [lat, lng, intensity] triples"
    )
    clusters: List[Dict[str, Any]] = Field(
        default_factory=list, description="DBSCAN cluster summaries"
    )
    predicted_hotspots: List[Dict[str, Any]] = Field(
        default_factory=list, description="Emerging hotspot predictions"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics"
    )
    processing_time_ms: float = 0.0


class ZoneRiskResponse(BaseModel):
    """Risk assessment for a specific geographic zone."""
    risk_level: str
    nearest_cluster: Optional[Dict[str, Any]] = None
    distance_km: Optional[float] = None


class HeatmapEventInput(BaseModel):
    """Input for manually injecting a heatmap event."""
    lat: float = Field(..., description="Latitude in decimal degrees")
    lng: float = Field(..., description="Longitude in decimal degrees")
    flag_type: str = Field("flagged_medium", description="One of: normal, flagged_low, flagged_medium, flagged_high, velocity_anomaly")
    timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp; defaults to now")
    label: Optional[str] = Field(None, description="Human-readable event label")
    medicine_id: Optional[int] = Field(None, description="Associated medicine ID")


class HeatmapStatsResponse(BaseModel):
    """Summary statistics about the heatmap data store."""
    total_points: int
    total_clusters: int
    predicted_hotspots: int
    last_computed: Optional[str] = None


# --------------------------------------------------------------------------- #
#  In-memory cache for computed heatmap results                               #
# --------------------------------------------------------------------------- #

# Simple cache to avoid recomputing the heatmap on every request.
_heatmap_cache: Dict[str, Any] = {
    "result": None,
    "timestamp": 0.0,
    "ttl_seconds": 30.0,  # cache for 30 seconds
}

# In-memory event store for injected events (supplements seed data).
_injected_events: List[Dict[str, Any]] = []


# --------------------------------------------------------------------------- #
#  Routes                                                                     #
# --------------------------------------------------------------------------- #

@router.get("/heatmap-data", response_model=HeatmapDataResponse)
async def get_heatmap_data(
    request: Request,
    time_window: str = Query("7d", description="Time window: 1h, 6h, 24h, 7d, 30d, 90d, all"),
    min_severity: str = Query("low", description="Minimum severity to include: low, medium, high, critical"),
    force_refresh: bool = Query(False, description="Bypass cache and recompute"),
):
    """Compute and return heatmap data for the frontend map visualisation.

    The heatmap is built from:
      - Seed data (known Indian pharma hotspots loaded at startup)
      - Injected events (from POST /api/heatmap-event or the event listener)
      - Real-time blockchain events (if the event listener is running)

    Results are cached for 30 seconds to avoid redundant computation.  Pass
    ``force_refresh=true`` to bypass the cache.

    The response includes:
      - ``heatmap_points``: array of [lat, lng, intensity] triples for the
        heatmap layer.
      - ``clusters``: DBSCAN cluster summaries with center coordinates,
        radius, event count, and severity.
      - ``predicted_hotspots``: clusters predicted to grow significantly.
      - ``stats``: summary counts.
    """
    start_time = time.perf_counter()

    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(
            status_code=503,
            detail="HeatmapEngine is not initialised.",
        )

    # Check cache.
    cache_key = f"{time_window}:{min_severity}"
    now = time.time()
    if (
        not force_refresh
        and _heatmap_cache["result"] is not None
        and _heatmap_cache.get("key") == cache_key
        and (now - _heatmap_cache["timestamp"]) < _heatmap_cache["ttl_seconds"]
    ):
        cached = _heatmap_cache["result"]
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        cached["processing_time_ms"] = round(elapsed_ms, 2)
        return HeatmapDataResponse(**cached)

    # Build the scan events list from all available sources.
    scan_events = _build_scan_events(request)

    # Apply time window filter.
    reference_time = datetime.utcnow()
    time_window_map = {
        "1h": 3600,
        "6h": 6 * 3600,
        "24h": 24 * 3600,
        "7d": 7 * 86400,
        "30d": 30 * 86400,
        "90d": 90 * 86400,
        "all": 0,
    }
    window_seconds = time_window_map.get(time_window, 7 * 86400)

    if window_seconds > 0:
        cutoff = reference_time.timestamp() - window_seconds
        filtered_events = []
        for ev in scan_events:
            ts = ev.get("timestamp")
            if ts is None:
                filtered_events.append(ev)
                continue
            if isinstance(ts, (int, float)):
                if ts >= cutoff:
                    filtered_events.append(ev)
            elif isinstance(ts, str):
                # Try to parse ISO timestamp.
                try:
                    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if parsed.timestamp() >= cutoff:
                        filtered_events.append(ev)
                except (ValueError, TypeError):
                    filtered_events.append(ev)
            else:
                filtered_events.append(ev)
    else:
        filtered_events = scan_events

    # Apply minimum severity filter.
    severity_order = {"normal": 0, "flagged_low": 1, "flagged_medium": 2, "flagged_high": 3, "velocity_anomaly": 4}
    severity_name_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    min_sev_threshold = severity_name_map.get(min_severity, 0)

    if min_sev_threshold > 0:
        filtered_events = [
            ev for ev in filtered_events
            if severity_order.get(ev.get("flag_type", "normal"), 0) >= min_sev_threshold
        ]

    # Compute heatmap.
    try:
        heatmap_result = heatmap_engine.compute_heatmap(
            scan_events=filtered_events,
            reference_time=reference_time,
        )
    except Exception as exc:
        logger.error("HeatmapEngine.compute_heatmap() failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Heatmap computation failed: {exc}",
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    heatmap_result["processing_time_ms"] = round(elapsed_ms, 2)

    # Cache the result.
    _heatmap_cache["result"] = heatmap_result
    _heatmap_cache["timestamp"] = now
    _heatmap_cache["key"] = cache_key

    return HeatmapDataResponse(**heatmap_result)


@router.get("/heatmap-zone-risk", response_model=ZoneRiskResponse)
async def get_zone_risk(
    request: Request,
    lat: float = Query(..., description="Latitude of the zone center"),
    lng: float = Query(..., description="Longitude of the zone center"),
):
    """Assess the risk level at a specific geographic coordinate.

    The risk is determined by proximity to the nearest cached cluster from
    the most recent heatmap computation:
      - **critical**: within the cluster radius
      - **high**: within 2x the cluster radius
      - **medium**: within 10 km
      - **low**: farther than 10 km from any cluster

    Returns the risk level, nearest cluster details, and distance.
    """
    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(
            status_code=503,
            detail="HeatmapEngine is not initialised.",
        )

    try:
        zone_risk = heatmap_engine.get_zone_risk_level(lat, lng)
    except Exception as exc:
        logger.error("get_zone_risk_level(%.6f, %.6f) failed: %s", lat, lng, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Zone risk assessment failed: {exc}",
        )

    return ZoneRiskResponse(**zone_risk)


@router.get("/heatmap-stats", response_model=HeatmapStatsResponse)
async def get_heatmap_stats(request: Request):
    """Return summary statistics about the heatmap data store.

    Includes total cached heatmap points, cluster count, number of predicted
    hotspots, and the timestamp of the last computation.
    """
    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(status_code=503, detail="HeatmapEngine is not initialised.")

    total_points = len(heatmap_engine.heatmap_points)
    total_clusters = len(heatmap_engine.clusters)

    last_computed = None
    if _heatmap_cache["timestamp"] > 0:
        last_computed = datetime.utcfromtimestamp(_heatmap_cache["timestamp"]).isoformat() + "Z"

    return HeatmapStatsResponse(
        total_points=total_points,
        total_clusters=total_clusters,
        predicted_hotspots=0,  # filled after compute_heatmap
        last_computed=last_computed,
    )


@router.post("/heatmap-event")
async def add_heatmap_event(
    request: Request,
    event: HeatmapEventInput,
):
    """Manually inject a heatmap event for testing or external integrations.

    Injected events are stored in-memory and included in subsequent heatmap
    computations alongside seed data and blockchain events.
    """
    ts_str = event.timestamp or datetime.utcnow().isoformat()

    event_dict = {
        "lat": event.lat,
        "lng": event.lng,
        "flag_type": event.flag_type,
        "timestamp": ts_str,
        "label": event.label or f"Manual event at ({event.lat:.4f}, {event.lng:.4f})",
        "medicine_id": event.medicine_id,
    }

    _injected_events.append(event_dict)

    # Invalidate cache so the next heatmap request includes this event.
    _heatmap_cache["result"] = None

    logger.info(
        "Heatmap event injected: flag_type=%s at (%.6f, %.6f)",
        event.flag_type,
        event.lat,
        event.lng,
    )

    return {
        "status": "ok",
        "message": "Event injected successfully.",
        "total_injected_events": len(_injected_events),
    }


# --------------------------------------------------------------------------- #
#  Helpers                                                                    #
# --------------------------------------------------------------------------- #

def _build_scan_events(request: Request) -> List[Dict[str, Any]]:
    """Assemble all available scan events from seed data and injected events.

    This merges:
      1. Seed heatmap points already loaded into the engine.
      2. Manually injected events.
      3. Events from the cached heatmap points (if any).
    """
    import json
    from pathlib import Path

    events: List[Dict[str, Any]] = []

    # Include injected events.
    events.extend(_injected_events)

    # Include seed data hotspots as flagged events.
    seed_path = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "indian_pharma_hubs.json"
    if seed_path.exists():
        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_data = json.load(f)

            # Known hotspots become flagged events.
            risk_to_flag = {
                "high": "flagged_high",
                "medium": "flagged_medium",
                "low": "flagged_low",
            }
            for hotspot in seed_data.get("known_hotspots", []):
                risk = hotspot.get("risk_level", "medium").lower()
                events.append({
                    "lat": hotspot["lat"],
                    "lng": hotspot["lng"],
                    "flag_type": risk_to_flag.get(risk, "flagged_medium"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "label": hotspot.get("name", "Unknown"),
                })

            # Manufacturing and distribution hubs as normal scan events.
            for hub in seed_data.get("manufacturing_hubs", []):
                events.append({
                    "lat": hub["lat"],
                    "lng": hub["lng"],
                    "flag_type": "normal",
                    "timestamp": datetime.utcnow().isoformat(),
                    "label": hub.get("name", "Manufacturing Hub"),
                })

            for hub in seed_data.get("distribution_hubs", []):
                events.append({
                    "lat": hub["lat"],
                    "lng": hub["lng"],
                    "flag_type": "normal",
                    "timestamp": datetime.utcnow().isoformat(),
                    "label": hub.get("name", "Distribution Hub"),
                })
        except Exception as exc:
            logger.warning("Could not load seed data for heatmap: %s", exc)

    return events
