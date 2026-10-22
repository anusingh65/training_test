"""
MediChain AI Engine -- FastAPI Backend

Startup sequence:
  1. Load PillVerifier CNN model (EfficientNet-B0 with custom head).
  2. Instantiate AnomalyDetector (Isolation Forest + Autoencoder ensemble).
     If pre-trained weights exist on disk, load them.
  3. Instantiate AdverseEventMonitor (OpenFDA async client).
  4. Instantiate HeatmapEngine and load seed data (Indian pharma hubs).
  5. Instantiate RiskScorer and wire all models into it.
  6. Attempt to initialise BlockchainBridge; log a warning if the node is
     unreachable (the app can still function in read-only / simulation mode).
  7. Start BlockchainEventListener as a background asyncio task (unless
     the bridge is unavailable and SIMULATION_MODE is off).

Shutdown:
  Stop the event listener gracefully.

CORS:
  Allow localhost:5173 (Vite dev server) and localhost:3000 (alternative).
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Route modules
from api.verify_routes import router as verify_router
from api.anomaly_routes import router as anomaly_router
from api.heatmap_routes import router as heatmap_router
from api.risk_routes import router as risk_router
from api.adverse_event_routes import router as adverse_router

# AI modules
from models.pill_verifier import PillVerifier
from models.anomaly_detector import AnomalyDetector
from models.adverse_event_monitor import AdverseEventMonitor
from models.heatmap_engine import HeatmapEngine
from models.risk_scorer import RiskScorer

# Blockchain modules
from blockchain.bridge import BlockchainBridge
from blockchain.event_listener import BlockchainEventListener, start_event_listener

import config

# --------------------------------------------------------------------------- #
#  Logging                                                                     #
# --------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("medichain")


# --------------------------------------------------------------------------- #
#  WebSocket connection manager                                               #
# --------------------------------------------------------------------------- #

class ConnectionManager:
    """Manages active WebSocket connections for real-time alert broadcasting."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and register it."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket connected. Active connections: %d",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the active set."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "WebSocket disconnected. Active connections: %d",
            len(self.active_connections),
        )

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a JSON message to every connected WebSocket client."""
        disconnected: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Module-level manager instance so the event listener callback can reach it.
ws_manager = ConnectionManager()


# --------------------------------------------------------------------------- #
#  Alert callback for the event listener                                      #
# --------------------------------------------------------------------------- #

async def _alert_callback(event: Dict[str, Any]) -> None:
    """Forward blockchain events to all connected WebSocket clients."""
    await ws_manager.broadcast(event)


# --------------------------------------------------------------------------- #
#  Application lifespan                                                       #
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the FastAPI application."""

    logger.info("=" * 60)
    logger.info("MediChain AI Engine starting up...")
    logger.info("SIMULATION_MODE=%s", config.SIMULATION_MODE)
    logger.info("=" * 60)

    # -- 1. PillVerifier ---------------------------------------------------- #
    logger.info("[1/7] Loading PillVerifier (model_path=%s)...", config.PILL_MODEL_PATH)
    try:
        pill_verifier = PillVerifier(model_path=config.PILL_MODEL_PATH)
        logger.info("[1/7] PillVerifier loaded: %s", pill_verifier)
    except Exception as exc:
        logger.error("[1/7] PillVerifier failed to load: %s", exc)
        pill_verifier = None

    # -- 2. AnomalyDetector ------------------------------------------------- #
    logger.info("[2/7] Initialising AnomalyDetector...")
    anomaly_detector = AnomalyDetector()
    anomaly_model_dir = config.MODEL_DIR / "anomaly"
    if anomaly_model_dir.exists() and (anomaly_model_dir / "iforest.pkl").exists():
        try:
            anomaly_detector.load(str(anomaly_model_dir))
            logger.info("[2/7] AnomalyDetector loaded pre-trained weights from %s", anomaly_model_dir)
        except Exception as exc:
            logger.warning("[2/7] AnomalyDetector could not load weights: %s", exc)
    else:
        logger.info(
            "[2/7] AnomalyDetector initialised (no pre-trained weights at %s; "
            "train via the /api/detect-anomaly endpoint or scripts).",
            anomaly_model_dir,
        )

    # -- 3. AdverseEventMonitor --------------------------------------------- #
    logger.info("[3/7] Initialising AdverseEventMonitor (OpenFDA client)...")
    adverse_monitor = AdverseEventMonitor()
    logger.info("[3/7] AdverseEventMonitor ready.")

    # -- 4. HeatmapEngine --------------------------------------------------- #
    logger.info("[4/7] Initialising HeatmapEngine and loading seed data...")
    heatmap_engine = HeatmapEngine()
    seed_path = config.DATA_DIR / "synthetic" / "indian_pharma_hubs.json"
    if seed_path.exists():
        try:
            heatmap_engine.load_seed_data(str(seed_path))
            logger.info("[4/7] HeatmapEngine seed data loaded from %s", seed_path)
        except Exception as exc:
            logger.warning("[4/7] HeatmapEngine seed data load failed: %s", exc)
    else:
        logger.info("[4/7] HeatmapEngine: no seed data file at %s", seed_path)

    # -- 5. RiskScorer ------------------------------------------------------ #
    logger.info("[5/7] Initialising RiskScorer (wiring all models)...")
    risk_scorer = RiskScorer(
        pill_verifier=pill_verifier,
        anomaly_detector=anomaly_detector,
        adverse_monitor=adverse_monitor,
        heatmap_engine=heatmap_engine,
    )
    logger.info("[5/7] RiskScorer ready: %s", risk_scorer)

    # -- 6. BlockchainBridge ------------------------------------------------ #
    bridge: Optional[BlockchainBridge] = None
    logger.info("[6/7] Initialising BlockchainBridge...")
    try:
        bridge = BlockchainBridge()
        if bridge.w3.is_connected():
            logger.info(
                "[6/7] BlockchainBridge connected (rpc=%s, account=%s).",
                config.LOCAL_RPC_URL,
                bridge.address or "(read-only)",
            )
        else:
            logger.warning(
                "[6/7] BlockchainBridge created but provider is not reachable. "
                "Blockchain features will be unavailable."
            )
    except Exception as exc:
        logger.warning("[6/7] BlockchainBridge init failed: %s. Continuing without blockchain.", exc)
        bridge = None

    # -- 7. Event Listener -------------------------------------------------- #
    event_listener: Optional[BlockchainEventListener] = None
    logger.info("[7/7] Starting BlockchainEventListener...")
    if config.SIMULATION_MODE or (bridge is not None and bridge.w3.is_connected()):
        try:
            event_listener = await start_event_listener(
                bridge=bridge,
                alert_callback=_alert_callback,
            )
            logger.info("[7/7] BlockchainEventListener started (simulation=%s).", config.SIMULATION_MODE)
        except Exception as exc:
            logger.warning("[7/7] BlockchainEventListener failed to start: %s", exc)
    else:
        logger.info(
            "[7/7] Skipping BlockchainEventListener (no blockchain connection "
            "and SIMULATION_MODE is off)."
        )

    # -- Store everything in app.state -------------------------------------- #
    app.state.pill_verifier = pill_verifier
    app.state.anomaly_detector = anomaly_detector
    app.state.adverse_monitor = adverse_monitor
    app.state.heatmap_engine = heatmap_engine
    app.state.risk_scorer = risk_scorer
    app.state.bridge = bridge
    app.state.event_listener = event_listener
    app.state.ws_manager = ws_manager

    # In-memory cache for risk scores keyed by medicine_id.
    app.state.risk_cache: Dict[int, Dict[str, Any]] = {}

    # Dashboard statistics counters.
    app.state.stats = {
        "total_scans": 0,
        "total_flags": 0,
        "total_verifications": 0,
        "total_anomaly_checks": 0,
    }

    logger.info("=" * 60)
    logger.info("MediChain AI Engine startup complete.")
    logger.info("=" * 60)

    # ----- yield: application runs here ----- #
    yield

    # ----- SHUTDOWN ----- #
    logger.info("MediChain AI Engine shutting down...")
    if event_listener is not None:
        try:
            await event_listener.stop()
            logger.info("BlockchainEventListener stopped.")
        except Exception as exc:
            logger.warning("Error stopping event listener: %s", exc)

    logger.info("MediChain AI Engine shutdown complete.")


