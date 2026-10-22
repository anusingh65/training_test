"""
Batch Trace Routes for MediChain AI Engine.

Endpoints:
  GET  /api/batch-trace/batches        -- List batches with anomaly summaries.
  GET  /api/batch-trace/{batch_id}     -- Full backtrace of a single batch.
  POST /api/batch-trace/common-origin  -- Find common origins across batches.
"""

from __future__ import annotations

import csv
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


# --------------------------------------------------------------------------- #
#  Response / request models                                                   #
# --------------------------------------------------------------------------- #

class BatchSummary(BaseModel):
    batch_id: str
    medicine_name: str = ""
    manufacturer: str = ""
    total_transfers: int = 0
    anomaly_count: int = 0


class BatchListResponse(BaseModel):
    flagged_batches: List[BatchSummary] = Field(default_factory=list)
    total_batches: int = 0
    total_flagged: int = 0


class BatchTraceResponse(BaseModel):
    batch_id: str
    origin: Dict[str, Any] = Field(default_factory=dict)
    chain: List[Dict[str, Any]] = Field(default_factory=list)
    total_transfers: int = 0
    anomaly_count: int = 0
    anomaly_rate: float = 0.0
    risk_level: str = "low"
    affected_locations: List[Dict[str, Any]] = Field(default_factory=list)
    actors_involved: List[str] = Field(default_factory=list)
    medicine_name: str = ""
    manufacturer: str = ""
    processing_time_ms: float = 0.0


class CommonOriginRequest(BaseModel):
    batch_ids: List[str] = Field(..., min_length=2, max_length=20)


class CommonOriginResponse(BaseModel):
    batches: List[Dict[str, Any]] = Field(default_factory=list)
    common_origins: List[Dict[str, Any]] = Field(default_factory=list)
    pattern_detected: bool = False
    alert: str = ""
    processing_time_ms: float = 0.0


# --------------------------------------------------------------------------- #
#  In-memory cache                                                             #
# --------------------------------------------------------------------------- #

_supply_chain_full_cache: Optional[List[Dict[str, Any]]] = None
_batch_summary_cache: Optional[BatchListResponse] = None


# --------------------------------------------------------------------------- #
#  Data loader                                                                 #
# --------------------------------------------------------------------------- #

def _load_supply_chain_full() -> List[Dict[str, Any]]:
    """Load supply_chain_transactions.csv with all fields needed for backtrace.

    Maps CSV columns ``from_role`` -> ``from_actor`` and
    ``to_role`` -> ``to_actor`` so data matches what
    ``HeatmapEngine.backtrace_batch()`` expects.
    """
    global _supply_chain_full_cache
    if _supply_chain_full_cache is not None:
        return _supply_chain_full_cache

    csv_path = _DATA_DIR / "supply_chain_transactions.csv"
    if not csv_path.exists():
        logger.warning("supply_chain_transactions.csv not found at %s", csv_path)
        _supply_chain_full_cache = []
        return _supply_chain_full_cache

    rows: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                rows.append({
                    "batch_id": row["batch_id"],
                    "medicine_name": row.get("medicine_name", ""),
                    "manufacturer": row.get("manufacturer", ""),
                    "from_actor": (
                        row.get("manufacturer", "Unknown Manufacturer")
                        if row.get("from_role") == "Manufacturer"
                        else row.get("from_role", "Unknown")
                    ),
                    "to_actor": row.get("to_role", "Unknown"),
                    "from_lat": float(row["from_lat"]),
                    "from_lng": float(row["from_lng"]),
                    "to_lat": float(row["to_lat"]),
                    "to_lng": float(row["to_lng"]),
                    "timestamp": row.get("timestamp", ""),
                    "is_anomaly": row.get("is_anomaly", "0"),
                    "anomaly_type": row.get("anomaly_type", ""),
                    "transfer_velocity_kmh": float(
                        row.get("transfer_velocity_kmh", 0)
                    ),
                })
            except (ValueError, KeyError):
                continue

    logger.info("Loaded %d supply chain rows (full) from %s", len(rows), csv_path)
    _supply_chain_full_cache = rows
    return _supply_chain_full_cache


