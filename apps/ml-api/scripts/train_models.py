"""Train Isolation Forest and XGBoost models."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from models.anomaly_detector import AnomalyDetector
from models.risk_predictor import RiskPredictor
from utils.feature_engineering import FEATURE_COLUMNS

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_scans.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "trained_models")


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS].values
    y = df["is_counterfeit"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Isolation Forest
    print("\nTraining Isolation Forest...")
    anomaly = AnomalyDetector()
    anomaly.train(X_train)
    anomaly.save(os.path.join(MODELS_DIR, "isolation_forest.joblib"))
    print("Isolation Forest saved.")

    # XGBoost
    print("\nTraining XGBoost classifier...")
    risk = RiskPredictor()
    risk.train(X_train, y_train)
    risk.save(
        os.path.join(MODELS_DIR, "xgboost_risk.joblib"),
        os.path.join(MODELS_DIR, "xgboost_meta.json"),
    )

    # Evaluate
    y_pred = [1 if risk.predict_risk_score(X_test[i:i+1]) > 50 else 0 for i in range(len(X_test))]
    print("\nXGBoost Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Counterfeit"]))

    print("\nFeature Importances:")
    for feat, imp in sorted(risk.feature_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {imp:.4f}")

    print("\nModels saved to", MODELS_DIR)


if __name__ == "__main__":
    main()
