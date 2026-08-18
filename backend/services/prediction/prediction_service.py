from __future__ import annotations

from typing import Any
from services.risk.base import RiskEngine
from services.risk.threshold_engine import threshold_engine
from services.prediction.model_adapter import normalize_prediction_output
from models.database import get_db
from models.provider import Provider
from models.risk_assessment import RiskAssessment
from models.risk_factor import RiskFactor


class PredictionService:
    """
    Coordinates provider prediction requests using the configured RiskEngine,
    evaluating features against the ThresholdEngine and persisting
    RiskAssessment and RiskFactor entities to PostgreSQL / database.
    """

    def __init__(self, risk_engine: RiskEngine):
        self.risk_engine = risk_engine

    def predict(self, provider_id: str) -> dict[str, Any]:
        """Generate, record, and persist a standardized fraud-risk prediction for one provider."""
        clean_id = str(provider_id).strip()

        with get_db() as db:
            provider = db.query(Provider).filter(Provider.provider_id == clean_id).first()

            if provider is None:
                # If not in database, attempt ad-hoc scoring using risk engine
                raw_prediction = self.risk_engine.predict_provider({"Provider": clean_id})
                return normalize_prediction_output(raw_prediction)

            # Build feature dictionary from provider record (Strictly excluding PotentialFraud)
            features = {
                "Provider": provider.provider_id,
                "TotalClaims": float(provider.total_claims or 0),
                "UniqueBeneficiaries": float(provider.unique_beneficiaries or 0),
                "TotalReimbursement": float(provider.total_reimbursement or 0.0),
                "AverageReimbursement": float(provider.average_reimbursement or 0.0),
                "MaxReimbursement": float(provider.max_reimbursement or 0.0),
                "StdReimbursement": float(provider.std_reimbursement or 0.0),
                "TotalDeductiblePaid": float(provider.total_deductible_paid or 0.0),
                "AverageDeductiblePaid": float(provider.average_deductible_paid or 0.0),
                "UniqueAttendingPhysicians": float(provider.unique_attending_physicians or 0),
                "UniqueOperatingPhysicians": float(provider.unique_operating_physicians or 0),
                "UniqueOtherPhysicians": float(provider.unique_other_physicians or 0),
                "ClaimsPerBeneficiary": float(provider.claims_per_beneficiary or 0.0),
                "InpatientShare": float(provider.inpatient_share or 0.0),
                "AveragePatientAge": float(provider.average_patient_age or 0.0),
                "AverageChronicConditionCount": float(provider.average_chronic_condition_count or 0.0),
                "AveragePartACoverage": float(provider.average_part_a_coverage or 0.0),
                "AveragePartBCoverage": float(provider.average_part_b_coverage or 0.0),
                "ChronicCond_Alzheimer": float(provider.chronic_cond_alzheimer or 0.0),
                "ChronicCond_Heartfailure": float(provider.chronic_cond_heartfailure or 0.0),
                "ChronicCond_KidneyDisease": float(provider.chronic_cond_kidney_disease or 0.0),
                "ChronicCond_Cancer": float(provider.chronic_cond_cancer or 0.0),
                "ChronicCond_ObstrPulmonary": float(provider.chronic_cond_obstr_pulmonary or 0.0),
                "ChronicCond_Depression": float(provider.chronic_cond_depression or 0.0),
                "ChronicCond_Diabetes": float(provider.chronic_cond_diabetes or 0.0),
                "ChronicCond_IschemicHeart": float(provider.chronic_cond_ischemic_heart or 0.0),
                "ChronicCond_Osteoporasis": float(provider.chronic_cond_osteoporasis or 0.0),
                "ChronicCond_rheumatoidarthritis": float(provider.chronic_cond_rheumatoidarthritis or 0.0),
                "ChronicCond_stroke": float(provider.chronic_cond_stroke or 0.0),
                "AverageDeductiblePaid_Missing": float(provider.average_deductible_paid_missing or 0),
                "StdReimbursement_Missing": float(provider.std_reimbursement_missing or 0),
            }

            # Run inference through configured RiskEngine
            raw_prediction = self.risk_engine.predict_provider(features)

            prob = float(raw_prediction.get("risk_probability") or (raw_prediction.get("risk_score", 0.0) / 100.0))
            score = float(raw_prediction.get("risk_score") or (prob * 100.0))

            # Classify using ThresholdEngine
            level, decision, _ = threshold_engine.classify(prob)

            # Update provider record
            provider.risk_score = score
            provider.risk_probability = prob
            provider.risk_level = level
            provider.risk_status = decision

            # Persist RiskAssessment
            factors = raw_prediction.get("risk_factors") or []
            assessment = RiskAssessment(
                provider_id=provider.provider_id,
                analysis_run_id=provider.analysis_run_id,
                risk_score=score,
                risk_probability=prob,
                risk_level=level,
                decision=decision,
                model_type=self.risk_engine.engine_type,
                model_version=self.risk_engine.version,
                summary=f"Evaluated with {self.risk_engine.engine_type} model. Result: {level} ({decision}).",
            )
            db.add(assessment)
            db.flush()

            # Persist RiskFactors if any
            for f in factors:
                factor_obj = RiskFactor(
                    risk_assessment_id=assessment.id,
                    factor_name=f.get("name", "Unknown Factor"),
                    factor_value=float(f.get("provider_value", 0.0)),
                    benchmark_value=float(f.get("benchmark", 0.0)),
                    difference_percent=float(f.get("difference_percent", 0.0)),
                    impact=f.get("impact", "MEDIUM"),
                    severity=f.get("severity", "MEDIUM"),
                    explanation=f.get("explanation", ""),
                )
                db.add(factor_obj)

            output_data = {
                "provider_id": provider.provider_id,
                "Provider": provider.provider_id,
                "risk_score": score,
                "risk_probability": prob,
                "risk_level": level,
                "decision": decision,
                "model_type": self.risk_engine.engine_type,
                "model_version": self.risk_engine.version,
                "risk_factors": factors,
                "threshold": threshold_engine.low_threshold,
            }
            return normalize_prediction_output(output_data)
