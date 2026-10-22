import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.anomaly_detector import AnomalyDetector
from models.risk_predictor import RiskPredictor
from routers import predict, analytics

# Global model instances
anomaly_detector: AnomalyDetector | None = None
risk_predictor: RiskPredictor | None = None

MODELS_DIR = os.path.join(os.path.dirname(__file__), "trained_models")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global anomaly_detector, risk_predictor

    iso_path = os.path.join(MODELS_DIR, "isolation_forest.joblib")
    xgb_path = os.path.join(MODELS_DIR, "xgboost_risk.joblib")

    if os.path.exists(iso_path) and os.path.exists(xgb_path):
        anomaly_detector = AnomalyDetector()
        anomaly_detector.load(iso_path)
        risk_predictor = RiskPredictor()
        risk_predictor.load(xgb_path)
        print("Models loaded successfully.")
    else:
        print("WARNING: Models not found. Run scripts/train_models.py first.")

    yield

    anomaly_detector = None
    risk_predictor = None


app = FastAPI(
    title="PharmaChain ML API",
    description="Risk scoring and anomaly detection for pharmaceutical supply chain",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, tags=["Prediction"])
app.include_router(analytics.router, tags=["Analytics"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models_loaded": anomaly_detector is not None and risk_predictor is not None,
    }
