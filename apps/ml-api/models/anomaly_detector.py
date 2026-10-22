"""Isolation Forest anomaly detector."""

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from utils.feature_engineering import FEATURE_COLUMNS


class AnomalyDetector:
    def __init__(self):
        self.model: IsolationForest | None = None

    def train(self, X: np.ndarray, contamination: float = 0.15):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X)

    def predict(self, X: np.ndarray) -> bool:
        """Returns True if anomaly."""
        pred = self.model.predict(X)
        return bool(pred[0] == -1)

    def anomaly_score(self, X: np.ndarray) -> float:
        """Returns anomaly score 0-100 (higher = more anomalous)."""
        raw = self.model.decision_function(X)
        # decision_function: lower = more anomalous, typically in [-0.5, 0.5]
        score = max(0, min(100, (0.5 - raw[0]) * 100))
        return round(float(score), 1)

    def save(self, path: str):
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)
