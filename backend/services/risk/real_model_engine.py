from __future__ import annotations

from typing import Any
import pandas as pd

from services.risk.base import RiskEngine
from services.risk.risk_classifier import classify_risk_score
from services.feature_engineering.provider_features import MODEL_FEATURES


class RealModelRiskEngine(RiskEngine):
    """
    Adapter for real ML model (XGBoost / external predictor).
    Implements the standard RiskEngine interface.
    """

    def __init__(self, loader=None):
        self._loader = loader
        self._version = "2.0"

    @property
    def engine_type(self) -> str:
        return "xgboost"

    @property
    def version(self) -> str:
        return self._version

    def _ensure_model(self):
        if self._loader is None:
            from services.model.loader import ModelLoader
            self._loader = ModelLoader().load()
        return self._loader

    def predict_provider(
        self,
        features: dict[str, Any],
        benchmarks: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader = self._ensure_model()
        from services.model.predictor import FraudPredictor
        predictor = FraudPredictor(loader)

        pred = predictor.predict(features)
        prob = float(pred["fraud_probability"])
        score = round(prob * 100.0, 2)
        level, decision, _ = classify_risk_score(score)
        pid = str(features.get("Provider", "UNKNOWN"))

        return {
            "provider_id": pid,
            "risk_score": score,
            "risk_probability": round(prob, 4),
            "risk_level": level,
            "decision": decision,
            "model_type": self.engine_type,
            "model_version": self.version,
            "risk_factors": [],
            "fraud_probability": round(prob, 4),
            "threshold": float(loader.threshold),
        }

    def predict_batch(
        self,
        provider_features_df: pd.DataFrame,
        dataset_claims_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        loader = self._ensure_model()
        from services.model.predictor import FraudPredictor
        predictor = FraudPredictor(loader)

        features_matrix = provider_features_df[MODEL_FEATURES].copy()
        pred_df = predictor.predict_batch(features_matrix)

        scores = (pred_df["fraud_probability"] * 100.0).round(2)
        levels = []
        decisions = []
        for s in scores:
            l, d, _ = classify_risk_score(s)
            levels.append(l)
            decisions.append(d)

        results_df = pd.DataFrame(
            {
                "Provider": provider_features_df["Provider"],
                "risk_score": scores,
                "risk_probability": pred_df["fraud_probability"].round(4),
                "risk_level": levels,
                "decision": decisions,
                "risk_factors": [[] for _ in range(len(provider_features_df))],
                "model_type": self.engine_type,
                "model_version": self.version,
                "fraud_probability": pred_df["fraud_probability"].round(4),
                "threshold": float(loader.threshold),
            },
            index=provider_features_df.index,
        )

        return results_df
