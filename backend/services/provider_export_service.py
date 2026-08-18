from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

from config.settings import EXPORT_DIR, AUTO_RETRAIN_AFTER_TRAINING_EXPORT
from models.database import get_db
from models.provider import Provider

# 30 model feature columns
FEATURE_COLUMNS = [
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

INFERENCE_COLUMNS = ["Provider"] + FEATURE_COLUMNS
TRAINING_COLUMNS = ["Provider", "PotentialFraud"] + FEATURE_COLUMNS


class ProviderExportService:
    """
    Dedicated export service for querying Provider records from the database
    and generating CSV files with strict purpose separation:
      1. INFERENCE EXPORT (31 columns: Provider + 30 features)
      2. TRAINING EXPORT (32 columns: Provider + PotentialFraud + 30 features)
    """

    def __init__(self, training_service=None):
        self.training_service = training_service

    def _query_provider_records(self, run_id: str | None = None) -> list[dict[str, Any]]:
        with get_db() as db:
            query = db.query(Provider)
            if run_id:
                query = query.filter(Provider.analysis_run_id == run_id)
            providers = query.all()

            if not providers:
                # If filtered by run_id returned empty, try all providers as fallback
                providers = db.query(Provider).all()

            records = []
            for p in providers:
                rec = {
                    "Provider": str(p.provider_id),
                    "PotentialFraud": int(p.potential_fraud or 0),
                    "TotalClaims": int(p.total_claims or 0),
                    "UniqueBeneficiaries": int(p.unique_beneficiaries or 0),
                    "TotalReimbursement": float(p.total_reimbursement or 0.0),
                    "AverageReimbursement": float(p.average_reimbursement or 0.0),
                    "MaxReimbursement": float(p.max_reimbursement or 0.0),
                    "StdReimbursement": float(p.std_reimbursement or 0.0),
                    "TotalDeductiblePaid": float(p.total_deductible_paid or 0.0),
                    "AverageDeductiblePaid": float(p.average_deductible_paid or 0.0),
                    "UniqueAttendingPhysicians": int(p.unique_attending_physicians or 0),
                    "UniqueOperatingPhysicians": int(p.unique_operating_physicians or 0),
                    "UniqueOtherPhysicians": int(p.unique_other_physicians or 0),
                    "ClaimsPerBeneficiary": float(p.claims_per_beneficiary or 0.0),
                    "InpatientShare": float(p.inpatient_share or 0.0),
                    "AveragePatientAge": float(p.average_patient_age or 0.0),
                    "AverageChronicConditionCount": float(p.average_chronic_condition_count or 0.0),
                    "AveragePartACoverage": float(p.average_part_a_coverage or 0.0),
                    "AveragePartBCoverage": float(p.average_part_b_coverage or 0.0),
                    "ChronicCond_Alzheimer": float(p.chronic_cond_alzheimer or 0.0),
                    "ChronicCond_Heartfailure": float(p.chronic_cond_heartfailure or 0.0),
                    "ChronicCond_KidneyDisease": float(p.chronic_cond_kidney_disease or 0.0),
                    "ChronicCond_Cancer": float(p.chronic_cond_cancer or 0.0),
                    "ChronicCond_ObstrPulmonary": float(p.chronic_cond_obstr_pulmonary or 0.0),
                    "ChronicCond_Depression": float(p.chronic_cond_depression or 0.0),
                    "ChronicCond_Diabetes": float(p.chronic_cond_diabetes or 0.0),
                    "ChronicCond_IschemicHeart": float(p.chronic_cond_ischemic_heart or 0.0),
                    "ChronicCond_Osteoporasis": float(p.chronic_cond_osteoporasis or 0.0),
                    "ChronicCond_rheumatoidarthritis": float(p.chronic_cond_rheumatoidarthritis or 0.0),
                    "ChronicCond_stroke": float(p.chronic_cond_stroke or 0.0),
                    "AverageDeductiblePaid_Missing": int(p.average_deductible_paid_missing or 0),
                    "StdReimbursement_Missing": int(p.std_reimbursement_missing or 0),
                }
                records.append(rec)

            return records

    def export_for_inference(
        self,
        run_id: str | None = None,
        output_path: Path | str | None = None,
    ) -> dict[str, Any]:
        """
        Export provider features formatted specifically for inference (31 columns).
        """
        records = self._query_provider_records(run_id=run_id)
        if not records:
            raise ValueError("No provider records found in database to export.")

        df = pd.DataFrame(records)[INFERENCE_COLUMNS]

        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"providers_inference_{now_str}.csv"
        target_path = Path(output_path) if output_path else EXPORT_DIR / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(target_path, index=False, encoding="utf-8")

        return {
            "status": "success",
            "file": str(target_path),
            "filename": target_path.name,
            "rows": len(df),
            "columns": len(INFERENCE_COLUMNS),
            "purpose": "inference",
            "column_list": INFERENCE_COLUMNS,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def export_for_training(
        self,
        run_id: str | None = None,
        output_path: Path | str | None = None,
        trigger_training: bool | None = None,
    ) -> dict[str, Any]:
        """
        Export provider features with PotentialFraud ground truth label (32 columns)
        formatted for model training / retraining.
        """
        records = self._query_provider_records(run_id=run_id)
        if not records:
            raise ValueError("No provider records found in database to export.")

        df = pd.DataFrame(records)[TRAINING_COLUMNS]

        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"providers_training_{now_str}.csv"
        target_path = Path(output_path) if output_path else EXPORT_DIR / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(target_path, index=False, encoding="utf-8")

        # Auto-retraining check
        should_retrain = trigger_training if trigger_training is not None else AUTO_RETRAIN_AFTER_TRAINING_EXPORT
        retraining_job_id = None

        if should_retrain and self.training_service is not None:
            job = self.training_service.trigger_training_job(training_csv_path=str(target_path))
            retraining_job_id = job.get("job_id")

        return {
            "status": "success",
            "file": str(target_path),
            "filename": target_path.name,
            "rows": len(df),
            "columns": len(TRAINING_COLUMNS),
            "purpose": "training",
            "column_list": TRAINING_COLUMNS,
            "potential_fraud_distribution": {
                "flagged_1": int((df["PotentialFraud"] == 1).sum()),
                "not_flagged_0": int((df["PotentialFraud"] == 0).sum()),
            },
            "retraining_triggered": should_retrain and (retraining_job_id is not None),
            "retraining_job_id": retraining_job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def export_providers_to_csv(
        self,
        purpose: str = "inference",
        run_id: str | None = None,
        output_path: Path | str | None = None,
        trigger_training: bool | None = None,
    ) -> dict[str, Any]:
        """Unified export router accepting purpose='inference' or purpose='training'."""
        purpose_clean = str(purpose).strip().lower()
        if purpose_clean == "training":
            return self.export_for_training(
                run_id=run_id,
                output_path=output_path,
                trigger_training=trigger_training,
            )
        else:
            return self.export_for_inference(
                run_id=run_id,
                output_path=output_path,
            )
