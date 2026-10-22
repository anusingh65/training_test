"""Generate synthetic training data."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.synthetic_data import generate_dataset

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating synthetic data...")
    df = generate_dataset(n_samples=10000, anomaly_ratio=0.15)
    path = os.path.join(OUTPUT_DIR, "synthetic_scans.csv")
    df.to_csv(path, index=False)
    print(f"Generated {len(df)} records -> {path}")
    print(f"  Normal: {(df['is_counterfeit'] == 0).sum()}")
    print(f"  Anomalous: {(df['is_counterfeit'] == 1).sum()}")


if __name__ == "__main__":
    main()
