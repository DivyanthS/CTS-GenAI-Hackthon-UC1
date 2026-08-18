from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class RiskEngine(ABC):
    """
    Abstract base class for all risk prediction engines.
    Ensures that the ML prediction layer is replaceable without
    rewriting the rest of the backend.
    """

    @property
    @abstractmethod
    def engine_type(self) -> str:
        """Returns 'dummy' or 'real' (e.g. xgboost, external_api)."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Returns the version of the risk engine."""
        pass

    @abstractmethod
    def predict_provider(
        self,
        features: dict[str, Any],
        benchmarks: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Predict risk for a single provider.
        Returns normalized risk dict containing score, probability, level, decision, risk_factors.
        """
        pass

    @abstractmethod
    def predict_batch(
        self,
        provider_features_df: pd.DataFrame,
        dataset_claims_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """
        Predict risk for a batch of providers.
        Returns a DataFrame containing provider_id, risk_score, risk_probability,
        risk_level, decision, risk_factors, model_type, model_version.
        """
        pass
