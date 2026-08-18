"""
src/feature_engineering.py

Faithful reproduction of the provider-level aggregation performed in the
Kaggle notebook (cells 23–42).

Pipeline
--------
1.  Claim/financial aggregation      → 11 stats per provider
2.  ClaimsPerBeneficiary             → derived ratio
3.  InpatientShare                   → pd.crosstab(Provider, ClaimType, normalize='index')
                                       OutpatientShare is intentionally DROPPED (notebook cell 36)
4.  Beneficiary features             → de-dup [Provider, BeneID], then group mean
5.  Chronic-condition rates          → de-dup [Provider, BeneID], then group mean (11 cols)
6.  Merge all components on Provider
7.  Missing-value indicators         → flag BEFORE filling with 0
8.  Return Provider + 30 features in exact training order
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Exact feature order that the saved XGBoost model was trained on
FEATURES: list[str] = [
    "TotalClaims",
    "UniqueBeneficiaries",
    "TotalReimbursement",
    "AverageReimbursement",
    "MaxReimbursement",
    "StdReimbursement",
    "TotalDeductiblePaid",
    "AverageDeductiblePaid",
    "UniqueAttendingPhysicians",
    "UniqueOperatingPhysicians",
    "UniqueOtherPhysicians",
    "ClaimsPerBeneficiary",
    "InpatientShare",
    "AveragePatientAge",
    "AverageChronicConditionCount",
    "AveragePartACoverage",
    "AveragePartBCoverage",
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
    "AverageDeductiblePaid_Missing",
    "StdReimbursement_Missing",
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


class FeatureEngineeringError(ValueError):
    """Raised when required features cannot be produced."""


def create_provider_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate a cleaned claims DataFrame to the provider level and return
    exactly the 30 features expected by the trained XGBoost model.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned output of src.preprocessing.preprocess().
        Must contain all REQUIRED_COLUMNS from preprocessing.

    Returns
    -------
    pd.DataFrame
        One row per provider with columns: ['Provider'] + FEATURES (30 cols).

    Raises
    ------
    FeatureEngineeringError
        If any expected feature cannot be calculated.
    """
    # ------------------------------------------------------------------ #
    # Step 1: Claim / financial aggregation  (notebook cell 23)
    # ------------------------------------------------------------------ #
    provider_features = (
        df.groupby("Provider")
        .agg(
            TotalClaims=("ClaimID", "nunique"),
            UniqueBeneficiaries=("BeneID", "nunique"),
            TotalReimbursement=("InscClaimAmtReimbursed", "sum"),
            AverageReimbursement=("InscClaimAmtReimbursed", "mean"),
            MaxReimbursement=("InscClaimAmtReimbursed", "max"),
            StdReimbursement=("InscClaimAmtReimbursed", "std"),
            TotalDeductiblePaid=("DeductibleAmtPaid", "sum"),
            AverageDeductiblePaid=("DeductibleAmtPaid", "mean"),
            UniqueAttendingPhysicians=("AttendingPhysician", "nunique"),
            UniqueOperatingPhysicians=("OperatingPhysician", "nunique"),
            UniqueOtherPhysicians=("OtherPhysician", "nunique"),
        )
        .reset_index()
    )

    # ------------------------------------------------------------------ #
    # Step 2: ClaimsPerBeneficiary  (notebook cell 24)
    # ------------------------------------------------------------------ #
    provider_features["ClaimsPerBeneficiary"] = (
        provider_features["TotalClaims"]
        / provider_features["UniqueBeneficiaries"]
    )

    # ------------------------------------------------------------------ #
    # Step 3: InpatientShare via pd.crosstab  (notebook cells 25–26, 36)
    # OutpatientShare is computed but then DROPPED (cell 36).
    # ------------------------------------------------------------------ #
    claim_type_features = (
        pd.crosstab(
            df["Provider"],
            df["ClaimType"],
            normalize="index",
        )
        .reset_index()
    )

    # Guard: if no Inpatient claims in the upload, add a zero column
    if "Inpatient" not in claim_type_features.columns:
        claim_type_features["Inpatient"] = 0.0

    claim_type_features = (
        claim_type_features[["Provider", "Inpatient"]]
        .rename(columns={"Inpatient": "InpatientShare"})
    )

    # ------------------------------------------------------------------ #
    # Step 4: Beneficiary-level features  (notebook cells 28–29)
    # De-duplicate by [Provider, BeneID] before aggregating
    # ------------------------------------------------------------------ #
    beneficiary_provider = (
        df[
            [
                "Provider",
                "BeneID",
                "Age",
                "ChronicConditionCount",
                "NoOfMonths_PartACov",
                "NoOfMonths_PartBCov",
            ]
        ]
        .drop_duplicates(["Provider", "BeneID"])
    )

    beneficiary_features = (
        beneficiary_provider.groupby("Provider")
        .agg(
            AveragePatientAge=("Age", "mean"),
            AverageChronicConditionCount=("ChronicConditionCount", "mean"),
            AveragePartACoverage=("NoOfMonths_PartACov", "mean"),
            AveragePartBCoverage=("NoOfMonths_PartBCov", "mean"),
        )
        .reset_index()
    )

    # ------------------------------------------------------------------ #
    # Step 5: Chronic-condition rates  (notebook cell 29)
    # De-duplicate by [Provider, BeneID] before averaging
    # ------------------------------------------------------------------ #
    beneficiary_conditions = (
        df[["Provider", "BeneID"] + CHRONIC_COLUMNS]
        .drop_duplicates(["Provider", "BeneID"])
    )

    condition_features = (
        beneficiary_conditions
        .groupby("Provider")[CHRONIC_COLUMNS]
        .mean()
        .reset_index()
    )

    # ------------------------------------------------------------------ #
    # Step 6: Merge all components  (notebook cell 30)
    # ------------------------------------------------------------------ #
    provider_data = (
        provider_features
        .merge(claim_type_features, on="Provider", how="left")
        .merge(beneficiary_features, on="Provider", how="left")
        .merge(condition_features, on="Provider", how="left")
    )

    # ------------------------------------------------------------------ #
    # Step 7: Missing-value indicators BEFORE filling  (cells 41–42)
    # Order is critical: flag first, fill second
    # ------------------------------------------------------------------ #
    provider_data["AverageDeductiblePaid_Missing"] = (
        provider_data["AverageDeductiblePaid"].isna().astype(int)
    )
    provider_data["AverageDeductiblePaid"] = (
        provider_data["AverageDeductiblePaid"].fillna(0)
    )

    provider_data["StdReimbursement_Missing"] = (
        provider_data["StdReimbursement"].isna().astype(int)
    )
    provider_data["StdReimbursement"] = (
        provider_data["StdReimbursement"].fillna(0)
    )

    # ------------------------------------------------------------------ #
    # Step 8: Validate all 30 features exist
    # ------------------------------------------------------------------ #
    missing_features = [f for f in FEATURES if f not in provider_data.columns]
    if missing_features:
        raise FeatureEngineeringError(
            f"Failed to compute expected features: {missing_features}"
        )

    logger.info(
        "Feature engineering complete: %d providers, %d features.",
        len(provider_data),
        len(FEATURES),
    )

    # Return Provider column + exactly the 30 model features in training order
    return provider_data[["Provider"] + FEATURES].reset_index(drop=True)
