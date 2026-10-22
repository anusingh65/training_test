"""XGBoost risk predictor."""

import json
import joblib
import numpy as np
from xgboost import XGBClassifier

from utils.feature_engineering import FEATURE_COLUMNS


class RiskPredictor:
    def __init__(self):
        self.model: XGBClassifier | None = None
        self.feature_importances: dict | None = None

    def train(self, X: np.ndarray, y: np.ndarray):
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
        )
        self.model.fit(X, y)
        self.feature_importances = dict(
            zip(FEATURE_COLUMNS, self.model.feature_importances_.tolist())
        )

    def predict_risk_score(self, X: np.ndarray) -> float:
        """Returns risk score 0-100."""
        proba = self.model.predict_proba(X)[0][1]
        return round(float(proba * 100), 1)

    def predict(self, X: np.ndarray) -> bool:
        """Returns True if predicted counterfeit."""
        return bool(self.model.predict(X)[0] == 1)

    def save(self, model_path: str, meta_path: str):
        joblib.dump(self.model, model_path)
        with open(meta_path, "w") as f:
            json.dump({
                "feature_columns": FEATURE_COLUMNS,
                "feature_importances": self.feature_importances,
            }, f, indent=2)

    def load(self, model_path: str):
        self.model = joblib.load(model_path)
