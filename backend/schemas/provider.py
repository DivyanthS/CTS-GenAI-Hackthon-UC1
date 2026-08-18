from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class ProviderListItem(BaseModel):
    provider_id: str
    provider_name: str
    risk_score: float
    risk_probability: float
    risk_level: str
    risk_status: str

    total_claims: int
    unique_beneficiaries: int
    total_reimbursement: float
    average_reimbursement: float
    max_reimbursement: float
    inpatient_share: float
    outpatient_share: float

    # Legacy fields for backward compatibility with frontend:
    Provider: str | None = None
    TotalClaims: int | None = None
    UniqueBeneficiaries: int | None = None
    TotalReimbursement: float | None = None
    AverageReimbursement: float | None = None
    MaxReimbursement: float | None = None
    StdReimbursement: float | None = None
    InpatientShare: float | None = None
    AveragePatientAge: float | None = None
    AverageDeductiblePaid: float | None = None
    ClaimsPerBeneficiary: float | None = None
    fraud_probability: float | None = None
    threshold: float | None = 0.5
    decision: str | None = None


class ProviderListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    providers: list[dict[str, Any]]
