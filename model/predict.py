"""Inference logic: load model, compute features, predict."""

import json
import logging
from pathlib import Path

import joblib
import numpy as np

from config import settings
from pipeline.features import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

_model = None
_scaler = None
_meta = None


def load_model() -> bool:
    """Load model artifacts from disk. Returns True if successful."""
    global _model, _scaler, _meta

    model_path = Path(settings.model_path)
    scaler_path = model_path.with_name(model_path.stem + "_scaler.joblib")
    meta_path = model_path.with_name(model_path.stem + "_meta.json")

    if not model_path.exists():
        logger.warning(f"Model not found at {model_path}")
        return False

    _model = joblib.load(model_path)
    _scaler = joblib.load(scaler_path) if scaler_path.exists() else None
    _meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    logger.info("Model loaded successfully")
    return True


def predict(features: dict) -> dict | None:
    """Run prediction on a feature dict.

    Returns:
        {
            "outcome": "gain" | "loss",
            "confidence": float (0-1),
            "predicted_trophy_change": float | None,
            "top_features": list of {"name": str, "value": float, "importance": float}
        }
    """
    if _model is None:
        if not load_model():
            return None

    # Build feature vector in correct order
    feature_vector = np.array([[features.get(col, 0) for col in FEATURE_COLUMNS]])

    # Handle NaN/inf
    feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=0.0, neginf=0.0)

    # Scale if scaler is available
    if _scaler is not None:
        feature_vector = _scaler.transform(feature_vector)

    # Predict class and probability
    proba = _model.predict_proba(feature_vector)[0]
    prediction = int(_model.predict(feature_vector)[0])

    outcome = "gain" if prediction == 1 else "loss"
    confidence = float(proba[prediction])

    # Estimate trophy change from probability and recent performance
    avg_change = float(features.get("avg_trophy_change_10", 0))
    predicted_change = float(abs(avg_change) * (1 if prediction == 1 else -1) * confidence)

    # Top contributing features
    importance = _meta.get("feature_importance", {})
    top_features = []
    for name in sorted(importance, key=importance.get, reverse=True)[:5]:
        top_features.append({
            "name": name,
            "value": float(features.get(name, 0)),
            "importance": float(importance.get(name, 0)),
        })

    return {
        "outcome": outcome,
        "confidence": round(confidence, 4),
        "predicted_trophy_change": round(predicted_change, 1),
        "top_features": top_features,
    }


def get_model_meta() -> dict:
    """Return model metadata (metrics, feature importance, etc.)."""
    if _meta is None:
        if not load_model():
            return {}
    return _meta or {}


def is_model_loaded() -> bool:
    return _model is not None
