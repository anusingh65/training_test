"""
Train the MediChain supply-chain anomaly detection model.

Usage
-----
From the ``ai-engine/`` directory::

    python -m models.train_anomaly_detector
    python -m models.train_anomaly_detector --data_path data/synthetic/supply_chain_transactions.csv
    python -m models.train_anomaly_detector --model_dir data/models

Steps
-----
1. Load ``supply_chain_transactions.csv`` (from ``data/synthetic/``).
2. Filter to ``is_anomaly == 0`` (train exclusively on normal traffic).
3. Train IsolationForest + Autoencoder via ``AnomalyDetector.train()``.
4. Evaluate on the **full** dataset (including anomalies) -- print
   precision, recall, F1-score, and confusion matrix.
5. Save trained models to ``data/models/``.

If no CSV exists yet the script generates a realistic synthetic dataset
automatically so the pipeline can be demonstrated end-to-end.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ---------------------------------------------------------------------------
# Make sure the project root (ai-engine/) is on sys.path so we can import
# the shared config regardless of how the script is invoked.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MODEL_DIR, SYNTHETIC_DIR  # noqa: E402

from models.anomaly_detector import FEATURE_COLUMNS, AnomalyDetector  # noqa: E402


# ======================================================================
# Synthetic data generation
# ======================================================================

def generate_synthetic_data(n_normal: int = 5000, n_anomaly: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Create a realistic synthetic supply-chain transaction dataset.

    Normal transactions reflect typical Indian pharma supply-chain patterns.
    Anomalies are generated with intentionally suspicious characteristics.

    Returns a DataFrame with all ``FEATURE_COLUMNS`` plus an ``is_anomaly`` label.
    """
    rng = np.random.RandomState(seed)

    # ---- Normal transactions ----
    normal = pd.DataFrame({
        'transfer_velocity_kmh': rng.lognormal(mean=3.5, sigma=0.6, size=n_normal).clip(5, 450),
        'time_since_last_transfer_hours': rng.exponential(scale=24.0, size=n_normal).clip(0.5, 720),
        'transfer_count': rng.poisson(lam=2.0, size=n_normal).clip(1, 5),
        'scan_frequency_24h': rng.poisson(lam=4.0, size=n_normal).clip(1, 20),
        'unique_devices_24h': rng.poisson(lam=2.0, size=n_normal).clip(1, 5),
        'path_deviation_score': rng.exponential(scale=0.02, size=n_normal).clip(0, 0.15),
        'geographic_consistency': rng.beta(a=8, b=2, size=n_normal),
        'hour_of_day': rng.choice(range(6, 22), size=n_normal),
        'is_weekend': rng.choice([0, 1], size=n_normal, p=[0.72, 0.28]),
        'days_since_manufacture': rng.exponential(scale=90, size=n_normal).clip(1, 730).astype(int),
        'batch_anomaly_rate': rng.beta(a=1, b=50, size=n_normal),
        'actor_reputation_score': rng.normal(loc=750, scale=100, size=n_normal).clip(300, 1000),
    })
    normal['is_anomaly'] = 0

    # ---- Anomalous transactions ----
    anomaly = pd.DataFrame({
        'transfer_velocity_kmh': rng.lognormal(mean=6.0, sigma=0.8, size=n_anomaly).clip(200, 2000),
        'time_since_last_transfer_hours': rng.exponential(scale=2.0, size=n_anomaly).clip(0.1, 10),
        'transfer_count': rng.poisson(lam=7.0, size=n_anomaly).clip(4, 20),
        'scan_frequency_24h': rng.poisson(lam=1.0, size=n_anomaly).clip(0, 3),
        'unique_devices_24h': rng.poisson(lam=6.0, size=n_anomaly).clip(3, 15),
        'path_deviation_score': rng.exponential(scale=0.5, size=n_anomaly).clip(0.1, 1.0),
        'geographic_consistency': rng.beta(a=2, b=8, size=n_anomaly),
        'hour_of_day': rng.choice(range(0, 6), size=n_anomaly),
        'is_weekend': rng.choice([0, 1], size=n_anomaly, p=[0.3, 0.7]),
        'days_since_manufacture': rng.exponential(scale=300, size=n_anomaly).clip(180, 1500).astype(int),
        'batch_anomaly_rate': rng.beta(a=3, b=5, size=n_anomaly),
        'actor_reputation_score': rng.normal(loc=250, scale=80, size=n_anomaly).clip(50, 500),
    })
    anomaly['is_anomaly'] = 1

    df = pd.concat([normal, anomaly], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df


# ======================================================================
# Main training pipeline
# ======================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Train MediChain supply-chain anomaly detection model.',
    )
    parser.add_argument(
        '--data_path',
        type=str,
        default=str(SYNTHETIC_DIR / 'supply_chain_transactions.csv'),
        help='Path to the supply-chain transactions CSV. '
             'If missing, a synthetic dataset is generated.',
    )
    parser.add_argument(
        '--model_dir',
        type=str,
        default=str(MODEL_DIR),
        help='Directory where trained model artefacts will be saved.',
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Number of autoencoder training epochs (default: 50).',
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=256,
        help='Mini-batch size for autoencoder training (default: 256).',
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=1e-3,
        help='Adam learning rate for autoencoder (default: 1e-3).',
    )
    args = parser.parse_args()

    data_path = Path(args.data_path)
    model_dir = Path(args.model_dir)

    # ------------------------------------------------------------------
    # 1. Load or generate data
    # ------------------------------------------------------------------
    if data_path.exists():
        print(f"[Pipeline] Loading data from {data_path}")
        df = pd.read_csv(data_path)
    else:
        print(f"[Pipeline] {data_path} not found -- generating synthetic dataset ...")
        df = generate_synthetic_data()
        data_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(data_path, index=False)
        print(f"[Pipeline] Synthetic data saved to {data_path}")

    print(f"[Pipeline] Dataset shape: {df.shape}")
    print(f"[Pipeline] Anomaly distribution:\n{df['is_anomaly'].value_counts().to_string()}")

    # Validate that required feature columns are present
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in dataset: {missing_cols}")

    # ------------------------------------------------------------------
    # 2. Filter to normal transactions for training
    # ------------------------------------------------------------------
    normal_df = df[df['is_anomaly'] == 0].copy()
    print(f"[Pipeline] Training on {len(normal_df)} normal transactions")

    # ------------------------------------------------------------------
    # 3. Train
    # ------------------------------------------------------------------
    detector = AnomalyDetector()
    detector.train(normal_df, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)

    # ------------------------------------------------------------------
    # 4. Evaluate on full dataset
    # ------------------------------------------------------------------
    print("\n[Pipeline] Evaluating on full dataset (normal + anomalous) ...")
    results_df = detector.detect_batch(df)

    # detect_batch stores ground truth in 'is_anomaly' and predictions in 'predicted_anomaly'
    y_true = results_df['is_anomaly'].astype(int).values
    y_pred = results_df['predicted_anomaly'].astype(int).values

    # Metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    print("\n" + "=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Precision : {precision:.4f}")
    print(f"  Recall    : {recall:.4f}")
    print(f"  F1 Score  : {f1:.4f}")
    print()
    print("  Confusion Matrix (rows=true, cols=predicted):")
    cm = confusion_matrix(y_true, y_pred)
    print(f"    TN={cm[0, 0]:5d}   FP={cm[0, 1]:5d}")
    print(f"    FN={cm[1, 0]:5d}   TP={cm[1, 1]:5d}")
    print()
    print("  Classification Report:")
    print(classification_report(y_true, y_pred, target_names=['Normal', 'Anomaly']))
    print("=" * 60)

    # Severity distribution among detected anomalies
    detected = results_df[results_df['predicted_anomaly'].astype(bool)]
    if not detected.empty and 'recommended_severity' in detected.columns:
        print("\n  Severity distribution (detected anomalies):")
        severity_counts = detected['recommended_severity'].value_counts()
        for sev, cnt in severity_counts.items():
            print(f"    {sev:10s}: {cnt}")
        print()

    # ------------------------------------------------------------------
    # 5. Save models
    # ------------------------------------------------------------------
    detector.save(str(model_dir))
    print(f"[Pipeline] Model artefacts saved to {model_dir}")
    print("[Pipeline] Done.")


if __name__ == '__main__':
    main()
