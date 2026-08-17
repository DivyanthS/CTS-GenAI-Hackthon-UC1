from __future__ import annotations

from typing import Final

import pandas as pd


CHRONIC_COLUMNS: Final[list[str]] = [
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


MODEL_FEATURES: Final[list[str]] = [
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


def build_provider_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the provider-level feature matrix used by the trained XGBoost model.

    The implementation follows the provider feature-engineering logic
    used in the modeling notebook.

    Parameters
    ----------
    df:
        Combined inpatient + outpatient claim-level dataframe containing
        beneficiary-derived fields and ClaimType.

    Returns
    -------
    pd.DataFrame
        One row per Provider with the exact 30 model features plus Provider.
    """

    required_columns = {
        "Provider",
        "ClaimID",
        "BeneID",
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
        *CHRONIC_COLUMNS,
    }

    missing_columns = sorted(required_columns - set(df.columns))

    if missing_columns:
        raise ValueError(
            "Missing columns required for provider feature engineering: "
            + ", ".join(missing_columns)
        )

    # ---------------------------------------------------------
    # 1. Provider-level claim features
    # ---------------------------------------------------------
    claim_features = (
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

    # Exact notebook formula.
    claim_features["ClaimsPerBeneficiary"] = (
        claim_features["TotalClaims"]
        / claim_features["UniqueBeneficiaries"]
    )

    # ---------------------------------------------------------
    # 2. Claim-type share
    # ---------------------------------------------------------
    claim_type_features = (
        pd.crosstab(
            df["Provider"],
            df["ClaimType"],
            normalize="index",
        )
        .reset_index()
    )

    # Make inference robust when an input dataset contains only
    # one claim type.
    if "Inpatient" not in claim_type_features.columns:
        claim_type_features["Inpatient"] = 0.0

    if "Outpatient" not in claim_type_features.columns:
        claim_type_features["Outpatient"] = 0.0

    claim_type_features["InpatientShare"] = (
        claim_type_features["Inpatient"]
    )

    # OutpatientShare was removed from the final model because:
    # InpatientShare + OutpatientShare = 1.
    #
    # We deliberately do not return OutpatientShare.

    claim_type_features = claim_type_features[
        ["Provider", "InpatientShare"]
    ]

    # ---------------------------------------------------------
    # 3. Beneficiary-level provider features
    # ---------------------------------------------------------
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
            AverageChronicConditionCount=(
                "ChronicConditionCount",
                "mean",
            ),
            AveragePartACoverage=("NoOfMonths_PartACov", "mean"),
            AveragePartBCoverage=("NoOfMonths_PartBCov", "mean"),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # 4. Chronic-condition provider features
    # ---------------------------------------------------------
    beneficiary_conditions = (
        df[["Provider", "BeneID"] + CHRONIC_COLUMNS]
        .drop_duplicates(["Provider", "BeneID"])
    )

    condition_features = (
        beneficiary_conditions.groupby("Provider")[CHRONIC_COLUMNS]
        .mean()
        .reset_index()
    )

    # ---------------------------------------------------------
    # 5. Combine provider feature groups
    # ---------------------------------------------------------
    provider_features = claim_features.merge(
        claim_type_features,
        on="Provider",
        how="left",
    )

    provider_features = provider_features.merge(
        beneficiary_features,
        on="Provider",
        how="left",
    )

    provider_features = provider_features.merge(
        condition_features,
        on="Provider",
        how="left",
    )

    # ---------------------------------------------------------
    # 6. Missing-value indicators
    # ---------------------------------------------------------
    provider_features["AverageDeductiblePaid_Missing"] = (
        provider_features["AverageDeductiblePaid"]
        .isna()
        .astype(int)
    )

    provider_features["AverageDeductiblePaid"] = (
        provider_features["AverageDeductiblePaid"]
        .fillna(0)
    )

    provider_features["StdReimbursement_Missing"] = (
        provider_features["StdReimbursement"]
        .isna()
        .astype(int)
    )

    provider_features["StdReimbursement"] = (
        provider_features["StdReimbursement"]
        .fillna(0)
    )

    # ---------------------------------------------------------
    # 7. Final validation
    # ---------------------------------------------------------
    missing_model_features = [
        feature
        for feature in MODEL_FEATURES
        if feature not in provider_features.columns
    ]

    if missing_model_features:
        raise ValueError(
            "Provider feature engineering did not produce the required "
            "model features: "
            + ", ".join(missing_model_features)
        )

    result = provider_features[
        ["Provider"] + MODEL_FEATURES
    ].copy()

    return result