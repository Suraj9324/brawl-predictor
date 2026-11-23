"""Model evaluation: metrics, confusion matrix, feature importance."""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_predict

from config import settings
from db.session import SessionLocal
from pipeline.features import FEATURE_COLUMNS, build_training_dataset

logger = logging.getLogger(__name__)


def evaluate() -> dict:
    """Evaluate the trained model. Returns detailed metrics."""
    model_path = Path(settings.model_path)
    scaler_path = model_path.with_name(model_path.stem + "_scaler.joblib")

    if not model_path.exists():
        return {"error": "No trained model found. Run `python -m model.train` first."}

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None

    db = SessionLocal()
    try:
        df = build_training_dataset(db)
    finally:
        db.close()

    if df.empty:
        return {"error": "No data available for evaluation"}

    X = df[FEATURE_COLUMNS].copy()
    y = df["target_gain"].values
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X.values

    # Cross-validated predictions for unbiased evaluation
    y_pred = cross_val_predict(model, X_scaled, y, cv=5)
    y_proba = cross_val_predict(model, X_scaled, y, cv=5, method="predict_proba")[:, 1]

    cm = confusion_matrix(y, y_pred)
    report = classification_report(y, y_pred, target_names=["Loss", "Gain"], output_dict=True)

    metrics = {
        "samples": len(df),
        "accuracy": float(accuracy_score(y, y_pred)),
        "precision": float(precision_score(y, y_pred)),
        "recall": float(recall_score(y, y_pred)),
        "f1": float(f1_score(y, y_pred)),
        "roc_auc": float(roc_auc_score(y, y_proba)),
        "confusion_matrix": {
            "true_negative": int(cm[0][0]),
            "false_positive": int(cm[0][1]),
            "false_negative": int(cm[1][0]),
            "true_positive": int(cm[1][1]),
        },
        "classification_report": report,
        "feature_importance": dict(
            zip(FEATURE_COLUMNS, model.feature_importances_.tolist())
        ),
    }

    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = evaluate()

    if "error" in result:
        print(result["error"])
    else:
        print(f"\nEvaluation on {result['samples']} samples")
        print(f"{'='*40}")
        print(f"Accuracy:  {result['accuracy']:.4f}")
        print(f"Precision: {result['precision']:.4f}")
        print(f"Recall:    {result['recall']:.4f}")
        print(f"F1 Score:  {result['f1']:.4f}")
        print(f"ROC-AUC:   {result['roc_auc']:.4f}")

        cm = result["confusion_matrix"]
        print(f"\nConfusion Matrix:")
        print(f"  TN={cm['true_negative']}  FP={cm['false_positive']}")
        print(f"  FN={cm['false_negative']}  TP={cm['true_positive']}")

        print(f"\nTop 10 Features:")
        sorted_fi = sorted(result["feature_importance"].items(), key=lambda x: x[1], reverse=True)
        for name, score in sorted_fi[:10]:
            bar = "#" * int(score * 100)
            print(f"  {name:35s} {score:.4f} {bar}")
