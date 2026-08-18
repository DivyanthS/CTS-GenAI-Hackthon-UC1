from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class ClaimListItem(BaseModel):
    claim_id: str
    provider_id: str
    beneficiary_id: str | None = None
    claim_type: str = "Outpatient"
    reimbursement_amount: float = 0.0
    deductible_amount: float = 0.0
    claim_start_date: str | None = None
    claim_end_date: str | None = None
    attending_physician: str | None = None
    operating_physician: str | None = None
    other_physician: str | None = None
    potential_fraud: str | None = None

    # Legacy fields matching BackendClaim for frontend mapBackendClaim:
    ClaimID: str | None = None
    Provider: str | None = None
    BeneID: str | None = None
    ClaimType: str | None = None
    InscClaimAmtReimbursed: float | None = None
    ClaimStartDt: str | None = None
    ClaimEndDt: str | None = None
    AttendingPhysician: str | None = None
    OperatingPhysician: str | None = None
    OtherPhysician: str | None = None
    PotentialFraud: str | None = None


class ClaimListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    provider_id: str | None = None
    claims: list[dict[str, Any]]
