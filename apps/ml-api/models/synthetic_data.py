"""Generate synthetic drug scan data for training."""

import numpy as np
import pandas as pd


def generate_dataset(n_samples: int = 10000, anomaly_ratio: float = 0.15, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_anomalous = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomalous

    # Normal records
    normal = pd.DataFrame({
        "drug_id": [f"DRG-{i:05d}" for i in range(n_normal)],
        "batch_id": [f"BAT-{rng.integers(1, 200):04d}" for _ in range(n_normal)],
        "scan_lat": rng.uniform(8.0, 33.0, n_normal),  # India lat range
        "scan_lon": rng.uniform(68.0, 97.0, n_normal),  # India lon range
        "scanner_role": rng.choice(["consumer", "commuter", "manufacturer"], n_normal, p=[0.7, 0.2, 0.1]),
        "supply_chain_hops": rng.integers(2, 5, n_normal),
        "time_since_manufacture": rng.integers(5, 180, n_normal),
        "days_to_expiry": rng.integers(90, 730, n_normal),
        "duplicate_scan": 0,
        "hash_matched": 1,
        "scan_velocity": rng.uniform(0.0, 2.0, n_normal),
        "geographic_distance": rng.uniform(0, 200, n_normal),
        "is_counterfeit": 0,
    })

    # Anomalous records
    anomalous_records = []
    patterns = ["duplicate", "hash_mismatch", "impossible_travel", "geo_outlier", "high_velocity", "expired"]

    for i in range(n_anomalous):
        pattern = rng.choice(patterns)
        rec = {
            "drug_id": f"DRG-{n_normal + i:05d}",
            "batch_id": f"BAT-{rng.integers(1, 200):04d}",
            "scan_lat": rng.uniform(8.0, 33.0),
            "scan_lon": rng.uniform(68.0, 97.0),
            "scanner_role": rng.choice(["consumer", "commuter", "manufacturer"]),
            "supply_chain_hops": int(rng.integers(2, 5)),
            "time_since_manufacture": int(rng.integers(5, 180)),
            "days_to_expiry": int(rng.integers(90, 730)),
            "duplicate_scan": 0,
            "hash_matched": 1,
            "scan_velocity": float(rng.uniform(0.0, 2.0)),
            "geographic_distance": float(rng.uniform(0, 200)),
            "is_counterfeit": 1,
        }

        if pattern == "duplicate":
            rec["duplicate_scan"] = 1
            rec["geographic_distance"] = float(rng.uniform(300, 1500))
        elif pattern == "hash_mismatch":
            rec["hash_matched"] = 0
        elif pattern == "impossible_travel":
            rec["geographic_distance"] = float(rng.uniform(800, 2000))
            rec["scan_velocity"] = float(rng.uniform(5, 20))
        elif pattern == "geo_outlier":
            rec["geographic_distance"] = float(rng.uniform(500, 1500))
            rec["supply_chain_hops"] = int(rng.integers(6, 12))
        elif pattern == "high_velocity":
            rec["scan_velocity"] = float(rng.uniform(5, 15))
        elif pattern == "expired":
            rec["days_to_expiry"] = int(rng.integers(-180, -1))
            rec["time_since_manufacture"] = int(rng.integers(365, 900))

        anomalous_records.append(rec)

    anomalous = pd.DataFrame(anomalous_records)
    df = pd.concat([normal, anomalous], ignore_index=True)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)
