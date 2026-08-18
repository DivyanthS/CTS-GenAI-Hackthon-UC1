from __future__ import annotations

import io
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

from models.database import get_db
from models.provider import Provider
from models.analysis_run import AnalysisRun
from utils.risk_utils import generate_run_id

# Expected 32 dataset columns
PROVIDER_DATASET_COLUMNS = [
    "Provider",
    "PotentialFraud",
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


class ProviderImportService:
    """
    Dedicated ingestion service for provider-level datasets (32 columns).
    Validates data structure, normalizes types, maps to Provider ORM,
    and bulk-persists into PostgreSQL / database inside an atomic transaction.
    """

    def import_dataset(
        self,
        file_input: bytes | str | Path | io.BytesIO,
        filename: str = "provider_data.csv",
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Ingests provider dataset CSV and writes records directly to the database.
        """
        # 1. Parse CSV into DataFrame
        try:
            if isinstance(file_input, (bytes, bytearray)):
                df = pd.read_csv(io.BytesIO(file_input))
            elif isinstance(file_input, (str, Path)):
                df = pd.read_csv(file_input)
            elif hasattr(file_input, "read"):
                df = pd.read_csv(file_input)
            else:
                raise ValueError("Unsupported file input format.")
        except Exception as exc:
            raise ValueError(f"Failed to read CSV dataset: {str(exc)}") from exc

        if df.empty:
            raise ValueError("Uploaded provider CSV is empty.")

        # 2. Validate columns
        col_map = {col.strip().lower(): col for col in df.columns}
        missing_cols = []
        for expected in PROVIDER_DATASET_COLUMNS:
            if expected.lower() not in col_map:
                # PotentialFraud and missing indicators can be derived if not present
                if expected in ("PotentialFraud", "AverageDeductiblePaid_Missing", "StdReimbursement_Missing"):
                    continue
                missing_cols.append(expected)

        if missing_cols:
            raise ValueError(f"Dataset is missing required columns: {', '.join(missing_cols)}")

        # Normalize column names in DataFrame
        rename_dict = {}
        for expected in PROVIDER_DATASET_COLUMNS:
            if expected.lower() in col_map:
                rename_dict[col_map[expected.lower()]] = expected
        df = df.rename(columns=rename_dict)

        # 3. Clean & Validate PotentialFraud ground-truth label
        if "PotentialFraud" in df.columns:
            df["PotentialFraud"] = (
                df["PotentialFraud"]
                .astype(str)
                .str.strip()
                .map({"Yes": 1, "yes": 1, "Y": 1, "1": 1, 1: 1, "No": 0, "no": 0, "N": 0, "0": 0, 0: 0})
                .fillna(0)
                .astype(int)
            )
        else:
            df["PotentialFraud"] = 0

        # Fill missing indicators & numerical values
        if "AverageDeductiblePaid_Missing" not in df.columns:
            df["AverageDeductiblePaid_Missing"] = df["AverageDeductiblePaid"].isna().astype(int)
        if "StdReimbursement_Missing" not in df.columns:
            df["StdReimbursement_Missing"] = df["StdReimbursement"].isna().astype(int)

        df = df.fillna(0.0)

        effective_run_id = run_id or generate_run_id(prefix="RUN-PROV")
        total_rows = len(df)
        fraud_yes = int((df["PotentialFraud"] == 1).sum())
        fraud_no = total_rows - fraud_yes

        # 4. Map to SQLAlchemy Provider ORM records and bulk-insert in transaction
        with get_db() as db:
            # Create or update AnalysisRun
            run = db.query(AnalysisRun).filter(AnalysisRun.run_id == effective_run_id).first()
            if not run:
                run = AnalysisRun(
                    run_id=effective_run_id,
                    filename=filename,
                    total_rows=total_rows,
                    total_columns=len(df.columns),
                    total_providers=total_rows,
                    total_reimbursement=float(df["TotalReimbursement"].sum()),
                    status="imported",
                )
                db.add(run)
                db.flush()

            provider_objects = []
            for _, row in df.iterrows():
                pid = str(row["Provider"]).strip()
                p_obj = Provider(
                    provider_id=pid,
                    potential_fraud=int(row["PotentialFraud"]),
                    total_claims=int(row.get("TotalClaims", 0)),
                    unique_beneficiaries=int(row.get("UniqueBeneficiaries", 0)),
                    total_reimbursement=float(row.get("TotalReimbursement", 0.0)),
                    average_reimbursement=float(row.get("AverageReimbursement", 0.0)),
                    max_reimbursement=float(row.get("MaxReimbursement", 0.0)),
                    std_reimbursement=float(row.get("StdReimbursement", 0.0)),
                    total_deductible_paid=float(row.get("TotalDeductiblePaid", 0.0)),
                    average_deductible_paid=float(row.get("AverageDeductiblePaid", 0.0)),
                    unique_attending_physicians=int(row.get("UniqueAttendingPhysicians", 0)),
                    unique_operating_physicians=int(row.get("UniqueOperatingPhysicians", 0)),
                    unique_other_physicians=int(row.get("UniqueOtherPhysicians", 0)),
                    claims_per_beneficiary=float(row.get("ClaimsPerBeneficiary", 0.0)),
                    inpatient_share=float(row.get("InpatientShare", 0.0)),
                    average_patient_age=float(row.get("AveragePatientAge", 0.0)),
                    average_chronic_condition_count=float(row.get("AverageChronicConditionCount", 0.0)),
                    average_part_a_coverage=float(row.get("AveragePartACoverage", 0.0)),
                    average_part_b_coverage=float(row.get("AveragePartBCoverage", 0.0)),
                    chronic_cond_alzheimer=float(row.get("ChronicCond_Alzheimer", 0.0)),
                    chronic_cond_heartfailure=float(row.get("ChronicCond_Heartfailure", 0.0)),
                    chronic_cond_kidney_disease=float(row.get("ChronicCond_KidneyDisease", 0.0)),
                    chronic_cond_cancer=float(row.get("ChronicCond_Cancer", 0.0)),
                    chronic_cond_obstr_pulmonary=float(row.get("ChronicCond_ObstrPulmonary", 0.0)),
                    chronic_cond_depression=float(row.get("ChronicCond_Depression", 0.0)),
                    chronic_cond_diabetes=float(row.get("ChronicCond_Diabetes", 0.0)),
                    chronic_cond_ischemic_heart=float(row.get("ChronicCond_IschemicHeart", 0.0)),
                    chronic_cond_osteoporasis=float(row.get("ChronicCond_Osteoporasis", 0.0)),
                    chronic_cond_rheumatoidarthritis=float(row.get("ChronicCond_rheumatoidarthritis", 0.0)),
                    chronic_cond_stroke=float(row.get("ChronicCond_stroke", 0.0)),
                    average_deductible_paid_missing=int(row.get("AverageDeductiblePaid_Missing", 0)),
                    std_reimbursement_missing=int(row.get("StdReimbursement_Missing", 0)),
                    analysis_run_id=effective_run_id,
                )
                provider_objects.append(p_obj)

            for p_obj in provider_objects:
                existing = db.query(Provider).filter(Provider.provider_id == p_obj.provider_id).first()
                if existing:
                    for attr in [
                        "potential_fraud", "total_claims", "unique_beneficiaries",
                        "total_reimbursement", "average_reimbursement", "max_reimbursement",
                        "std_reimbursement", "total_deductible_paid", "average_deductible_paid",
                        "unique_attending_physicians", "unique_operating_physicians",
                        "unique_other_physicians", "claims_per_beneficiary", "inpatient_share",
                        "average_patient_age", "average_chronic_condition_count",
                        "average_part_a_coverage", "average_part_b_coverage",
                        "chronic_cond_alzheimer", "chronic_cond_heartfailure",
                        "chronic_cond_kidney_disease", "chronic_cond_cancer",
                        "chronic_cond_obstr_pulmonary", "chronic_cond_depression",
                        "chronic_cond_diabetes", "chronic_cond_ischemic_heart",
                        "chronic_cond_osteoporasis", "chronic_cond_rheumatoidarthritis",
                        "chronic_cond_stroke", "average_deductible_paid_missing",
                        "std_reimbursement_missing", "analysis_run_id",
                    ]:
                        setattr(existing, attr, getattr(p_obj, attr))
                else:
                    db.add(p_obj)
            # Transaction commits upon exit of context manager

        return {
            "status": "success",
            "message": f"Successfully imported {total_rows} provider records.",
            "run_id": effective_run_id,
            "filename": filename,
            "rows_imported": total_rows,
            "providers_count": total_rows,
            "columns_count": len(PROVIDER_DATASET_COLUMNS),
            "potential_fraud_distribution": {
                "flagged_1": fraud_yes,
                "not_flagged_0": fraud_no,
            },
        }
