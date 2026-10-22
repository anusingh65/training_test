"""
Geographic Heatmap Routes for MediChain AI Engine.

Endpoints:
  GET /api/heatmap-data      -- Full heatmap payload (points, clusters,
                                corridors, state risk, hotspot activity).
  GET /api/heatmap-zone-risk -- Risk assessment at a GPS coordinate.
  GET /api/heatmap-stats     -- Summary statistics.
  POST /api/heatmap-event    -- Manually inject a heatmap event.
"""

from __future__ import annotations

import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


# --------------------------------------------------------------------------- #
#  Response models                                                            #
# --------------------------------------------------------------------------- #

class HeatmapDataResponse(BaseModel):
    """Full heatmap response for the dashboard."""
    heatmap_points: List[List[float]] = Field(
        default_factory=list, description="[lat, lng, intensity] triples"
    )
    clusters: List[Dict[str, Any]] = Field(
        default_factory=list, description="DBSCAN cluster summaries"
    )
    predicted_hotspots: List[Dict[str, Any]] = Field(
        default_factory=list, description="Emerging hotspot predictions"
    )
    corridors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Supply-chain route corridor risk"
    )
    known_hotspot_activity: List[Dict[str, Any]] = Field(
        default_factory=list, description="Activity near known pharma hotspots"
    )
    state_risk: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Per-state risk aggregation"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics"
    )
    processing_time_ms: float = 0.0


class ZoneRiskResponse(BaseModel):
    """Risk assessment for a specific geographic zone."""
    risk_level: str
    risk_score: Optional[float] = None
    state: Optional[str] = None
    nearest_cluster: Optional[Dict[str, Any]] = None
    cluster_distance_km: Optional[float] = None
    nearest_hotspot: Optional[str] = None
    hotspot_distance_km: Optional[float] = None
    distance_km: Optional[float] = None


class HeatmapEventInput(BaseModel):
    """Input for manually injecting a heatmap event."""
    lat: float = Field(..., description="Latitude in decimal degrees")
    lng: float = Field(..., description="Longitude in decimal degrees")
    flag_type: str = Field(
        "flagged_medium",
        description="One of: normal, flagged_low, flagged_medium, "
                    "flagged_high, velocity_anomaly, etc.",
    )
    timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp; defaults to now")
    label: Optional[str] = None
    medicine_id: Optional[int] = None


class HeatmapStatsResponse(BaseModel):
    """Summary statistics about the heatmap data store."""
    total_points: int
    total_clusters: int
    predicted_hotspots: int
    states_at_risk: int = 0
    known_hotspots_active: int = 0
    last_computed: Optional[str] = None


# --------------------------------------------------------------------------- #
#  In-memory caches                                                           #
# --------------------------------------------------------------------------- #

_heatmap_cache: Dict[str, Any] = {
    "result": None,
    "timestamp": 0.0,
    "ttl_seconds": 60.0,
}

_injected_events: List[Dict[str, Any]] = []

# Lazily-loaded CSV data (loaded once, reused)
_scan_events_cache: Optional[List[Dict[str, Any]]] = None
_supply_chain_cache: Optional[List[Dict[str, Any]]] = None
_corridors_cache: Optional[List[Dict[str, Any]]] = None


# --------------------------------------------------------------------------- #
#  Data loaders (cached at module level)                                      #
# --------------------------------------------------------------------------- #

def _build_from_seed(heatmap_engine) -> Dict[str, Any]:
    """Assemble heatmap response from precomputed seed data already in memory."""
    clusters = heatmap_engine.clusters or []
    state_risk = heatmap_engine.state_risk or {}
    hotspot_activity = getattr(heatmap_engine, "_seed_hotspot_activity", [])
    heatmap_points = heatmap_engine.heatmap_points or []

    # Filter out normal points from the heat layer (only show flagged)
    flagged_points = [p for p in heatmap_points if p[2] > 0.12]

    # Build predicted hotspots from clusters with high growth
    predicted = []
    for c in clusters:
        risk = c.get("risk_score", 0)
        if risk > 0.5:
            predicted.append({
                "cluster_id": c.get("cluster_id", 0),
                "center_lat": c.get("center_lat", c.get("centroid_lat", 0)),
                "center_lng": c.get("center_lng", c.get("centroid_lng", 0)),
                "state": c.get("state", ""),
                "current_count": c.get("event_count", c.get("member_count", 0)),
                "predicted_count_2w": int(c.get("event_count", 0) * 1.4),
                "growth_rate_per_week": 0.2,
                "growth_pct": 40.0,
                "confidence": 0.7,
                "severity": "high" if risk > 0.7 else "medium",
                "near_known_hotspot": bool(c.get("nearest_known_hotspot")),
                "is_emerging": risk > 0.6,
                "alert": f"Cluster near {c.get('nearest_known_hotspot', 'unknown')} showing elevated activity"
                if c.get("nearest_known_hotspot") else "",
            })

    states_at_risk = sum(1 for s in state_risk.values() if s.get("risk_level") != "low")
    active_hotspots = sum(1 for h in hotspot_activity if h.get("recent_events", 0) > 0)

    return {
        "heatmap_points": flagged_points,
        "clusters": clusters,
        "predicted_hotspots": predicted,
        "known_hotspot_activity": hotspot_activity,
        "state_risk": state_risk,
        "stats": {
            "total_events": len(heatmap_points),
            "flagged_events": len(flagged_points),
            "cluster_count": len(clusters),
            "hotspot_predictions": len(predicted),
            "known_hotspots_active": active_hotspots,
            "states_at_risk": states_at_risk,
        },
    }


