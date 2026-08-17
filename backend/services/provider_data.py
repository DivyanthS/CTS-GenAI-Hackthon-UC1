from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import COMBINED_DATA_FILE
from services.feature_engineering.provider_features import (
    MODEL_FEATURES,
    build_provider_features,
)


class ProviderDataService:
    """Loads and provides access to provider-level model features."""

    def __init__(
        self,
        csv_path: Path | None = None,
    ):
        self.csv_path = csv_path or COMBINED_DATA_FILE
        self.provider_features: pd.DataFrame | None = None

    def load(self) -> "ProviderDataService":
        """Load the combined dataset and build provider features."""

        if not self.csv_path.is_file():
            raise FileNotFoundError(
                f"Combined dataset not found: {self.csv_path}"
            )

        df = pd.read_csv(
            self.csv_path,
            low_memory=False,
        )

        self.provider_features = build_provider_features(df)

        return self

    def get_provider_features(
        self,
        provider_id: str,
    ) -> dict[str, float]:
        """Return model features for one provider."""

        if self.provider_features is None:
            raise RuntimeError(
                "Provider data service has not been loaded."
            )

        matches = self.provider_features[
            self.provider_features["Provider"] == provider_id
        ]

        if matches.empty:
            raise KeyError(
                f"Provider not found: {provider_id}"
            )

        row = matches.iloc[0]

        return {
            feature: float(row[feature])
            for feature in MODEL_FEATURES
        }

    def get_providers(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        """
        Return paginated provider-level feature data.
        """

        if self.provider_features is None:
            raise RuntimeError(
                "Provider data service has not been loaded."
            )

        if page < 1:
            raise ValueError("page must be >= 1")

        if page_size < 1 or page_size > 100:
            raise ValueError(
                "page_size must be between 1 and 100"
            )

        total = len(self.provider_features)

        start = (page - 1) * page_size
        end = start + page_size

        page_data = self.provider_features.iloc[start:end]

        providers = (
            page_data.astype(object)
            .where(pd.notna(page_data), None)
            .to_dict(orient="records")
        )

        return providers, total

    def get_provider(
        self,
        provider_id: str,
    ) -> dict:
        """
        Return model features for one provider.
        """

        if self.provider_features is None:
            raise RuntimeError(
                "Provider data service has not been loaded."
            )

        matches = self.provider_features[
            self.provider_features["Provider"] == provider_id
        ]

        if matches.empty:
            raise KeyError(
                f"Provider not found: {provider_id}"
            )

        row = (
            matches.iloc[0]
            .astype(object)
            .where(pd.notna(matches.iloc[0]), None)
            .to_dict()
        )

        return row
    def provider_exists(
        self,
        provider_id: str,
    ) -> bool:
        """Return whether a provider exists in the loaded dataset."""

        if self.provider_features is None:
            raise RuntimeError(
                "Provider data service has not been loaded."
            )

        return (
            self.provider_features["Provider"] == provider_id
        ).any()

    @property
    def provider_count(self) -> int:
        """Return number of providers loaded."""

        if self.provider_features is None:
            return 0

        return len(self.provider_features)