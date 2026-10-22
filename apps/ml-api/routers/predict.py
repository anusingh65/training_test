from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.feature_engineering import extract_features, compute_risk_factors, risk_level

router = APIRouter()


class ScanInput(BaseModel):
    drug_id: str = ""
    batch_id: str = ""
    supply_chain_hops: int = 3
    time_since_manufacture: int = 30
    days_to_expiry: int = 365
    duplicate_scan: int = 0
    hash_matched: int = 1
    scan_velocity: float = 0.5
    geographic_distance: float = 50.0


class RiskOutput(BaseModel):
    risk_score: float
    is_anomaly: bool
    risk_level: str
    contributing_factors: list[str]


@router.post("/predict/risk", response_model=RiskOutput)
async def predict_risk(scan: ScanInput):
    from main import anomaly_detector, risk_predictor

    if anomaly_detector is None or risk_predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    data = scan.model_dump()
    features = extract_features(data)

    score = risk_predictor.predict_risk_score(features)
    is_anomaly = anomaly_detector.predict(features)
    factors = compute_risk_factors(data, score)
    level = risk_level(score)

    return RiskOutput(
        risk_score=score,
        is_anomaly=is_anomaly,
        risk_level=level,
        contributing_factors=factors,
    )