def _get_batch_summaries() -> BatchListResponse:
    """Build per-batch summary stats (cached)."""
    global _batch_summary_cache
    if _batch_summary_cache is not None:
        return _batch_summary_cache

    events = _load_supply_chain_full()

    groups: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "medicine_name": "",
            "manufacturer": "",
            "total_transfers": 0,
            "anomaly_count": 0,
        }
    )

    for e in events:
        bid = e["batch_id"]
        g = groups[bid]
        g["total_transfers"] += 1
        if str(e.get("is_anomaly", "0")) in ("1", "True", "true"):
            g["anomaly_count"] += 1
        if not g["medicine_name"]:
            g["medicine_name"] = e.get("medicine_name", "")
        if not g["manufacturer"]:
            g["manufacturer"] = e.get("manufacturer", "")

    flagged = []
    for bid, g in groups.items():
        if g["anomaly_count"] > 0:
            flagged.append(BatchSummary(
                batch_id=bid,
                medicine_name=g["medicine_name"],
                manufacturer=g["manufacturer"],
                total_transfers=g["total_transfers"],
                anomaly_count=g["anomaly_count"],
            ))

    flagged.sort(key=lambda b: b.anomaly_count, reverse=True)

    _batch_summary_cache = BatchListResponse(
        flagged_batches=flagged,
        total_batches=len(groups),
        total_flagged=len(flagged),
    )
    return _batch_summary_cache


# --------------------------------------------------------------------------- #
#  Routes                                                                      #
# --------------------------------------------------------------------------- #

@router.get("/batch-trace/batches", response_model=BatchListResponse)
async def list_batches():
    """List all batches with anomaly summaries, flagged batches first."""
    return _get_batch_summaries()


@router.get("/batch-trace/{batch_id}", response_model=BatchTraceResponse)
async def trace_batch(request: Request, batch_id: str):
    """Full backtrace of a single batch through the supply chain."""
    start = time.perf_counter()

    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(503, "HeatmapEngine is not initialised.")

    events = _load_supply_chain_full()
    result = heatmap_engine.backtrace_batch(batch_id, events)

    if "error" in result:
        raise HTTPException(404, result["error"])

    # Enrich with medicine/manufacturer from first matching event.
    batch_events = [e for e in events if e["batch_id"] == batch_id]
    medicine_name = batch_events[0]["medicine_name"] if batch_events else ""
    manufacturer = batch_events[0]["manufacturer"] if batch_events else ""

    origin = result.get("origin", {})

    elapsed = (time.perf_counter() - start) * 1000.0

    return BatchTraceResponse(
        batch_id=result["batch_id"],
        origin=origin,
        chain=result.get("chain", []),
        total_transfers=result.get("total_transfers", 0),
        anomaly_count=result.get("anomaly_count", 0),
        anomaly_rate=result.get("anomaly_rate", 0.0),
        risk_level=result.get("risk_level", "low"),
        affected_locations=result.get("affected_locations", []),
        actors_involved=result.get("actors_involved", []),
        medicine_name=medicine_name,
        manufacturer=manufacturer,
        processing_time_ms=round(elapsed, 2),
    )


@router.post("/batch-trace/common-origin", response_model=CommonOriginResponse)
async def find_common_origin(request: Request, body: CommonOriginRequest):
    """Find common factory origins across multiple flagged batches."""
    start = time.perf_counter()

    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is None:
        raise HTTPException(503, "HeatmapEngine is not initialised.")

    events = _load_supply_chain_full()
    result = heatmap_engine.backtrace_common_origin(body.batch_ids, events)

    # Enrich each trace with manufacturer name.
    batch_manufacturers: Dict[str, str] = {}
    for e in events:
        if e["batch_id"] in body.batch_ids and e.get("manufacturer"):
            batch_manufacturers.setdefault(e["batch_id"], e["manufacturer"])

    for trace in result.get("batches", []):
        bid = trace.get("batch_id", "")
        if bid in batch_manufacturers:
            trace["manufacturer"] = batch_manufacturers[bid]

    elapsed = (time.perf_counter() - start) * 1000.0

    return CommonOriginResponse(
        batches=result.get("batches", []),
        common_origins=result.get("common_origins", []),
        pattern_detected=result.get("pattern_detected", False),
        alert=result.get("alert", ""),
        processing_time_ms=round(elapsed, 2),
    )
