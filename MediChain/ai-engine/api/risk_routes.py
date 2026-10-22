"""
Composite Risk Scoring Routes for MediChain AI Engine.

Endpoints:
  POST /api/risk-score              -- Compute a full composite risk score for
                                       a medicine using all available AI signals.
  GET  /api/risk-score/{medicine_id} -- Retrieve a cached risk score.
  GET  /api/dashboard-stats         -- Return aggregate dashboard statistics.
  WS   /api/ws/alerts               -- WebSocket endpoint for real-time alert
                                       streaming from the blockchain event
                                       listener.

The RiskScorer fuses three signal sources into a single 0-100 Trust Score:
  1. Supply chain anomaly score          (50%)
  2. External risk factors               (30%) - adverse events, recalls, reputation
  3. Geographic risk / hotspot proximity (20%)

Trust score thresholds:
  80-100 -> "low" risk       (no action)
  50-79  -> "medium" risk    (warning)
  20-49  -> "high" risk      (auto-flag on blockchain)
  0-19   -> "critical" risk  (auto-flag + immediate alert)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Request / response models                                                  #
# --------------------------------------------------------------------------- #

class SignalDetail(BaseModel):
    """Detail of a single risk signal."""
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score for this signal (0=safe, 1=highest risk)")
    status: str = Field(..., description="Status label: pass, normal, warning, elevated, critical")
    source: Optional[str] = None
    available: Optional[bool] = None

    class Config:
        extra = "allow"


class RiskScoreRequest(BaseModel):
    """Request body for computing a composite risk score."""
    medicine_id: int = Field(..., description="On-chain medicine identifier")
    drug_name: Optional[str] = Field(None, description="Drug name for adverse-event lookup")
    location: Optional[Dict[str, float]] = Field(None, description='{"lat": float, "lng": float}')
    transaction_data: Optional[Dict[str, Any]] = Field(None, description="Supply-chain transaction data for anomaly detection")
    actor_reputation: Optional[float] = Field(None, ge=0.0, le=1.0, description="Actor reputation 0-1")
    shortage_flag: bool = Field(False, description="Is the drug on a shortage list?")
    recall_flag: bool = Field(False, description="Is the drug under recall?")
    auto_flag: bool = Field(True, description="Auto-flag on blockchain if trust score < 50?")
    # Note: image is handled via multipart form upload on a separate endpoint.
    # For JSON-only requests, image verification uses a neutral default.


class RiskScoreResponse(BaseModel):
    """Full composite risk score result."""
    medicine_id: int
    trust_score: int = Field(..., ge=0, le=100, description="Composite trust score 0-100")
    risk_level: str = Field(..., description="low, medium, high, or critical")
    flag_severity: int = Field(..., ge=0, le=3, description="On-chain FlagSeverity enum value")
    signals: Dict[str, Any] = Field(default_factory=dict, description="Per-signal breakdown")
    recommendation: str = Field(..., description="Human-readable recommendation")
    auto_flag: bool = Field(..., description="Whether auto-flagging was triggered")
    blockchain_tx: Optional[str] = Field(None, description="Transaction hash if auto-flagged on chain")
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    processing_time_ms: float = 0.0


class DashboardStats(BaseModel):
    """Aggregate statistics for the dashboard overview."""
    total_scans: int = 0
    total_flags: int = 0
    total_verifications: int = 0
    total_anomaly_checks: int = 0
    avg_trust_score: float = 0.0
    active_hotspots: int = 0
    risk_distribution: Dict[str, int] = Field(default_factory=lambda: {
        "low": 0, "medium": 0, "high": 0, "critical": 0,
    })
    cached_scores_count: int = 0
    blockchain_connected: bool = False
    event_listener_running: bool = False
    websocket_clients: int = 0


# --------------------------------------------------------------------------- #
#  Routes                                                                     #
# --------------------------------------------------------------------------- #

@router.post("/risk-score", response_model=RiskScoreResponse)
async def compute_risk_score(
    request: Request,
    body: RiskScoreRequest,
):
    """Compute a full composite risk score for a medicine.

    Fuses all available AI signals (image verification, supply-chain anomaly,
    adverse events, geographic risk, external factors) into a single 0-100
    Trust Score.

    If ``auto_flag`` is true and the trust score falls below 50, the medicine
    is automatically flagged on the blockchain via ``core.flagDrug()``.

    The result is cached in-memory keyed by ``medicine_id`` for subsequent
    retrieval via GET /api/risk-score/{medicine_id}.
    """
    start_time = time.perf_counter()

    risk_scorer = request.app.state.risk_scorer
    if risk_scorer is None:
        raise HTTPException(
            status_code=503,
            detail="RiskScorer is not initialised.",
        )

    # Build kwargs for score_medicine().
    kwargs: Dict[str, Any] = {
        "medicine_id": body.medicine_id,
        "transaction_data": body.transaction_data,
        "drug_name": body.drug_name,
        "location": body.location,
        "actor_reputation": body.actor_reputation,
        "shortage_flag": body.shortage_flag,
        "recall_flag": body.recall_flag,
    }

    try:
        result = await risk_scorer.score_medicine(**kwargs)
    except Exception as exc:
        logger.error(
            "RiskScorer.score_medicine() failed for medicine %d: %s",
            body.medicine_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Risk scoring failed: {exc}",
        )

    # -- Optional auto-flagging on blockchain ------------------------------- #
    blockchain_tx: Optional[str] = None
    if body.auto_flag and result.get("auto_flag", False):
        bridge = request.app.state.bridge
        if bridge is not None and bridge.w3.is_connected():
            flag_args = risk_scorer.get_flag_args(result)
            if flag_args is not None:
                try:
                    tx_hash = bridge.flag_drug(
                        medicine_id=flag_args["medicine_id"],
                        severity=flag_args["severity"],
                    )
                    blockchain_tx = tx_hash
                    request.app.state.stats["total_flags"] += 1
                    logger.info(
                        "Auto-flagged medicine %d with severity %d -> tx %s",
                        flag_args["medicine_id"],
                        flag_args["severity"],
                        tx_hash,
                    )
                except Exception as exc:
                    logger.warning(
                        "Auto-flag on blockchain failed for medicine %d: %s",
                        body.medicine_id,
                        exc,
                    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Cache the result.
    request.app.state.risk_cache[body.medicine_id] = result

    # Update dashboard stats.
    request.app.state.stats["total_scans"] += 1

    # Broadcast the result via WebSocket if it is high/critical.
    risk_level = result.get("risk_level", "low")
    if risk_level in ("high", "critical"):
        ws_manager = request.app.state.ws_manager
        if ws_manager is not None:
            try:
                await ws_manager.broadcast({
                    "type": "RiskAlert",
                    "medicine_id": body.medicine_id,
                    "trust_score": result.get("trust_score"),
                    "risk_level": risk_level,
                    "recommendation": result.get("recommendation", ""),
                    "blockchain_tx": blockchain_tx,
                    "timestamp": result.get("timestamp"),
                })
            except Exception:
                pass  # Non-critical; don't fail the request.

    return RiskScoreResponse(
        medicine_id=result["medicine_id"],
        trust_score=result["trust_score"],
        risk_level=result["risk_level"],
        flag_severity=result["flag_severity"],
        signals=result.get("signals", {}),
        recommendation=result.get("recommendation", ""),
        auto_flag=result.get("auto_flag", False),
        blockchain_tx=blockchain_tx,
        timestamp=result.get("timestamp", ""),
        processing_time_ms=round(elapsed_ms, 2),
    )


@router.get("/risk-score/{medicine_id}", response_model=RiskScoreResponse)
async def get_cached_risk_score(
    request: Request,
    medicine_id: int,
):
    """Retrieve a previously computed risk score from the in-memory cache.

    Returns a 404 if no cached score exists for the given medicine ID.
    Use POST /api/risk-score to compute a new score.
    """
    cache: Dict[int, Dict[str, Any]] = request.app.state.risk_cache
    result = cache.get(medicine_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached risk score found for medicine_id={medicine_id}. "
                   f"Use POST /api/risk-score to compute one.",
        )

    return RiskScoreResponse(
        medicine_id=result["medicine_id"],
        trust_score=result["trust_score"],
        risk_level=result["risk_level"],
        flag_severity=result["flag_severity"],
        signals=result.get("signals", {}),
        recommendation=result.get("recommendation", ""),
        auto_flag=result.get("auto_flag", False),
        blockchain_tx=None,
        timestamp=result.get("timestamp", ""),
        processing_time_ms=0.0,
    )


@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request):
    """Return aggregate statistics for the MediChain dashboard.

    Includes:
      - ``total_scans``: number of risk scoring requests processed
      - ``total_flags``: number of medicines flagged (auto or manual)
      - ``total_verifications``: number of image verification requests
      - ``total_anomaly_checks``: number of anomaly detection requests
      - ``avg_trust_score``: average trust score across cached results
      - ``active_hotspots``: number of high/critical heatmap clusters
      - ``risk_distribution``: counts per risk level across cached scores
      - ``cached_scores_count``: number of medicines with cached scores
      - ``blockchain_connected``: whether the blockchain bridge is live
      - ``event_listener_running``: whether the event listener is active
      - ``websocket_clients``: number of active WebSocket connections
    """
    stats = request.app.state.stats
    cache: Dict[int, Dict[str, Any]] = request.app.state.risk_cache

    # Compute aggregates from the risk cache.
    risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    trust_scores: List[int] = []

    for result in cache.values():
        level = result.get("risk_level", "medium")
        risk_dist[level] = risk_dist.get(level, 0) + 1
        trust_scores.append(result.get("trust_score", 50))

    avg_trust = sum(trust_scores) / max(len(trust_scores), 1) if trust_scores else 0.0

    # Active hotspots from heatmap engine.
    active_hotspots = 0
    heatmap_engine = request.app.state.heatmap_engine
    if heatmap_engine is not None:
        active_hotspots = len([
            c for c in heatmap_engine.clusters
            if c.get("avg_severity", 0) >= 0.5
        ])

    # Blockchain and listener status.
    bridge = request.app.state.bridge
    blockchain_connected = bridge is not None and bridge.w3.is_connected()

    event_listener = request.app.state.event_listener
    listener_running = event_listener is not None and event_listener.running

    ws_manager = request.app.state.ws_manager
    ws_clients = len(ws_manager.active_connections) if ws_manager else 0

    return DashboardStats(
        total_scans=stats.get("total_scans", 0),
        total_flags=stats.get("total_flags", 0),
        total_verifications=stats.get("total_verifications", 0),
        total_anomaly_checks=stats.get("total_anomaly_checks", 0),
        avg_trust_score=round(avg_trust, 2),
        active_hotspots=active_hotspots,
        risk_distribution=risk_dist,
        cached_scores_count=len(cache),
        blockchain_connected=blockchain_connected,
        event_listener_running=listener_running,
        websocket_clients=ws_clients,
    )


# --------------------------------------------------------------------------- #
#  WebSocket endpoint for real-time alerts                                    #
# --------------------------------------------------------------------------- #

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alert streaming.

    Clients connect to receive live blockchain events and risk alerts
    as JSON messages.  Events are broadcast by the BlockchainEventListener
    through the ConnectionManager.

    The connection stays alive with periodic ping/pong.  Send any JSON
    message to the server to keep the connection alive (heartbeat).

    Message types received by clients:
      - DrugScanned, CustodyTransferred, DrugFlagged, VelocityAlert,
        MedicineRegistered (from blockchain event listener)
      - RiskAlert (from risk scoring auto-flag events)
    """
    # Import the manager from the main module.
    ws_manager = websocket.app.state.ws_manager

    await ws_manager.connect(websocket)

    # Send a welcome message.
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to MediChain real-time alert stream.",
            "active_clients": len(ws_manager.active_connections),
        })
    except Exception:
        ws_manager.disconnect(websocket)
        return

    try:
        while True:
            # Wait for client messages (heartbeat / commands).
            # This keeps the connection alive.  The actual alert broadcast
            # is handled by ConnectionManager.broadcast() called from the
            # event listener callback in main.py.
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0,
                )

                # Handle client commands.
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif msg.get("type") == "subscribe":
                        # Future: filter by event type.
                        await websocket.send_json({
                            "type": "subscribed",
                            "message": "Subscription acknowledged.",
                        })
                except (json.JSONDecodeError, TypeError):
                    # Plain text heartbeat -- just acknowledge.
                    await websocket.send_json({"type": "ack"})

            except asyncio.TimeoutError:
                # No message from client in 60s -- send a server-side ping
                # to check if the connection is still alive.
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected gracefully.")
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
    finally:
        ws_manager.disconnect(websocket)
