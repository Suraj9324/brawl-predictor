"""Training pipeline: load data, engineer features, train, evaluate, save."""

import json
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from config import settings
from db.session import SessionLocal
from pipeline.features import FEATURE_COLUMNS, build_training_dataset

logger = logging.getLogger(__name__)

RANDOM_SEED = 42


def train() -> dict:
    """Full training pipeline. Returns evaluation metrics."""
    logger.info("Building training dataset...")
    db = SessionLocal()
    try:
        df = build_training_dataset(db)
    finally:
        db.close()

    if df.empty or len(df) < 20:
        logger.warning(f"Insufficient data for training: {len(df)} samples")
        return {"error": "Insufficient data", "samples": len(df)}

    logger.info(f"Dataset: {len(df)} samples, {len(FEATURE_COLUMNS)} features")

    X = df[FEATURE_COLUMNS].copy()
    y = df["target_gain"].values

    # Handle any NaN/inf values
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train XGBoost classifier
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        eval_metric="logloss",
    )

    # Cross-validation
    logger.info("Running 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="accuracy")
    cv_f1 = cross_val_score(model, X_scaled, y, cv=5, scoring="f1")
    cv_roc_auc = cross_val_score(model, X_scaled, y, cv=5, scoring="roc_auc")

    logger.info(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    logger.info(f"CV F1: {cv_f1.mean():.4f} (+/- {cv_f1.std():.4f})")
    logger.info(f"CV ROC-AUC: {cv_roc_auc.mean():.4f} (+/- {cv_roc_auc.std():.4f})")

    # Train final model on all data
    model.fit(X_scaled, y)

    # Feature importance
    importance = dict(zip(FEATURE_COLUMNS, model.feature_importances_.tolist()))
    sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    # Save artifacts
    model_path = settings.model_path
    scaler_path = model_path.replace(".joblib", "_scaler.joblib")
    meta_path = model_path.replace(".joblib", "_meta.json")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    metrics = {
        "samples": len(df),
        "features": len(FEATURE_COLUMNS),
        "feature_columns": FEATURE_COLUMNS,
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_accuracy_std": float(cv_scores.std()),
        "cv_f1_mean": float(cv_f1.mean()),
        "cv_f1_std": float(cv_f1.std()),
        "cv_roc_auc_mean": float(cv_roc_auc.mean()),
        "cv_roc_auc_std": float(cv_roc_auc.std()),
        "feature_importance": sorted_importance,
        "class_distribution": {
            "gain": int(y.sum()),
            "loss": int(len(y) - y.sum()),
        },
    }

    with open(meta_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Model saved to {model_path}")
    logger.info(f"Scaler saved to {scaler_path}")
    logger.info(f"Metadata saved to {meta_path}")

    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = train()
    if "error" in result:
        print(f"Training failed: {result['error']}")
    else:
        print(f"Training complete — {result['samples']} samples")
        print(f"Accuracy: {result['cv_accuracy_mean']:.4f}")
        print(f"F1: {result['cv_f1_mean']:.4f}")
        print(f"ROC-AUC: {result['cv_roc_auc_mean']:.4f}")
        print("\nTop 5 features:")
        for name, score in list(result["feature_importance"].items())[:5]:
            print(f"  {name}: {score:.4f}")
