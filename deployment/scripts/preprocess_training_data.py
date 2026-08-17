import pandas as pd


REQUIRED_COLUMNS = [
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
    "PotentialFraud",
]


def preprocess_training_data(path):
    df = pd.read_csv(path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Keep only the fields required for retraining.
    df = df[REQUIRED_COLUMNS].copy()

    # Remove records without essential identifiers.
    df = df.dropna(
        subset=["Provider", "BeneID", "ClaimID"]
    )

    # Ensure the target is available for supervised retraining.
    df = df.dropna(
        subset=["PotentialFraud"]
    )

    # Keep the original project target representation.
    df["PotentialFraud"] = (
        df["PotentialFraud"]
        .map({"No": 0, "Yes": 1})
    )

    # Remove rows whose target could not be mapped.
    df = df.dropna(
        subset=["PotentialFraud"]
    )

    df["PotentialFraud"] = (
        df["PotentialFraud"].astype(int)
    )

    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python preprocess_training_data.py <input_csv>"
        )
        raise SystemExit(1)

    input_path = sys.argv[1]

    processed = preprocess_training_data(input_path)

    print("Preprocessing completed successfully")
    print("Rows:", len(processed))
    print("Columns:", len(processed.columns))
    print(
        "Fraud labels:",
        processed["PotentialFraud"].value_counts().to_dict()
    )
