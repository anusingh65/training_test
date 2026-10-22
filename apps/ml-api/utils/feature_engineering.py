import numpy as np

FEATURE_COLUMNS = [
    "supply_chain_hops",
    "time_since_manufacture",
    "days_to_expiry",
    "duplicate_scan",
    "hash_matched",
    "scan_velocity",
    "geographic_distance",
]


def extract_features(data: dict) -> np.ndarray:
    """Extract feature vector from a scan data dict."""
    features = []
    for col in FEATURE_COLUMNS:
        val = data.get(col, 0)
        if isinstance(val, bool):
            val = int(val)
        features.append(float(val))
    return np.array([features])


def compute_risk_factors(data: dict, risk_score: float) -> list[str]:
    """Return human-readable contributing risk factors."""
    factors = []
    if data.get("duplicate_scan", 0) == 1:
        factors.append("Duplicate scan detected")
    if data.get("hash_matched", 1) == 0:
        factors.append("Hash mismatch with database")
    if data.get("scan_velocity", 0) > 3:
        factors.append("Abnormally high scan velocity")
    if data.get("geographic_distance", 0) > 500:
        factors.append("Geographic anomaly detected")
    if data.get("days_to_expiry", 999) < 0:
        factors.append("Drug past expiry date")
    if data.get("supply_chain_hops", 0) > 5:
        factors.append("Excessive supply chain hops")
    if data.get("time_since_manufacture", 0) > 365:
        factors.append("Extended time since manufacture")
    if not factors and risk_score > 50:
        factors.append("Statistical anomaly in scan pattern")
    return factors


def risk_level(score: float) -> str:
    if score < 30:
        return "low"
    elif score < 60:
        return "medium"
    elif score < 80:
        return "high"
    return "critical"
