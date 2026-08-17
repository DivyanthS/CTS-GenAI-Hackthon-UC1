from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from services.model.loader import ModelLoader


class FraudPredictor:
    """Runs fraud-risk inference using the trained XGBoost model."""

    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Predict fraud risk for one provider.
        """

        expected_features = self.model_loader.features

        missing_features = [
            feature
            for feature in expected_features
            if feature not in features
        ]

        if missing_features:
            raise ValueError(
                "Missing required model features: "
                + ", ".join(missing_features)
            )

        feature_values = [
            features[feature]
            for feature in expected_features
        ]

        try:
            feature_row = pd.DataFrame(
                [feature_values],
                columns=expected_features,
            ).astype(float)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Model features must contain numeric values."
            ) from exc

        if not np.isfinite(
            feature_row.to_numpy(dtype=float)
        ).all():
            raise ValueError(
                "Model features must not contain NaN or infinite values."
            )

        probabilities = self.model_loader.model.predict_proba(
            feature_row
        )

        fraud_probability = float(probabilities[0][1])
        threshold = self.model_loader.threshold

        is_flagged = fraud_probability >= threshold

        return {
            "fraud_probability": fraud_probability,
            "threshold": threshold,
            "decision": (
                "FRAUD_FLAG"
                if is_flagged
                else "NOT_FLAGGED"
            ),
        }

    def predict_batch(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Predict fraud risk for multiple providers.

        The input DataFrame must contain the exact model
        features stored in features.json.
        """

        expected_features = self.model_loader.features

        missing_features = [
            feature
            for feature in expected_features
            if feature not in features.columns
        ]

        if missing_features:
            raise ValueError(
                "Missing required model features: "
                + ", ".join(missing_features)
            )

        # Use the exact feature order stored in features.json.
        feature_matrix = (
            features[expected_features]
            .copy()
            .astype(float)
        )

        if not np.isfinite(
            feature_matrix.to_numpy(dtype=float)
        ).all():
            raise ValueError(
                "Model features must not contain NaN or infinite values."
            )

        probabilities = (
            self.model_loader.model
            .predict_proba(feature_matrix)[:, 1]
        )

        threshold = self.model_loader.threshold

        decisions = [
            "FRAUD_FLAG"
            if probability >= threshold
            else "NOT_FLAGGED"
            for probability in probabilities
        ]

        return pd.DataFrame(
            {
                "fraud_probability": probabilities,
                "threshold": threshold,
                "decision": decisions,
            },
            index=features.index,
        )