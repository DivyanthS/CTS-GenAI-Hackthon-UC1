from __future__ import annotations

from typing import Any
from sqlalchemy import desc, asc
from models.database import get_db
from models.provider import Provider
from models.claim import Claim
from models.risk_assessment import RiskAssessment
from models.risk_factor import RiskFactor


class ProviderDataService:
    """
    Database-backed service for retrieving provider records, statistics,
    and fraud risk profiles.
    """

    def get_providers(
        self,
        page: int = 1,
        page_size: int = 50,
        risk_level: str | None = None,
        search: str | None = None,
        sort_by: str = "risk_score",
        sort_order: str = "desc",
        run_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Return paginated, sorted, and filtered providers from the database.
        """
        if page < 1:
            raise ValueError("Page must be >= 1.")
        if page_size < 1 or page_size > 500:
            raise ValueError("Page size must be between 1 and 500.")

        with get_db() as db:
            query = db.query(Provider)

            if run_id:
                query = query.filter(Provider.analysis_run_id == run_id)

            if risk_level and risk_level.lower() != "all":
                clean_level = risk_level.strip().capitalize()
                query = query.filter(Provider.risk_level == clean_level)

            if search:
                term = f"%{search.strip()}%"
                query = query.filter(Provider.provider_id.ilike(term))

            total = query.count()

            # Sorting
            sort_column = getattr(Provider, sort_by, Provider.risk_score)
            if str(sort_order).lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))

            offset = (page - 1) * page_size
            providers = query.offset(offset).limit(page_size).all()

            results: list[dict[str, Any]] = []
            for p in providers:
                # Include both standard ORM fields and legacy capitalized fields for frontend compatibility
                record = {
                    "id": p.id,
                    "provider_id": p.provider_id,
                    "provider_name": p.provider_name,
                    "risk_score": p.risk_score,
                    "risk_probability": p.risk_probability,
                    "risk_level": p.risk_level,
                    "risk_status": p.risk_status,
                    "total_claims": p.total_claims,
                    "unique_beneficiaries": p.unique_beneficiaries,
                    "total_reimbursement": p.total_reimbursement,
                    "average_reimbursement": p.average_reimbursement,
                    "max_reimbursement": p.max_reimbursement,
                    "std_reimbursement": p.std_reimbursement,
                    "total_deductible_paid": p.total_deductible_paid,
                    "average_deductible_paid": p.average_deductible_paid,
                    "claims_per_beneficiary": p.claims_per_beneficiary,
                    "inpatient_share": p.inpatient_share,
                    "outpatient_share": p.outpatient_share,
                    "average_patient_age": p.average_patient_age,
                    "average_chronic_condition_count": p.average_chronic_condition_count,
                    "average_part_a_coverage": p.average_part_a_coverage,
                    "average_part_b_coverage": p.average_part_b_coverage,
                    "unique_attending_physicians": p.unique_attending_physicians,
                    "unique_operating_physicians": p.unique_operating_physicians,
                    "unique_other_physicians": p.unique_other_physicians,
                    # Legacy fields:
                    "Provider": p.provider_id,
                    "TotalClaims": p.total_claims,
                    "UniqueBeneficiaries": p.unique_beneficiaries,
                    "TotalReimbursement": p.total_reimbursement,
                    "AverageReimbursement": p.average_reimbursement,
                    "MaxReimbursement": p.max_reimbursement,
                    "StdReimbursement": p.std_reimbursement,
                    "InpatientShare": p.inpatient_share,
                    "AveragePatientAge": p.average_patient_age,
                    "AverageDeductiblePaid": p.average_deductible_paid,
                    "ClaimsPerBeneficiary": p.claims_per_beneficiary,
                    "fraud_probability": p.risk_probability,
                    "threshold": 0.5,
                    "decision": p.risk_status,
                }
                results.append(record)

            return results, total

    def get_provider(self, provider_id: str) -> dict[str, Any]:
        """
        Return complete provider details, risk assessment, risk factors, and summary statistics.
        """
        clean_id = str(provider_id).strip()
        with get_db() as db:
            provider = (
                db.query(Provider)
                .filter(Provider.provider_id == clean_id)
                .order_by(Provider.id.desc())
                .first()
            )

            if not provider:
                raise KeyError(f"Provider not found: {clean_id}")

            # Get latest risk assessment & factors
            ra = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.provider_id == clean_id)
                .order_by(RiskAssessment.id.desc())
                .first()
            )

            factors = []
            if ra:
                for rf in ra.risk_factors:
                    factors.append({
                        "name": rf.factor_name,
                        "provider_value": rf.factor_value,
                        "benchmark": rf.benchmark_value,
                        "difference_percent": rf.difference_percent,
                        "impact": rf.impact,
                        "severity": rf.severity,
                        "explanation": rf.explanation,
                    })

            # Claims summary
            total_claims = provider.total_claims
            inpatient_claims = int(round(total_claims * provider.inpatient_share))
            outpatient_claims = total_claims - inpatient_claims

            # Build provider payload
            provider_dict = {
                "id": provider.id,
                "provider_id": provider.provider_id,
                "provider_name": provider.provider_name,
                "risk_score": provider.risk_score,
                "risk_probability": provider.risk_probability,
                "risk_level": provider.risk_level,
                "risk_status": provider.risk_status,
                "total_claims": provider.total_claims,
                "unique_beneficiaries": provider.unique_beneficiaries,
                "total_reimbursement": provider.total_reimbursement,
                "average_reimbursement": provider.average_reimbursement,
                "max_reimbursement": provider.max_reimbursement,
                "std_reimbursement": provider.std_reimbursement,
                "total_deductible_paid": provider.total_deductible_paid,
                "average_deductible_paid": provider.average_deductible_paid,
                "claims_per_beneficiary": provider.claims_per_beneficiary,
                "inpatient_share": provider.inpatient_share,
                "outpatient_share": provider.outpatient_share,
                "average_patient_age": provider.average_patient_age,
                "average_chronic_condition_count": provider.average_chronic_condition_count,
                "average_part_a_coverage": provider.average_part_a_coverage,
                "average_part_b_coverage": provider.average_part_b_coverage,
                "unique_attending_physicians": provider.unique_attending_physicians,
                "unique_operating_physicians": provider.unique_operating_physicians,
                "unique_other_physicians": provider.unique_other_physicians,
                "risk_factors": factors,
                # Legacy fields for frontend compatibility
                "Provider": provider.provider_id,
                "TotalClaims": provider.total_claims,
                "UniqueBeneficiaries": provider.unique_beneficiaries,
                "TotalReimbursement": provider.total_reimbursement,
                "AverageReimbursement": provider.average_reimbursement,
                "MaxReimbursement": provider.max_reimbursement,
                "StdReimbursement": provider.std_reimbursement,
                "InpatientShare": provider.inpatient_share,
                "AveragePatientAge": provider.average_patient_age,
                "AverageDeductiblePaid": provider.average_deductible_paid,
                "ClaimsPerBeneficiary": provider.claims_per_beneficiary,
                "fraud_probability": provider.risk_probability,
                "threshold": 0.5,
                "decision": provider.risk_status,
            }

            return {
                "provider": provider_dict,
                "claims_summary": {
                    "total": total_claims,
                    "inpatient": inpatient_claims,
                    "outpatient": outpatient_claims,
                },
                "risk": {
                    "score": provider.risk_score,
                    "probability": provider.risk_probability,
                    "level": provider.risk_level,
                    "decision": provider.risk_status,
                },
                "risk_factors": factors,
                "charts": {
                    "reimbursement": [
                        {"name": "Total Reimbursement", "value": provider.total_reimbursement},
                        {"name": "Average Reimbursement", "value": provider.average_reimbursement},
                        {"name": "Max Reimbursement", "value": provider.max_reimbursement},
                    ],
                    "claims": [
                        {"name": "Inpatient", "value": inpatient_claims},
                        {"name": "Outpatient", "value": outpatient_claims},
                    ],
                },
            }

    def provider_exists(self, provider_id: str) -> bool:
        clean_id = str(provider_id).strip()
        with get_db() as db:
            return db.query(Provider).filter(Provider.provider_id == clean_id).first() is not None

    @property
    def provider_count(self) -> int:
        with get_db() as db:
            return db.query(Provider).count()