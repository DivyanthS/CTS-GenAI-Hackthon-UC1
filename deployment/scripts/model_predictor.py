import json
from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"


# Load model
MODEL = joblib.load(MODEL_DIR / "xgboost_fraud_model.pkl")

# Load expected feature list
with open(MODEL_DIR / "features.json", "r", encoding="utf-8") as f:
    FEATURE_CONFIG = json.load(f)

FEATURES = FEATURE_CONFIG["features"]

# Load model configuration
with open(MODEL_DIR / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

THRESHOLD = float(CONFIG["threshold"])


def predict_provider(provider_features):
    """
    Generate a fraud prediction from provider-level features.

    provider_features must contain the exact 30 features
    expected by the trained model.
    """

    missing_features = [
        feature for feature in FEATURES
        if feature not in provider_features.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing expected features: {missing_features}"
        )

    extra_features = [
        column for column in provider_features.columns
        if column not in FEATURES
    ]

    # Keep only the model features and enforce exact training order.
    model_input = provider_features[FEATURES].copy()

    if model_input.isnull().any().any():
        raise ValueError("Model input contains missing values.")

    probability = float(
        MODEL.predict_proba(model_input)[0, 1]
    )

    decision = (
        "FRAUD_FLAG"
        if probability >= THRESHOLD
        else "NOT_FLAGGED"
    )

    return {
        "fraud_probability": round(probability, 6),
        "threshold": THRESHOLD,
        "decision": decision,
        "extra_features_ignored": extra_features,
    }
