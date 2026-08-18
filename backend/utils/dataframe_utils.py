from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

COLUMN_ALIASES = {
    "provider": "Provider",
    "provider_id": "Provider",
    "providerid": "Provider",
    "claimid": "ClaimID",
    "claim_id": "ClaimID",
    "beneid": "BeneID",
    "bene_id": "BeneID",
    "beneficiary_id": "BeneID",
    "inscclaimamtreimbursed": "InscClaimAmtReimbursed",
    "reimbursement": "InscClaimAmtReimbursed",
    "reimbursement_amount": "InscClaimAmtReimbursed",
    "claim_amount": "InscClaimAmtReimbursed",
    "deductibleamtpaid": "DeductibleAmtPaid",
    "deductible": "DeductibleAmtPaid",
    "deductible_amount": "DeductibleAmtPaid",
    "claimtype": "ClaimType",
    "claim_type": "ClaimType",
    "claimstartdt": "ClaimStartDt",
    "claim_start_date": "ClaimStartDt",
    "claim_start_dt": "ClaimStartDt",
    "claimenddt": "ClaimEndDt",
    "claim_end_date": "ClaimEndDt",
    "claim_end_dt": "ClaimEndDt",
    "attendingphysician": "AttendingPhysician",
    "attending_physician": "AttendingPhysician",
    "operatingphysician": "OperatingPhysician",
    "operating_physician": "OperatingPhysician",
    "otherphysician": "OtherPhysician",
    "other_physician": "OtherPhysician",
    "potentialfraud": "PotentialFraud",
    "potential_fraud": "PotentialFraud",
    "age": "Age",
    "chronicconditioncount": "ChronicConditionCount",
    "chronic_condition_count": "ChronicConditionCount",
    "noofmonths_partacov": "NoOfMonths_PartACov",
    "no_of_months_part_a_cov": "NoOfMonths_PartACov",
    "part_a_coverage": "NoOfMonths_PartACov",
    "noofmonths_partbcov": "NoOfMonths_PartBCov",
    "no_of_months_part_b_cov": "NoOfMonths_PartBCov",
    "part_b_coverage": "NoOfMonths_PartBCov",
}

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


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame column names to match canonical naming.
    """
    normalized_cols = {}
    for col in df.columns:
        clean = str(col).strip()
        lower = clean.lower()
        if lower in COLUMN_ALIASES:
            normalized_cols[col] = COLUMN_ALIASES[lower]
        else:
            # Check for chronic condition prefix variants
            matched_chronic = False
            for cc in CHRONIC_COLUMNS:
                if lower == cc.lower():
                    normalized_cols[col] = cc
                    matched_chronic = True
                    break
            if not matched_chronic:
                normalized_cols[col] = clean

    df = df.rename(columns=normalized_cols)
    return df


def ensure_required_dataset_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the DataFrame has defaults for optional columns to avoid pipeline crashes.
    """
    df = df.copy()

    # Provider and ClaimID are mandatory
    if "Provider" not in df.columns:
        raise ValueError("Dataset is missing mandatory 'Provider' column.")
    if "ClaimID" not in df.columns:
        raise ValueError("Dataset is missing mandatory 'ClaimID' column.")

    # Defaults for optional columns
    if "BeneID" not in df.columns:
        df["BeneID"] = "BENE_" + df.index.astype(str)

    if "InscClaimAmtReimbursed" not in df.columns:
        df["InscClaimAmtReimbursed"] = 0.0
    else:
        df["InscClaimAmtReimbursed"] = pd.to_numeric(df["InscClaimAmtReimbursed"], errors="coerce").fillna(0.0)

    if "DeductibleAmtPaid" not in df.columns:
        df["DeductibleAmtPaid"] = 0.0
    else:
        df["DeductibleAmtPaid"] = pd.to_numeric(df["DeductibleAmtPaid"], errors="coerce").fillna(0.0)

    if "ClaimType" not in df.columns:
        df["ClaimType"] = "Outpatient"
    else:
        # Standardize ClaimType strings
        df["ClaimType"] = df["ClaimType"].astype(str).str.strip().str.capitalize()
        df["ClaimType"] = df["ClaimType"].replace({"1": "Inpatient", "2": "Outpatient"})
        df.loc[~df["ClaimType"].isin(["Inpatient", "Outpatient"]), "ClaimType"] = "Outpatient"

    if "AttendingPhysician" not in df.columns:
        df["AttendingPhysician"] = None
    if "OperatingPhysician" not in df.columns:
        df["OperatingPhysician"] = None
    if "OtherPhysician" not in df.columns:
        df["OtherPhysician"] = None

    if "Age" not in df.columns:
        df["Age"] = 70.0
    else:
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(70.0)

    if "ChronicConditionCount" not in df.columns:
        # If individual chronic columns exist, sum them, else default to 2.0
        cc_present = [col for col in CHRONIC_COLUMNS if col in df.columns]
        if cc_present:
            df["ChronicConditionCount"] = df[cc_present].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
        else:
            df["ChronicConditionCount"] = 2.0
    else:
        df["ChronicConditionCount"] = pd.to_numeric(df["ChronicConditionCount"], errors="coerce").fillna(2.0)

    if "NoOfMonths_PartACov" not in df.columns:
        df["NoOfMonths_PartACov"] = 12.0
    else:
        df["NoOfMonths_PartACov"] = pd.to_numeric(df["NoOfMonths_PartACov"], errors="coerce").fillna(12.0)

    if "NoOfMonths_PartBCov" not in df.columns:
        df["NoOfMonths_PartBCov"] = 12.0
    else:
        df["NoOfMonths_PartBCov"] = pd.to_numeric(df["NoOfMonths_PartBCov"], errors="coerce").fillna(12.0)

    for cc in CHRONIC_COLUMNS:
        if cc not in df.columns:
            df[cc] = 0
        else:
            # Chronic conditions are often 1 (Yes) or 2 (No) in CMS datasets, normalize 2 -> 0 or keep 0/1
            s = pd.to_numeric(df[cc], errors="coerce").fillna(0)
            # if values are 1 and 2, map 2 to 0
            if set(s.unique()).issubset({0, 1, 2}):
                s = s.map({1: 1, 2: 0, 0: 0}).fillna(0)
            df[cc] = s

    return df
