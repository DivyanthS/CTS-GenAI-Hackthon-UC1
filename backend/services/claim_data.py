from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import COMBINED_DATA_FILE


class ClaimDataService:
    """Provides access to the mapped claim-level dataset."""

    def __init__(
        self,
        csv_path: Path | None = None,
    ):
        self.csv_path = csv_path or COMBINED_DATA_FILE
        self.claims: pd.DataFrame | None = None

    def load(self) -> "ClaimDataService":
        """Load the already mapped combined claim dataset."""

        if not self.csv_path.is_file():
            raise FileNotFoundError(
                f"Combined dataset not found: {self.csv_path}"
            )

        self.claims = pd.read_csv(
            self.csv_path,
            low_memory=False,
        )

        required_columns = {
            "ClaimID",
            "Provider",
        }

        missing_columns = sorted(
            required_columns - set(self.claims.columns)
        )

        if missing_columns:
            raise ValueError(
                "Combined dataset is missing required columns: "
                + ", ".join(missing_columns)
            )

        return self

    def _ensure_loaded(self) -> pd.DataFrame:
        """Return the loaded claims dataframe."""

        if self.claims is None:
            self.load()

        if self.claims is None:
            raise RuntimeError(
                "Claim data service failed to load."
            )

        return self.claims

    @staticmethod
    def _safe_record(
        row: pd.Series,
    ) -> dict[str, Any]:
        """
        Convert one pandas row into a JSON-safe dictionary.

        NaN / NaT values are converted to None.
        NumPy scalar values are converted to normal Python values.
        """

        record = (
            row.astype(object)
            .where(pd.notna(row), None)
            .to_dict()
        )

        safe_record: dict[str, Any] = {}

        for key, value in record.items():

            if value is None:
                safe_record[key] = None
                continue

            if hasattr(value, "item"):
                try:
                    value = value.item()
                except (ValueError, TypeError):
                    pass

            safe_record[key] = value

        return safe_record

    @property
    def row_count(self) -> int:
        """Return the number of claims loaded."""

        if self.claims is None:
            return 0

        return len(self.claims)

    @property
    def column_count(self) -> int:
        """Return the number of columns loaded."""

        if self.claims is None:
            return 0

        return len(self.claims.columns)

    def get_claims(
        self,
        page: int = 1,
        page_size: int = 50,
        provider_id: str | None = None,
    ) -> tuple[list[dict], int]:
        """
        Return one paginated page of claim records.

        Optional provider_id filtering is applied before pagination.
        """

        claims = self._ensure_loaded()

        # ---------------------------------------------------------
        # Validate pagination
        # ---------------------------------------------------------

        if page < 1:
            raise ValueError(
                "Page must be greater than or equal to 1."
            )

        if page_size < 1:
            raise ValueError(
                "Page size must be greater than or equal to 1."
            )

        if page_size > 100:
            raise ValueError(
                "Page size cannot exceed 100."
            )

        # ---------------------------------------------------------
        # Normalize provider ID
        # ---------------------------------------------------------

        if provider_id is not None:
            provider_id = provider_id.strip()

            if not provider_id:
                provider_id = None

        # ---------------------------------------------------------
        # Filter before pagination
        # ---------------------------------------------------------

        if provider_id is not None:

            filtered_claims = claims[
                claims["Provider"]
                .astype("string")
                .str.strip()
                == provider_id
            ]

        else:

            filtered_claims = claims

        # ---------------------------------------------------------
        # Total matching claims
        # ---------------------------------------------------------

        total = len(filtered_claims)

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------

        start = (page - 1) * page_size
        end = start + page_size

        page_data = filtered_claims.iloc[start:end]

        # ---------------------------------------------------------
        # JSON-safe conversion
        # ---------------------------------------------------------

        safe_records = [
            self._safe_record(row)
            for _, row in page_data.iterrows()
        ]

        return safe_records, total

    def get_claim(
        self,
        claim_id: str,
    ) -> dict[str, Any]:
        """
        Return one claim by ClaimID.

        Raises
        ------
        KeyError
            If the claim does not exist.
        """

        claims = self._ensure_loaded()

        claim_id = claim_id.strip()

        if not claim_id:
            raise KeyError("Claim ID cannot be empty.")

        matches = claims[
            claims["ClaimID"]
            .astype("string")
            .str.strip()
            == claim_id
        ]

        if matches.empty:
            raise KeyError(
                f"Claim not found: {claim_id}"
            )

        row = matches.iloc[0]

        return self._safe_record(row)

    def claim_exists(
        self,
        claim_id: str,
    ) -> bool:
        """Return whether a claim exists."""

        claims = self._ensure_loaded()

        claim_id = claim_id.strip()

        if not claim_id:
            return False

        return (
            claims["ClaimID"]
            .astype("string")
            .str.strip()
            == claim_id
        ).any()