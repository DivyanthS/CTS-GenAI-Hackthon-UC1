import pandas as pd


FEATURES = [
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


CHRONIC_COLUMNS = [
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


def create_provider_features(df):
    # Provider-level claim and financial features
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

    provider_features["ClaimsPerBeneficiary"] = (
        provider_features["TotalClaims"]
        / provider_features["UniqueBeneficiaries"]
    )

    # Claim type share
    claim_type_features = (
        pd.crosstab(
            df["Provider"],
            df["ClaimType"],
            normalize="index",
        )
        .reset_index()
    )

    if "Inpatient" not in claim_type_features.columns:
        claim_type_features["Inpatient"] = 0

    claim_type_features = claim_type_features[
        ["Provider", "Inpatient"]
    ].rename(
        columns={"Inpatient": "InpatientShare"}
    )

    # Patient-level features
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
            AveragePartACoverage=(
                "NoOfMonths_PartACov",
                "mean",
            ),
            AveragePartBCoverage=(
                "NoOfMonths_PartBCov",
                "mean",
            ),
        )
        .reset_index()
    )

    # Chronic-condition features
    beneficiary_conditions = (
        df[
            ["Provider", "BeneID"] + CHRONIC_COLUMNS
        ]
        .drop_duplicates(["Provider", "BeneID"])
    )

    condition_features = (
        beneficiary_conditions
        .groupby("Provider")[CHRONIC_COLUMNS]
        .mean()
        .reset_index()
    )

    # Merge all provider-level features
    provider_data = (
        provider_features
        .merge(
            claim_type_features,
            on="Provider",
            how="left",
        )
        .merge(
            beneficiary_features,
            on="Provider",
            how="left",
        )
        .merge(
            condition_features,
            on="Provider",
            how="left",
        )
    )

    # Preserve missing-value information
    provider_data["AverageDeductiblePaid_Missing"] = (
        provider_data["AverageDeductiblePaid"]
        .isna()
        .astype(int)
    )

    provider_data["AverageDeductiblePaid"] = (
        provider_data["AverageDeductiblePaid"]
        .fillna(0)
    )

    provider_data["StdReimbursement_Missing"] = (
        provider_data["StdReimbursement"]
        .isna()
        .astype(int)
    )

    provider_data["StdReimbursement"] = (
        provider_data["StdReimbursement"]
        .fillna(0)
    )

    # Ensure every expected feature exists
    missing_features = [
        feature
        for feature in FEATURES
        if feature not in provider_data.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing engineered features: {missing_features}"
        )

    # Return exactly the 30 features in model order
    return provider_data[
        ["Provider"] + FEATURES
    ]


if __name__ == "__main__":
    import sys
    from preprocess_training_data import (
        preprocess_training_data,
    )

    if len(sys.argv) != 2:
        print(
            "Usage: python feature_engineering.py <input_csv>"
        )
        raise SystemExit(1)

    input_path = sys.argv[1]

    processed = preprocess_training_data(
        input_path
    )

    provider_features = create_provider_features(
        processed
    )

    print(
        "Feature engineering completed successfully"
    )
    print(
        "Providers:",
        len(provider_features)
    )
    print(
        "Feature count:",
        len(FEATURES)
    )
    print(
        "Feature order:",
        list(provider_features.columns[1:])
    )
