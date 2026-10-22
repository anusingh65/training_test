"""
Supply Chain Anomaly Detection Module for MediChain.

Ensemble approach combining Isolation Forest (statistical) + Autoencoder (deep learning)
+ rule-based heuristics for high-recall counterfeit pharmaceutical detection.

Flags a transaction as anomalous if EITHER ML model flags it OR 2+ rule-based
violations are triggered. This union strategy maximises recall, which is critical
for pharmaceutical safety -- missing a counterfeit is far worse than a false alarm.
"""

import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path

FEATURE_COLUMNS = [
    'transfer_velocity_kmh',
    'time_since_last_transfer_hours',
    'transfer_count',
    'scan_frequency_24h',
    'unique_devices_24h',
    'path_deviation_score',
    'geographic_consistency',
    'hour_of_day',
    'is_weekend',
    'days_since_manufacture',
    'batch_anomaly_rate',
    'actor_reputation_score',
]


class SupplyChainAutoencoder(nn.Module):
    """
    Shallow autoencoder: 12 -> 8 -> 4 -> 8 -> 12.

    High reconstruction error signals that a transaction does not resemble the
    normal-traffic distribution the model was trained on, i.e. it is anomalous.
    """

    def __init__(self, input_dim: int = 12):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, input_dim),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


class AnomalyDetector:
    """
    Ensemble anomaly detection combining Isolation Forest + Autoencoder.

    Flag as anomaly if EITHER model flags it (high recall for pharma safety).

    Usage::

        detector = AnomalyDetector()
        detector.train(normal_transactions_df)
        result = detector.detect(transaction_dict)

    Result format::

        {
            "is_anomaly": bool,
            "anomaly_score": 0.0-1.0,
            "iforest_score": float,
            "autoencoder_score": float,
            "anomaly_reasons": ["velocity_violation", ...],
            "recommended_severity": "Low" | "Medium" | "High" | "Critical",
        }
    """

    def __init__(self):
        self.iforest = IsolationForest(
            contamination=0.05,
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.autoencoder = SupplyChainAutoencoder(input_dim=len(FEATURE_COLUMNS))
        self.ae_threshold: float | None = None
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.autoencoder.to(self._device)
        self._is_trained = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 256, lr: float = 1e-3) -> None:
        """
        Train both models on *normal* (non-anomalous) transactions.

        Parameters
        ----------
        df : pd.DataFrame
            Training data containing columns listed in ``FEATURE_COLUMNS``.
            Should consist exclusively of normal transactions.
        epochs : int
            Number of autoencoder training epochs.
        batch_size : int
            Mini-batch size for autoencoder training.
        lr : float
            Learning rate for the Adam optimiser.
        """
        features = df[FEATURE_COLUMNS].values.astype(np.float64)

        # 1. Fit scaler and transform
        scaled = self.scaler.fit_transform(features).astype(np.float32)

        # 2. Fit Isolation Forest
        print("[AnomalyDetector] Fitting Isolation Forest ...")
        self.iforest.fit(scaled)
        print("[AnomalyDetector] Isolation Forest fitted.")

        # 3. Train autoencoder
        print(f"[AnomalyDetector] Training Autoencoder for {epochs} epochs (device={self._device}) ...")
        tensor_data = torch.tensor(scaled, dtype=torch.float32)
        dataset = TensorDataset(tensor_data, tensor_data)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        criterion = nn.MSELoss()
        optimiser = torch.optim.Adam(self.autoencoder.parameters(), lr=lr)

        self.autoencoder.train()
        for epoch in range(1, epochs + 1):
            epoch_loss = 0.0
            num_batches = 0
            for batch_x, _ in loader:
                batch_x = batch_x.to(self._device)
                reconstructed = self.autoencoder(batch_x)
                loss = criterion(reconstructed, batch_x)

                optimiser.zero_grad()
                loss.backward()
                optimiser.step()

                epoch_loss += loss.item()
                num_batches += 1

            avg_loss = epoch_loss / max(num_batches, 1)
            if epoch % 10 == 0 or epoch == 1:
                print(f"  Epoch {epoch:3d}/{epochs} -- MSE loss: {avg_loss:.6f}")

        print("[AnomalyDetector] Autoencoder training complete.")

        # 4. Compute ae_threshold (95th percentile reconstruction error on training data)
        self.autoencoder.eval()
        with torch.no_grad():
            all_tensor = torch.tensor(scaled, dtype=torch.float32).to(self._device)
            all_recon = self.autoencoder(all_tensor)
            mse_per_sample = torch.mean((all_tensor - all_recon) ** 2, dim=1).cpu().numpy()

        self.ae_threshold = float(np.percentile(mse_per_sample, 95))
        print(f"[AnomalyDetector] Autoencoder threshold (95th pct): {self.ae_threshold:.6f}")

        self._is_trained = True

    # ------------------------------------------------------------------
    # Single-transaction detection
    # ------------------------------------------------------------------

    def detect(self, transaction: dict) -> dict:
        """
        Score a single transaction and return an anomaly report.

        Parameters
        ----------
        transaction : dict
            Must contain keys matching ``FEATURE_COLUMNS``.

        Returns
        -------
        dict  with keys ``is_anomaly``, ``anomaly_score``, ``iforest_score``,
              ``autoencoder_score``, ``anomaly_reasons``, ``recommended_severity``.
        """
        if not self._is_trained:
            raise RuntimeError("AnomalyDetector has not been trained or loaded yet.")

        # --- Extract & scale features ---
        feature_values = np.array(
            [float(transaction.get(col, 0.0)) for col in FEATURE_COLUMNS],
            dtype=np.float64,
        ).reshape(1, -1)
        scaled = self.scaler.transform(feature_values).astype(np.float32)

        # --- Isolation Forest ---
        iforest_pred = self.iforest.predict(scaled)[0]          # -1 = anomaly, 1 = normal
        iforest_raw = self.iforest.decision_function(scaled)[0]  # lower = more anomalous
        # Normalise to 0-1 where 1 = most anomalous
        iforest_score = float(np.clip(0.5 - iforest_raw, 0.0, 1.0))
        iforest_flagged = iforest_pred == -1

        # --- Autoencoder ---
        self.autoencoder.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(scaled, dtype=torch.float32).to(self._device)
            x_recon = self.autoencoder(x_tensor)
            recon_error = float(torch.mean((x_tensor - x_recon) ** 2).cpu().item())

        # Normalise autoencoder score: ratio of error to threshold, capped at 1
        ae_score = float(np.clip(recon_error / max(self.ae_threshold, 1e-9), 0.0, 1.0))
        ae_flagged = recon_error > self.ae_threshold

        # --- Rule-based checks ---
        reasons: list[str] = []
        tv = float(transaction.get('transfer_velocity_kmh', 0))
        pd_score = float(transaction.get('path_deviation_score', 0))
        tc = float(transaction.get('transfer_count', 0))
        hour = int(transaction.get('hour_of_day', 12))
        weekend = int(transaction.get('is_weekend', 0))
        bar = float(transaction.get('batch_anomaly_rate', 0))
        rep = float(transaction.get('actor_reputation_score', 1000))

        if tv > 500:
            reasons.append('velocity_violation')
        if pd_score > 0:
            reasons.append('path_deviation')
        if tc > 5:
            reasons.append('excessive_transfers')
        if 2 <= hour <= 5 and weekend == 1:
            reasons.append('suspicious_timing')
        if bar > 0.1:
            reasons.append('batch_contamination')
        if rep < 300:
            reasons.append('low_reputation_actor')

        rule_flagged = len(reasons) >= 2

        # --- Combine: anomaly if EITHER ML model flags OR 2+ rule violations ---
        is_anomaly = bool(iforest_flagged or ae_flagged or rule_flagged)

        # Composite anomaly score (weighted average of sub-scores)
        anomaly_score = float(np.clip(
            0.4 * iforest_score + 0.35 * ae_score + 0.25 * (len(reasons) / 6.0),
            0.0,
            1.0,
        ))

        # Bump score if flagged but composite is low (ensure flagged items aren't scored < 0.3)
        if is_anomaly and anomaly_score < 0.3:
            anomaly_score = 0.3

        # --- Map severity ---
        if anomaly_score > 0.8:
            severity = 'Critical'
        elif anomaly_score > 0.6:
            severity = 'High'
        elif anomaly_score > 0.4:
            severity = 'Medium'
        else:
            severity = 'Low'

        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': round(anomaly_score, 4),
            'iforest_score': round(iforest_score, 4),
            'autoencoder_score': round(ae_score, 4),
            'anomaly_reasons': reasons,
            'recommended_severity': severity,
        }

    # ------------------------------------------------------------------
    # Batch detection
    # ------------------------------------------------------------------

    def detect_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply ``detect()`` to every row in *df* and return the dataframe
        augmented with anomaly detection columns.

        Added columns: ``predicted_anomaly``, ``anomaly_score``,
        ``iforest_score``, ``autoencoder_score``, ``anomaly_reasons``,
        ``recommended_severity``.

        The predicted label is stored as ``predicted_anomaly`` to avoid
        colliding with an existing ``is_anomaly`` ground-truth column.
        """
        results = df.apply(lambda row: self.detect(row.to_dict()), axis=1, result_type='expand')
        # Rename the predicted flag to avoid collision with ground-truth column
        results = results.rename(columns={'is_anomaly': 'predicted_anomaly'})
        return pd.concat([df.reset_index(drop=True), results.reset_index(drop=True)], axis=1)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, model_dir: str) -> None:
        """Persist all model artefacts to *model_dir*."""
        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)

        # Isolation Forest
        with open(model_path / 'iforest.pkl', 'wb') as f:
            pickle.dump(self.iforest, f)

        # Scaler
        with open(model_path / 'scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)

        # Autoencoder
        torch.save(self.autoencoder.state_dict(), model_path / 'autoencoder.pth')

        # Threshold
        with open(model_path / 'ae_threshold.pkl', 'wb') as f:
            pickle.dump(self.ae_threshold, f)

        print(f"[AnomalyDetector] Models saved to {model_path}")

    def load(self, model_dir: str) -> None:
        """Load previously saved model artefacts from *model_dir*."""
        model_path = Path(model_dir)

        # Isolation Forest
        with open(model_path / 'iforest.pkl', 'rb') as f:
            self.iforest = pickle.load(f)

        # Scaler
        with open(model_path / 'scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)

        # Autoencoder
        state_dict = torch.load(model_path / 'autoencoder.pth', map_location=self._device, weights_only=True)
        self.autoencoder.load_state_dict(state_dict)
        self.autoencoder.to(self._device)
        self.autoencoder.eval()

        # Threshold
        with open(model_path / 'ae_threshold.pkl', 'rb') as f:
            self.ae_threshold = pickle.load(f)

        self._is_trained = True
        print(f"[AnomalyDetector] Models loaded from {model_path}")
