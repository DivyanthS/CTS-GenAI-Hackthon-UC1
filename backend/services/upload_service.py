from __future__ import annotations

import io
from pathlib import Path
from typing import Any
import pandas as pd
from werkzeug.utils import secure_filename

from config.settings import UPLOAD_DIR
from models.database import get_db
from models.analysis_run import AnalysisRun
from models.provider import Provider
from models.claim import Claim
from models.risk_assessment import RiskAssessment
from models.risk_factor import RiskFactor
from services.risk.base import RiskEngine
from services.feature_engineering.provider_features import build_provider_features
from utils.dataframe_utils import normalize_dataframe_columns, ensure_required_dataset_columns
from utils.risk_utils import generate_provider_name, generate_run_id


class UploadService:
    """
    Handles CSV dataset upload, feature engineering, batch risk scoring,
    and bulk ORM database persistence.
    """

    def __init__(self, risk_engine: RiskEngine):
        self.risk_engine = risk_engine

    def process_csv_upload(
        self,
        file_bytes: bytes,
        original_filename: str,
    ) -> dict[str, Any]:
        """
        Execute full ingestion, scoring, and persistence pipeline for uploaded CSV.
        """
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        # 1. Parse CSV with pandas
        try:
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), low_memory=False)
            except UnicodeDecodeError:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1", low_memory=False)
        except Exception as exc:
            raise ValueError(f"Could not parse CSV file: {str(exc)}") from exc

        if df_raw.empty:
            raise ValueError("Uploaded CSV dataset contains no data rows.")

        # 2. Normalize columns & ensure required fields
        df_norm = normalize_dataframe_columns(df_raw)
        df_clean = ensure_required_dataset_columns(df_norm)

        # 3. Save copy of uploaded file
        safe_name = secure_filename(original_filename) or "uploaded_claims.csv"
        run_id = generate_run_id()
        saved_filename = f"{run_id}_{safe_name}"
        save_path = UPLOAD_DIR / saved_filename
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # 4. Generate Provider Features
        provider_features = build_provider_features(df_clean)

        # 5. Run Batch Risk Scoring through RiskEngine
        risk_results = self.risk_engine.predict_batch(provider_features, df_clean)

        # Combine provider features with predictions
        scored_providers_df = provider_features.merge(
            risk_results[["Provider", "risk_score", "risk_probability", "risk_level", "decision", "risk_factors", "model_type", "model_version"]],
            on="Provider",
            how="left",
        )

        # 6. Calculate Run Aggregates
        total_rows = int(len(df_clean))
        total_cols = int(len(df_raw.columns))
        total_providers = int(len(scored_providers_df))
        total_claims = int(df_clean["ClaimID"].nunique())
        total_bene = int(df_clean["BeneID"].nunique())

        low_count = int((scored_providers_df["risk_level"] == "Low").sum())
        med_count = int((scored_providers_df["risk_level"] == "Medium").sum())
        high_count = int((scored_providers_df["risk_level"] == "High").sum())
        crit_count = int((scored_providers_df["risk_level"] == "Critical").sum())

        total_reimb = float(df_clean["InscClaimAmtReimbursed"].sum())

        # 7. Persist to Database via SQLAlchemy ORM
        with get_db() as db:
            # Create AnalysisRun
            analysis_run = AnalysisRun(
                run_id=run_id,
                filename=original_filename,
                total_rows=total_rows,
                total_columns=total_cols,
                total_providers=total_providers,
                total_claims=total_claims,
                total_beneficiaries=total_bene,
                low_count=low_count,
                medium_count=med_count,
                high_count=high_count,
                critical_count=crit_count,
                total_reimbursement=total_reimb,
                status="completed",
            )
            db.add(analysis_run)
            db.flush()

            # Insert / Update Providers
            provider_orm_objects = []
            risk_assessments_map = {}  # provider_id -> (RiskAssessment, list_of_factors)

            for _, row in scored_providers_df.iterrows():
                pid = str(row["Provider"]).strip()
                pname = generate_provider_name(pid)

                provider_obj = Provider(
                    provider_id=pid,
                    potential_fraud=int(row.get("PotentialFraud", 0) if "PotentialFraud" in row and not pd.isna(row.get("PotentialFraud")) else 0),
                    analysis_run_id=run_id,
                    risk_score=float(row["risk_score"]),
                    risk_probability=float(row["risk_probability"]),
                    risk_level=str(row["risk_level"]),
                    risk_status=str(row["decision"]),
                    total_claims=int(row.get("TotalClaims", 0)),
                    unique_beneficiaries=int(row.get("UniqueBeneficiaries", 0)),
                    total_reimbursement=float(row.get("TotalReimbursement", 0.0)),
                    average_reimbursement=float(row.get("AverageReimbursement", 0.0)),
                    max_reimbursement=float(row.get("MaxReimbursement", 0.0)),
                    std_reimbursement=float(row.get("StdReimbursement", 0.0)),
                    total_deductible_paid=float(row.get("TotalDeductiblePaid", 0.0)),
                    average_deductible_paid=float(row.get("AverageDeductiblePaid", 0.0)),
                    claims_per_beneficiary=float(row.get("ClaimsPerBeneficiary", 0.0)),
                    inpatient_share=float(row.get("InpatientShare", 0.0)),
                    average_patient_age=float(row.get("AveragePatientAge", 0.0)),
                    average_chronic_condition_count=float(row.get("AverageChronicConditionCount", 0.0)),
                    average_part_a_coverage=float(row.get("AveragePartACoverage", 0.0)),
                    average_part_b_coverage=float(row.get("AveragePartBCoverage", 0.0)),
                    unique_attending_physicians=int(row.get("UniqueAttendingPhysicians", 0)),
                    unique_operating_physicians=int(row.get("UniqueOperatingPhysicians", 0)),
                    unique_other_physicians=int(row.get("UniqueOtherPhysicians", 0)),
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
                )
                provider_orm_objects.append(provider_obj)

                # Risk Assessment object
                ra_obj = RiskAssessment(
                    provider_id=pid,
                    analysis_run_id=run_id,
                    risk_probability=float(row["risk_probability"]),
                    risk_score=float(row["risk_score"]),
                    risk_level=str(row["risk_level"]),
                    decision=str(row["decision"]),
                    model_type=str(row["model_type"]),
                    model_version=str(row["model_version"]),
                    summary=f"Provider {pid} evaluated as {row['risk_level']} risk ({row['risk_score']:.1f}/100).",
                )
                risk_assessments_map[pid] = (ra_obj, row["risk_factors"])

            for p_obj in provider_orm_objects:
                existing = db.query(Provider).filter(Provider.provider_id == p_obj.provider_id).first()
                if existing:
                    # Update existing provider with new data
                    for attr in [
                        "potential_fraud", "analysis_run_id", "risk_score", "risk_probability",
                        "risk_level", "risk_status", "total_claims", "unique_beneficiaries",
                        "total_reimbursement", "average_reimbursement", "max_reimbursement",
                        "std_reimbursement", "total_deductible_paid", "average_deductible_paid",
                        "claims_per_beneficiary", "inpatient_share", "average_patient_age",
                        "average_chronic_condition_count", "average_part_a_coverage",
                        "average_part_b_coverage", "unique_attending_physicians",
                        "unique_operating_physicians", "unique_other_physicians",
                        "chronic_cond_alzheimer", "chronic_cond_heartfailure",
                        "chronic_cond_kidney_disease", "chronic_cond_cancer",
                        "chronic_cond_obstr_pulmonary", "chronic_cond_depression",
                        "chronic_cond_diabetes", "chronic_cond_ischemic_heart",
                        "chronic_cond_osteoporasis", "chronic_cond_rheumatoidarthritis",
                        "chronic_cond_stroke", "average_deductible_paid_missing",
                        "std_reimbursement_missing",
                    ]:
                        setattr(existing, attr, getattr(p_obj, attr))
                else:
                    db.add(p_obj)
            db.flush()

            # Insert Risk Assessments and Risk Factors
            for pid, (ra, factors) in risk_assessments_map.items():
                db.add(ra)
                db.flush()  # Flush to populate ra.id

                for f in factors:
                    rf = RiskFactor(
                        risk_assessment_id=ra.id,
                        factor_name=f["name"],
                        factor_value=f.get("provider_value"),
                        benchmark_value=f.get("benchmark"),
                        difference_percent=f.get("difference_percent"),
                        impact=f.get("impact", "MEDIUM"),
                        severity=f.get("severity", "MEDIUM"),
                        explanation=f["explanation"],
                    )
                    db.add(rf)

            # Insert Claims (preserve raw_data)
            claim_objects = []
            for _, c_row in df_clean.iterrows():
                cid = str(c_row["ClaimID"]).strip()
                pid = str(c_row["Provider"]).strip()
                bene_id = str(c_row.get("BeneID", ""))
                ctype = str(c_row.get("ClaimType", "Outpatient"))
                reimb = float(c_row.get("InscClaimAmtReimbursed", 0.0) or 0.0)
                deduct = float(c_row.get("DeductibleAmtPaid", 0.0) or 0.0)
                start_dt = str(c_row.get("ClaimStartDt", "")) if pd.notna(c_row.get("ClaimStartDt")) else None
                end_dt = str(c_row.get("ClaimEndDt", "")) if pd.notna(c_row.get("ClaimEndDt")) else None
                att_phys = str(c_row.get("AttendingPhysician", "")) if pd.notna(c_row.get("AttendingPhysician")) else None
                op_phys = str(c_row.get("OperatingPhysician", "")) if pd.notna(c_row.get("OperatingPhysician")) else None
                oth_phys = str(c_row.get("OtherPhysician", "")) if pd.notna(c_row.get("OtherPhysician")) else None
                pot_fraud = str(c_row.get("PotentialFraud", "")) if pd.notna(c_row.get("PotentialFraud")) else None

                # Clean raw data dict
                raw_dict = {
                    k: (None if pd.isna(v) else v)
                    for k, v in c_row.to_dict().items()
                }

                claim_obj = Claim(
                    claim_id=cid,
                    provider_id=pid,
                    analysis_run_id=run_id,
                    beneficiary_id=bene_id,
                    claim_type=ctype,
                    claim_start_date=start_dt,
                    claim_end_date=end_dt,
                    reimbursement_amount=reimb,
                    deductible_amount=deduct,
                    attending_physician=att_phys,
                    operating_physician=op_phys,
                    other_physician=oth_phys,
                    potential_fraud=pot_fraud,
                    raw_data=raw_dict,
                )
                claim_objects.append(claim_obj)

            db.bulk_save_objects(claim_objects)
            db.commit()

        # 8. Build Top Risky Providers for Response
        top_risky = (
            scored_providers_df.sort_values("risk_score", ascending=False)
            .head(10)
        )
        top_risky_list = []
        for _, r in top_risky.iterrows():
            top_risky_list.append({
                "provider_id": r["Provider"],
                "provider_name": generate_provider_name(r["Provider"]),
                "risk_score": round(float(r["risk_score"]), 2),
                "risk_level": r["risk_level"],
                "total_claims": int(r["TotalClaims"]),
                "total_reimbursement": round(float(r["TotalReimbursement"]), 2),
                "average_reimbursement": round(float(r["AverageReimbursement"]), 2),
                "primary_risk_factor": r["risk_factors"][0]["explanation"] if r["risk_factors"] else "High composite anomaly score",
            })

        # 9. Return complete upload response
        avg_claim_reimb = round(total_reimb / max(1, total_claims), 2)
        avg_provider_claims = round(total_claims / max(1, total_providers), 1)

        return {
            "run_id": run_id,
            "dataset": {
                "filename": original_filename,
                "rows": total_rows,
                "columns": total_cols,
                "providers": total_providers,
                "beneficiaries": total_bene,
            },
            "risk_summary": {
                "low": low_count,
                "medium": med_count,
                "high": high_count,
                "critical": crit_count,
            },
            "top_risky_providers": top_risky_list,
            "analytics": {
                "total_claims": total_claims,
                "total_providers": total_providers,
                "total_beneficiaries": total_bene,
                "total_reimbursement": round(total_reimb, 2),
                "average_claim_reimbursement": avg_claim_reimb,
                "average_provider_claims": avg_provider_claims,
                "high_risk_percentage": round(((high_count + crit_count) / max(1, total_providers)) * 100.0, 1),
            },
            "status": "completed",
        }
