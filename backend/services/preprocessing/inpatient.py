from __future__ import annotations

from pathlib import Path

import pandas as pd


DATE_COLUMNS = [
    "ClaimStartDt",
    "ClaimEndDt",
    "AdmissionDt",
    "DischargeDt",
]

IDENTIFIER_COLUMNS = [
    "BeneID",
    "ClaimID",
    "Provider",
]

PHYSICIAN_COLUMNS = [
    "AttendingPhysician",
    "OperatingPhysician",
    "OtherPhysician",
]

DIAGNOSIS_COLUMNS = [
    "ClmAdmitDiagnosisCode",
    "DiagnosisGroupCode",
] + [f"ClmDiagnosisCode_{i}" for i in range(1, 11)]

PROCEDURE_COLUMNS = [
    f"ClmProcedureCode_{i}" for i in range(1, 7)
]

# Exact columns removed by the notebook.
PROCEDURE_COLUMNS_TO_REMOVE = [
    "ClmProcedureCode_3",
    "ClmProcedureCode_4",
    "ClmProcedureCode_5",
    "ClmProcedureCode_6",
]

CONSTANT_COLUMNS_TO_REMOVE = [
    "DeductibleAmtPaid",
]


def preprocess_inpatient(
    input_path: str | Path,
) -> pd.DataFrame:
    """
    Preprocess raw inpatient claims using the transformations
    defined in the inpatient preprocessing notebook.

    This function performs preprocessing only.
    No provider-level aggregation or model feature engineering
    is performed here.
    """

    input_path = Path(input_path)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Inpatient dataset not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    # ---------------------------------------------------------
    # 1. Convert date columns
    # ---------------------------------------------------------
    for column in DATE_COLUMNS:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # ---------------------------------------------------------
    # 2. Standardize identifier columns
    # ---------------------------------------------------------
    for column in IDENTIFIER_COLUMNS:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # ---------------------------------------------------------
    # 3. Standardize physician identifiers
    #
    # Missing physician values are intentionally preserved
    # until the UNKNOWN replacement stage below.
    # ---------------------------------------------------------
    for column in PHYSICIAN_COLUMNS:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # ---------------------------------------------------------
    # 4. Standardize diagnosis codes
    # ---------------------------------------------------------
    for column in DIAGNOSIS_COLUMNS:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # ---------------------------------------------------------
    # 5. Standardize procedure codes
    #
    # Example:
    # 7092.0 -> "7092"
    # missing -> <NA>
    # ---------------------------------------------------------
    for column in PROCEDURE_COLUMNS:
        df[column] = (
            df[column]
            .astype("Int64")
            .astype("string")
        )

    # ---------------------------------------------------------
    # 6. Remove procedure columns with >= 90% missingness
    #
    # The notebook explicitly removes:
    # 3, 4, 5
    #
    # ClmProcedureCode_6 was already completely empty.
    # ---------------------------------------------------------
    df.drop(
        columns=[
            column
            for column in PROCEDURE_COLUMNS_TO_REMOVE
            if column in df.columns
        ],
        inplace=True,
    )

    # ---------------------------------------------------------
    # 7. Remove zero-variance deductible column
    # ---------------------------------------------------------
    for column in CONSTANT_COLUMNS_TO_REMOVE:
        if column in df.columns:
            unique_values = df[column].dropna().nunique()
            std_value = df[column].std()

            if unique_values == 1 and std_value == 0:
                df.drop(
                    columns=[column],
                    inplace=True,
                )

    # ---------------------------------------------------------
    # 8. Replace missing diagnosis values with UNKNOWN
    # ---------------------------------------------------------
    for column in DIAGNOSIS_COLUMNS:
        if column in df.columns:
            df[column] = df[column].fillna("UNKNOWN")

    # ---------------------------------------------------------
    # 9. Replace missing physician values with UNKNOWN
    # ---------------------------------------------------------
    for column in PHYSICIAN_COLUMNS:
        if column in df.columns:
            df[column] = df[column].fillna("UNKNOWN")

    # ---------------------------------------------------------
    # 10. Final validation
    # ---------------------------------------------------------
    _validate_inpatient_output(df)

    return df


def _validate_inpatient_output(df: pd.DataFrame) -> None:
    """Validate the final inpatient preprocessing result."""

    expected_removed_columns = (
        PROCEDURE_COLUMNS_TO_REMOVE
        + CONSTANT_COLUMNS_TO_REMOVE
    )

    remaining_removed_columns = [
        column
        for column in expected_removed_columns
        if column in df.columns
    ]

    if remaining_removed_columns:
        raise ValueError(
            "Expected columns were not removed: "
            + ", ".join(remaining_removed_columns)
        )

    # The notebook's final output is 40,474 × 25.
    if len(df) != 40_474:
        raise ValueError(
            f"Unexpected inpatient row count: {len(df)} "
            f"(expected 40,474)"
        )

    if len(df.columns) != 25:
        raise ValueError(
            f"Unexpected inpatient column count: "
            f"{len(df.columns)} (expected 25)"
        )

    # Required identifiers must remain complete.
    for column in IDENTIFIER_COLUMNS:
        if df[column].isna().any():
            raise ValueError(
                f"Missing values remain in identifier column: {column}"
            )

    # Date columns should be datetime.
    for column in DATE_COLUMNS:
        if not pd.api.types.is_datetime64_any_dtype(df[column]):
            raise ValueError(
                f"Date column is not datetime: {column}"
            )

    # No duplicate ClaimIDs according to the notebook validation.
    if df["ClaimID"].duplicated().any():
        raise ValueError("Duplicate ClaimIDs detected.")

    # Diagnosis and physician missing values should have been
    # converted to UNKNOWN.
    for column in DIAGNOSIS_COLUMNS + PHYSICIAN_COLUMNS:
        if column in df.columns and df[column].isna().any():
            raise ValueError(
                f"Missing values remain in standardized column: {column}"
            )