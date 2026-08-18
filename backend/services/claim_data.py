from __future__ import annotations

from typing import Any
from models.database import get_db
from models.claim import Claim
from models.provider import Provider


class ClaimDataService:
    """
    Database-backed service for querying claim records, filtering, and pagination.
    """

    def get_claims(
        self,
        page: int = 1,
        page_size: int = 50,
        provider_id: str | None = None,
        claim_type: str | None = None,
        search: str | None = None,
        run_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Return paginated claims from the database.
        """
        if page < 1:
            raise ValueError("Page must be >= 1.")
        if page_size < 1 or page_size > 500:
            raise ValueError("Page size must be between 1 and 500.")

        with get_db() as db:
            query = db.query(Claim)

            if run_id:
                query = query.filter(Claim.analysis_run_id == run_id)

            if provider_id:
                clean_pid = str(provider_id).strip()
                query = query.filter(Claim.provider_id == clean_pid)

            if claim_type and claim_type.lower() != "all":
                clean_ctype = str(claim_type).strip().capitalize()
                query = query.filter(Claim.claim_type == clean_ctype)

            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    (Claim.claim_id.ilike(term))
                    | (Claim.provider_id.ilike(term))
                    | (Claim.beneficiary_id.ilike(term))
                )

            total = query.count()
            offset = (page - 1) * page_size
            claims = query.order_by(Claim.id.desc()).offset(offset).limit(page_size).all()

            results: list[dict[str, Any]] = []
            for c in claims:
                record = {
                    "id": c.id,
                    "claim_id": c.claim_id,
                    "provider_id": c.provider_id,
                    "beneficiary_id": c.beneficiary_id,
                    "claim_type": c.claim_type,
                    "claim_start_date": c.claim_start_date,
                    "claim_end_date": c.claim_end_date,
                    "reimbursement_amount": c.reimbursement_amount,
                    "deductible_amount": c.deductible_amount,
                    "attending_physician": c.attending_physician,
                    "operating_physician": c.operating_physician,
                    "other_physician": c.other_physician,
                    "potential_fraud": c.potential_fraud,
                    # Legacy fields:
                    "ClaimID": c.claim_id,
                    "Provider": c.provider_id,
                    "BeneID": c.beneficiary_id,
                    "ClaimType": c.claim_type,
                    "InscClaimAmtReimbursed": c.reimbursement_amount,
                    "DeductibleAmtPaid": c.deductible_amount,
                    "ClaimStartDt": c.claim_start_date,
                    "ClaimEndDt": c.claim_end_date,
                    "AttendingPhysician": c.attending_physician,
                    "OperatingPhysician": c.operating_physician,
                    "OtherPhysician": c.other_physician,
                    "PotentialFraud": c.potential_fraud,
                    "raw_data": c.raw_data or {},
                }
                results.append(record)

            return results, total

    def get_claim(self, claim_id: str) -> dict[str, Any]:
        """
        Return a single claim by claim_id.
        """
        clean_cid = str(claim_id).strip()
        with get_db() as db:
            c = db.query(Claim).filter(Claim.claim_id == clean_cid).order_by(Claim.id.desc()).first()
            if not c:
                raise KeyError(f"Claim not found: {clean_cid}")

            # Also fetch provider risk level if available
            prov = db.query(Provider).filter(Provider.provider_id == c.provider_id).first()
            prov_risk_level = prov.risk_level if prov else "Unknown"
            prov_risk_score = prov.risk_score if prov else 0.0

            return {
                "id": c.id,
                "claim_id": c.claim_id,
                "provider_id": c.provider_id,
                "beneficiary_id": c.beneficiary_id,
                "claim_type": c.claim_type,
                "claim_start_date": c.claim_start_date,
                "claim_end_date": c.claim_end_date,
                "reimbursement_amount": c.reimbursement_amount,
                "deductible_amount": c.deductible_amount,
                "attending_physician": c.attending_physician,
                "operating_physician": c.operating_physician,
                "other_physician": c.other_physician,
                "potential_fraud": c.potential_fraud,
                "provider_risk_level": prov_risk_level,
                "provider_risk_score": prov_risk_score,
                # Legacy fields:
                "ClaimID": c.claim_id,
                "Provider": c.provider_id,
                "BeneID": c.beneficiary_id,
                "ClaimType": c.claim_type,
                "InscClaimAmtReimbursed": c.reimbursement_amount,
                "DeductibleAmtPaid": c.deductible_amount,
                "ClaimStartDt": c.claim_start_date,
                "ClaimEndDt": c.claim_end_date,
                "AttendingPhysician": c.attending_physician,
                "OperatingPhysician": c.operating_physician,
                "OtherPhysician": c.other_physician,
                "PotentialFraud": c.potential_fraud,
                "raw_data": c.raw_data or {},
            }

    def claim_exists(self, claim_id: str) -> bool:
        clean_cid = str(claim_id).strip()
        with get_db() as db:
            return db.query(Claim).filter(Claim.claim_id == clean_cid).first() is not None

    @property
    def row_count(self) -> int:
        with get_db() as db:
            return db.query(Claim).count()