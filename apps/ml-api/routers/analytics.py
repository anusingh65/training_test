import os
import pandas as pd
from fastapi import APIRouter

router = APIRouter()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_scans.csv")

# City mapping for heatmap
CITY_COORDS = {
    "Mumbai": (19.076, 72.877),
    "Delhi": (28.614, 77.209),
    "Bengaluru": (12.972, 77.595),
    "Chennai": (13.083, 80.271),
    "Hyderabad": (17.385, 78.487),
    "Kolkata": (22.573, 88.364),
    "Pune": (18.520, 73.857),
    "Ahmedabad": (23.023, 72.571),
    "Jaipur": (26.912, 75.787),
    "Lucknow": (26.847, 80.946),
    "Patna": (25.609, 85.138),
    "Surat": (21.170, 72.831),
    "Chandigarh": (30.734, 76.779),
    "Bhopal": (23.260, 77.413),
    "Kochi": (9.932, 76.267),
}


def _assign_city(lat: float, lon: float) -> str:
    """Assign nearest city based on coordinates."""
    import math
    min_dist = float("inf")
    nearest = "Unknown"
    for city, (clat, clon) in CITY_COORDS.items():
        d = math.sqrt((lat - clat) ** 2 + (lon - clon) ** 2)
        if d < min_dist:
            min_dist = d
            nearest = city
    return nearest


@router.get("/heatmap")
async def get_heatmap():
    """Aggregated risk data by city for heatmap display."""
    if not os.path.exists(DATA_PATH):
        return {"regions": []}

    df = pd.read_csv(DATA_PATH)
    df["city"] = df.apply(lambda row: _assign_city(row["scan_lat"], row["scan_lon"]), axis=1)

    result = []
    for city, group in df.groupby("city"):
        coords = CITY_COORDS.get(city, (0, 0))
        total = len(group)
        counterfeit = int(group["is_counterfeit"].sum())
        avg_distance = float(group["geographic_distance"].mean())
        result.append({
            "city": city,
            "latitude": coords[0],
            "longitude": coords[1],
            "total_scans": total,
            "counterfeit_count": counterfeit,
            "risk_ratio": round(counterfeit / total, 3) if total > 0 else 0,
            "avg_geographic_distance": round(avg_distance, 1),
        })

    return {"regions": sorted(result, key=lambda x: x["risk_ratio"], reverse=True)}


@router.get("/analytics/summary")
async def get_summary():
    """Dashboard summary statistics."""
    if not os.path.exists(DATA_PATH):
        return {
            "total_drugs": 0,
            "total_scans": 0,
            "verification_rate": 0,
            "counterfeit_rate": 0,
            "trends": {},
        }

    df = pd.read_csv(DATA_PATH)
    total = len(df)
    counterfeit = int(df["is_counterfeit"].sum())
    verified = total - counterfeit
    hash_match_rate = float(df["hash_matched"].mean())

    return {
        "total_drugs": int(df["drug_id"].nunique()),
        "total_scans": total,
        "verification_rate": round(hash_match_rate * 100, 1),
        "counterfeit_rate": round((counterfeit / total) * 100, 1) if total > 0 else 0,
        "avg_risk_score": round(float(df["geographic_distance"].mean()), 1),
        "trends": {
            "high_risk_batches": int(df[df["is_counterfeit"] == 1]["batch_id"].nunique()),
            "duplicate_scans": int(df["duplicate_scan"].sum()),
            "hash_mismatches": int((df["hash_matched"] == 0).sum()),
        },
    }


@router.get("/drug/{drug_id}/risk-history")
async def get_risk_history(drug_id: str):
    """Risk timeline for a specific drug."""
    if not os.path.exists(DATA_PATH):
        return {"drug_id": drug_id, "history": []}

    df = pd.read_csv(DATA_PATH)
    drug_df = df[df["drug_id"] == drug_id]

    if drug_df.empty:
        return {"drug_id": drug_id, "history": []}

    history = []
    for _, row in drug_df.iterrows():
        history.append({
            "scan_velocity": float(row["scan_velocity"]),
            "geographic_distance": float(row["geographic_distance"]),
            "hash_matched": bool(row["hash_matched"]),
            "supply_chain_hops": int(row["supply_chain_hops"]),
            "is_counterfeit": bool(row["is_counterfeit"]),
        })

    return {"drug_id": drug_id, "history": history}
