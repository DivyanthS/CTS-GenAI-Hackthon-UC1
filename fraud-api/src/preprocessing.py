"""
src/preprocessing.py

Validates and cleans a raw claims CSV so it is ready for provider-level
feature engineering.  This module purposely does NOT aggregate — that step
is handled by feature_engineering.py.

Pipeline reproduced from notebook cells 0–22:
  • Load raw CSV
  • Validate required columns are present
  • Drop rows with null identifiers (Provider / BeneID / ClaimID)
  • Ensure ClaimType column contains recognisable values
  • No scaling, no encoding beyond what the notebook applies before aggregation
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Required raw columns for inference
# (same as training except PotentialFraud is NOT required at inference)
# ------------------------------------------------------------------
REQUIRED_COLUMNS: list[str] = [
    "Provider",
    "BeneID",
    "ClaimID",
    "InscClaimAmtReimbursed",
    "DeductibleAmtPaid",
    "AttendingPhysician",
    "OperatingPhysician",
    "OtherPhysician",
    "ClaimType",
    "Age",
    "ChronicConditionCount",
    "NoOfMonths_PartACov",
    "NoOfMonths_PartBCov",
    # 11 chronic condition columns
    "ChronicCond_Alzheimer",
    "ChronicCond_Heartfailure",
    "ChronicCond_KidneyDisease",
    "ChronicCond_Cancer",
    "ChronicCond_ObstrPulmonary",
    "ChronicCond_Depression",
    "ChronicCond_Diabetes",
    "ChronicCond_IschemicHeart",
    "ChronicCond_Osteoporasis",
    "ChronicCond_rheumatoidarthritis",
    "ChronicCond_stroke",
]

CHRONIC_COLUMNS: list[str] = [
    "ChronicCond_Alzheimer",
    "ChronicCond_Heartfailure",
    "ChronicCond_KidneyDisease",
    "ChronicCond_Cancer",
    "ChronicCond_ObstrPulmonary",
    "ChronicCond_Depression",
    "ChronicCond_Diabetes",
    "ChronicCond_IschemicHeart",
    "ChronicCond_Osteoporasis",
    "ChronicCond_rheumatoidarthritis",
    "ChronicCond_stroke",
]

KNOWN_CLAIM_TYPES: set[str] = {"Inpatient", "Outpatient"}


class PreprocessingError(ValueError):
    """Raised when the raw CSV fails validation."""


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean a raw claims DataFrame for inference.

    Parameters
    ----------
    df : pd.DataFrame
        Raw CSV loaded into a DataFrame (before any aggregation).

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame ready for feature_engineering.create_provider_features().

    Raises
    ------
    PreprocessingError
        If any structural validation fails.
    """
    if df.empty:
        raise PreprocessingError("The uploaded CSV is empty.")

    # --- Column validation ---
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise PreprocessingError(
            f"Missing required columns: {missing_cols}"
        )

    # Work on a copy — never mutate the caller's DataFrame
    df = df[REQUIRED_COLUMNS].copy()

    # --- Drop rows missing essential identifiers ---
    before = len(df)
    df = df.dropna(subset=["Provider", "BeneID", "ClaimID"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with null Provider/BeneID/ClaimID.", dropped)

    if df.empty:
        raise PreprocessingError(
            "No valid records remain after removing rows with null identifiers."
        )

    # --- Provider column: ensure string type ---
    df["Provider"] = df["Provider"].astype(str).str.strip()
    if (df["Provider"] == "").any():
        df = df[df["Provider"] != ""]
        if df.empty:
            raise PreprocessingError("No valid Provider identifiers found.")

    # --- ClaimType validation ---
    if "ClaimType" not in df.columns or df["ClaimType"].isna().all():
        raise PreprocessingError(
            "Column 'ClaimType' is entirely missing or null."
        )

    # Drop rows whose ClaimType is not one of the known values
    valid_mask = df["ClaimType"].isin(KNOWN_CLAIM_TYPES)
    invalid_count = (~valid_mask).sum()
    if invalid_count:
        logger.warning(
            "Dropping %d rows with unrecognised ClaimType values.", invalid_count
        )
        df = df[valid_mask]

    if df.empty:
        raise PreprocessingError(
            "No rows remain after filtering to known ClaimType values "
            f"({sorted(KNOWN_CLAIM_TYPES)})."
        )

    # --- Chronic condition re-encoding ---
    # Medicare data may encode chronic conditions as 1=Yes / 2=No.
    # Re-map to binary 0/1 if that pattern is detected.
    for col in CHRONIC_COLUMNS:
        unique_vals = set(df[col].dropna().unique())
        if unique_vals <= {1, 2}:
            df[col] = df[col].map({1: 1, 2: 0})
        # If already 0/1 (or mixed floats), leave as-is

    # --- Numeric coercion for financial columns ---
    for col in ["InscClaimAmtReimbursed", "DeductibleAmtPaid", "Age",
                "ChronicConditionCount", "NoOfMonths_PartACov",
                "NoOfMonths_PartBCov"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info(
        "Preprocessing complete: %d rows across %d providers.",
        len(df),
        df["Provider"].nunique(),
    )
    return df
