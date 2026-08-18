from __future__ import annotations

from typing import Any
from utils.risk_utils import generate_provider_name


def normalize_prediction_output(
    raw_prediction: dict[str, Any],
    provider_name: str | None = None,
) -> dict[str, Any]:
    """
    Standardize any model output (dummy, XGBoost, REST API, etc.) into the canonical JSON schema.
    """
    provider_id = str(raw_prediction.get("provider_id") or raw_prediction.get("Provider") or "").strip()
    score = float(raw_prediction.get("risk_score") or (raw_prediction.get("fraud_probability", 0.0) * 100.0))
    score = round(max(0.0, min(100.0, score)), 2)
    probability = float(raw_prediction.get("risk_probability") or (score / 100.0))
    probability = round(max(0.0, min(1.0, probability)), 4)

    level = raw_prediction.get("risk_level")
    decision = raw_prediction.get("decision")

    if not level or not decision:
        from services.risk.risk_classifier import classify_risk_score
        computed_level, computed_decision, _ = classify_risk_score(score)
        level = level or computed_level
        decision = decision or computed_decision

    model_type = str(raw_prediction.get("model_type") or "dummy")
    model_version = str(raw_prediction.get("model_version") or "1.0")
    factors = raw_prediction.get("risk_factors") or []

    name = provider_name or generate_provider_name(provider_id)

    return {
        "provider_id": provider_id,
        "provider_name": name,
        "risk_score": score,
        "risk_probability": probability,
        "risk_level": level,
        "decision": decision,
        "model_type": model_type,
        "model_version": model_version,
        "risk": {
            "score": score,
            "probability": probability,
            "level": level,
            "decision": decision,
        },
        "model": {
            "type": model_type,
            "version": model_version,
        },
        "risk_factors": factors,
        # Legacy frontend fields
        "fraud_probability": probability,
        "threshold": float(raw_prediction.get("threshold") or 0.5),
    }