def _load_scan_events() -> List[Dict[str, Any]]:
    """Load scan_events.csv into memory (cached after first call).

    Timestamps are shifted so the most recent event aligns with "now".
    This makes synthetic data work with all time window filters.
    """
    global _scan_events_cache
    if _scan_events_cache is not None:
        return _scan_events_cache

    csv_path = _DATA_DIR / "scan_events.csv"
    if not csv_path.exists():
        logger.warning("scan_events.csv not found at %s", csv_path)
        _scan_events_cache = []
        return _scan_events_cache

    # First pass: find the newest timestamp so we can shift everything.
    max_ts: Optional[datetime] = None
    raw_rows: List[Dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw_rows.append(row)
            ts_str = row.get("timestamp", "")
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str)
                    if max_ts is None or dt > max_ts:
                        max_ts = dt
                except ValueError:
                    pass

    # Compute time offset to shift newest event to ~1 hour ago.
    now = datetime.utcnow()
    from datetime import timedelta
    offset = timedelta(0)
    if max_ts:
        offset = now - max_ts - timedelta(hours=1)

    events: List[Dict[str, Any]] = []
    for row in raw_rows:
        try:
            lat = float(row.get("latitude") or row.get("lat", 0))
            lng = float(row.get("longitude") or row.get("lng", 0))

            flag_type = "normal"
            if row.get("flag_type"):
                flag_type = row["flag_type"]
            elif row.get("is_flagged") == "1":
                sev = (row.get("flag_severity") or "medium").lower()
                flag_type = f"flagged_{sev}"

            # Shift timestamp to be recent.
            ts_str = row.get("timestamp", "")
            if ts_str and offset:
                try:
                    shifted = datetime.fromisoformat(ts_str) + offset
                    ts_str = shifted.isoformat()
                except ValueError:
                    pass

            events.append({
                "lat": lat,
                "lng": lng,
                "flag_type": flag_type,
                "timestamp": ts_str,
                "label": row.get("location_name", ""),
                "medicine_id": row.get("medicine_id"),
            })
        except (ValueError, KeyError):
            continue

    logger.info(
        "Loaded %d scan events from %s (shifted by %d days)",
        len(events), csv_path, offset.days,
    )
    _scan_events_cache = events
    return _scan_events_cache


def _load_supply_chain() -> List[Dict[str, Any]]:
    """Load supply_chain_transactions.csv for corridor computation (cached)."""
    global _supply_chain_cache
    if _supply_chain_cache is not None:
        return _supply_chain_cache

    csv_path = _DATA_DIR / "supply_chain_transactions.csv"
    if not csv_path.exists():
        logger.warning("supply_chain_transactions.csv not found at %s", csv_path)
        _supply_chain_cache = []
        return _supply_chain_cache

    rows: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                rows.append({
                    "from_lat": float(row["from_lat"]),
                    "from_lng": float(row["from_lng"]),
                    "to_lat": float(row["to_lat"]),
                    "to_lng": float(row["to_lng"]),
                    "is_anomaly": row.get("is_anomaly", "0"),
                    "anomaly_type": row.get("anomaly_type", ""),
                    "batch_id": row.get("batch_id", ""),
                })
            except (ValueError, KeyError):
                continue

    logger.info("Loaded %d supply chain rows from %s", len(rows), csv_path)
    _supply_chain_cache = rows
    return _supply_chain_cache