# --------------------------------------------------------------------------- #
#  Application factory                                                        #
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="MediChain AI Engine",
    description=(
        "AI-powered pharmaceutical supply chain verification engine. "
        "Provides pill image verification, supply chain anomaly detection, "
        "geographic heatmapping, adverse event monitoring, and composite "
        "risk scoring -- all backed by blockchain-anchored provenance."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
#  Register route modules                                                     #
# --------------------------------------------------------------------------- #

app.include_router(verify_router, prefix="/api", tags=["verification"])
app.include_router(anomaly_router, prefix="/api", tags=["anomaly"])
app.include_router(heatmap_router, prefix="/api", tags=["heatmap"])
app.include_router(risk_router, prefix="/api", tags=["risk"])
app.include_router(adverse_router, prefix="/api", tags=["adverse-events"])


# --------------------------------------------------------------------------- #
#  Health check                                                               #
# --------------------------------------------------------------------------- #

@app.get("/api/health", tags=["system"])
async def health():
    """Return service health status and model availability."""
    return {
        "status": "ok",
        "models_loaded": {
            "pill_verifier": app.state.pill_verifier is not None,
            "anomaly_detector": app.state.anomaly_detector is not None,
            "adverse_monitor": app.state.adverse_monitor is not None,
            "heatmap_engine": app.state.heatmap_engine is not None,
            "risk_scorer": app.state.risk_scorer is not None,
        },
        "blockchain_connected": (
            app.state.bridge is not None
            and app.state.bridge.w3.is_connected()
        ),
        "event_listener_running": (
            app.state.event_listener is not None
            and app.state.event_listener.running
        ),
        "simulation_mode": config.SIMULATION_MODE,
        "websocket_clients": len(ws_manager.active_connections),
    }


# --------------------------------------------------------------------------- #
#  Entrypoint                                                                 #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.AI_ENGINE_PORT,
        reload=True,
        log_level="info",
    )
