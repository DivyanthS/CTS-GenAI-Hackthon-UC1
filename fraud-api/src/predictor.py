"""
src/predictor.py

Loads the versioned XGBoost model and provides a single entry-point for
provider-level fraud probability prediction.

Model versioning
----------------
The active model version is set via the environment variable:

    ACTIVE_MODEL_VERSION=v1   (default)

To upgrade to v2, update the variable and restart the service — no code
changes required.  The prediction endpoint contract remains unchanged.

Directory layout expected:
    models/
        v1/
            model.joblib
            feature_schema.json
            config.json
        v2/
            model.joblib
            ...
"""

import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Resolve model paths from environment
# ------------------------------------------------------------------ #

ACTIVE_VERSION: str = os.getenv("ACTIVE_MODEL_VERSION", "v1")

_BASE_DIR = Path(__file__).resolve().parent.parent
_MODEL_DIR = _BASE_DIR / "models" / ACTIVE_VERSION


def _load_model():
    model_path = _MODEL_DIR / "model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. "
            f"Check ACTIVE_MODEL_VERSION (currently '{ACTIVE_VERSION}')."
        )
    return joblib.load(model_path)


def _load_feature_schema() -> list[str]:
    schema_path = _MODEL_DIR / "feature_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return schema["features"]


def _load_config() -> dict:
    config_path = _MODEL_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load once at module import time (fast subsequent requests)
try:
    MODEL = _load_model()
    FEATURES = _load_feature_schema()
    CONFIG = _load_config()
    THRESHOLD = float(CONFIG["threshold"])
    logger.info(
        "Loaded model version '%s' | threshold=%.2f | features=%d",
        ACTIVE_VERSION,
        THRESHOLD,
        len(FEATURES),
    )
except Exception as exc:
    logger.critical("Failed to load model: %s", exc)
    raise


class PredictionError(RuntimeError):
    """Raised when prediction cannot be completed."""


def predict_single_provider(provider_row: pd.DataFrame) -> float:
    """
    Predict the fraud probability for a single provider.

    Parameters
    ----------
    provider_row : pd.DataFrame
        Single-row DataFrame containing exactly the 30 model features in
        the correct order.  The 'Provider' column must NOT be included.

    Returns
    -------
    float
        Fraud probability ∈ [0, 1].

    Raises
    ------
    PredictionError
        If any required feature is missing or contains NaN.
    """
    # Validate feature set
    missing = [f for f in FEATURES if f not in provider_row.columns]
    if missing:
        raise PredictionError(f"Missing model features: {missing}")

    # Enforce exact training feature order
    X = provider_row[FEATURES].copy()

    if X.isnull().any().any():
        null_cols = X.columns[X.isnull().any()].tolist()
        raise PredictionError(
            f"Model input contains NaN values in features: {null_cols}. "
            "Provider may have insufficient data."
        )

    proba = float(MODEL.predict_proba(X)[0, 1])
    return proba


def predict_batch(provider_df: pd.DataFrame) -> np.ndarray:
    """
    Predict fraud probabilities for multiple providers at once.

    Parameters
    ----------
    provider_df : pd.DataFrame
        DataFrame with one row per provider, containing the 30 model features.
        The 'Provider' column may be present — it will be ignored.

    Returns
    -------
    np.ndarray
        Array of fraud probabilities, one per row.
    """
    X = provider_df[FEATURES].copy()

    if X.isnull().any().any():
        null_summary = X.isnull().sum()
        null_summary = null_summary[null_summary > 0].to_dict()
        raise PredictionError(
            f"Model input contains NaN values: {null_summary}"
        )

    return MODEL.predict_proba(X)[:, 1]


def get_model_info() -> dict:
    """Return metadata about the currently loaded model."""
    return {
        "model_version": ACTIVE_VERSION,
        "model_type": CONFIG.get("model_type", "XGBoost"),
        "threshold": THRESHOLD,
        "n_features": len(FEATURES),
        "features": FEATURES,
        "threshold_selection": CONFIG.get("threshold_selection"),
        "optimization_metric": CONFIG.get("optimization_metric"),
        "performance": CONFIG.get("performance", {}),
    }