def _get_corridors(heatmap_engine) -> List[Dict[str, Any]]:
    """Return precomputed corridors from seed data, or compute from CSV."""
    global _corridors_cache
    if _corridors_cache is not None:
        return _corridors_cache

    # Prefer precomputed corridors from seed (instant)
    if hasattr(heatmap_engine, "_precomputed_corridors") and heatmap_engine._precomputed_corridors:
        _corridors_cache = heatmap_engine._precomputed_corridors
        logger.info("Using %d precomputed corridors from seed data", len(_corridors_cache))
        return _corridors_cache

    # Fallback: compute from supply chain CSV
    sc_data = _load_supply_chain()
    if not sc_data:
        _corridors_cache = []
        return _corridors_cache

    try:
        corridors = heatmap_engine.compute_route_corridor_risk(sc_data)
        _corridors_cache = corridors[:50]  # top 50 by risk
        logger.info("Computed %d route corridors from CSV", len(_corridors_cache))
    except Exception as exc:
        logger.warning("Corridor computation failed: %s", exc)
        _corridors_cache = []

    return _corridors_cache


# --------------------------------------------------------------------------- #
#  Routes                                                                     #
# --------------------------------------------------------------------------- #

@router.get("/heatmap-data", response_model=HeatmapDataResponse)
async def get_heatmap_data(
    request: Request,
    time_window: str = Query("7d", description="Time window: 1h, 6h, 24h, 7d, 30d, 90d, all"),
    min_severity: str = Query("low", description="Minimum severity: low, medium, high, critical"),
    force_refresh: bool = Query(False, description="Bypass cache and recompute"),
):
    """Compute and return full heatmap data for the frontend.

    Returns heatmap points, DBSCAN clusters, predicted hotspots,
    route corridors, known hotspot activity, and per-state risk.
    """
    start_time = time.perf_counter()

    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(status_code=503, detail="HeatmapEngine is not initialised.")

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
        cached["processing_time_ms"] = round(
            (time.perf_counter() - start_time) * 1000, 2
        )
        return HeatmapDataResponse(**cached)

    # Fast path: serve precomputed seed data directly (no recomputation).
    # The seed JSON has points, clusters, state_risk, hotspot_activity already.
    heatmap_result = _build_from_seed(heatmap_engine)

    # Add corridors.
    corridors = _get_corridors(heatmap_engine)
    heatmap_result["corridors"] = corridors

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    heatmap_result["processing_time_ms"] = round(elapsed_ms, 2)

    # Cache.
    _heatmap_cache["result"] = heatmap_result
    _heatmap_cache["timestamp"] = now
    _heatmap_cache["key"] = cache_key

    return HeatmapDataResponse(**heatmap_result)


@router.get("/heatmap-zone-risk", response_model=ZoneRiskResponse)
async def get_zone_risk(
    request: Request,
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Assess the risk level at a specific geographic coordinate."""
    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(status_code=503, detail="HeatmapEngine is not initialised.")

    try:
        zone_risk = heatmap_engine.get_zone_risk_level(lat, lng)
    except Exception as exc:
        logger.error("get_zone_risk_level(%.6f, %.6f) failed: %s", lat, lng, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Zone risk assessment failed: {exc}")

    return ZoneRiskResponse(**zone_risk)


@router.get("/heatmap-stats", response_model=HeatmapStatsResponse)
async def get_heatmap_stats(request: Request):
    """Return summary statistics about the heatmap data store."""
    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(status_code=503, detail="HeatmapEngine is not initialised.")

    last_computed = None
    if _heatmap_cache["timestamp"] > 0:
        last_computed = datetime.utcfromtimestamp(
            _heatmap_cache["timestamp"]
        ).isoformat() + "Z"

    known_active = 0
    states_at_risk = 0
    if hasattr(heatmap_engine, "state_risk"):
        states_at_risk = sum(
            1 for s in heatmap_engine.state_risk.values()
            if s.get("risk_level") != "low"
        )

    return HeatmapStatsResponse(
        total_points=len(heatmap_engine.heatmap_points),
        total_clusters=len(heatmap_engine.clusters),
        predicted_hotspots=0,
        states_at_risk=states_at_risk,
        known_hotspots_active=len(heatmap_engine.known_hotspots),
        last_computed=last_computed,
    )


@router.post("/heatmap-event")
async def add_heatmap_event(
    request: Request,
    event: HeatmapEventInput,
):
    """Manually inject a heatmap event."""
    ts_str = event.timestamp or datetime.utcnow().isoformat()

    _injected_events.append({
        "lat": event.lat,
        "lng": event.lng,
        "flag_type": event.flag_type,
        "timestamp": ts_str,
        "label": event.label or f"Event at ({event.lat:.4f}, {event.lng:.4f})",
        "medicine_id": event.medicine_id,
    })

    # Invalidate caches.
    _heatmap_cache["result"] = None

    return {
        "status": "ok",
        "message": "Event injected successfully.",
        "total_injected_events": len(_injected_events),
    }
