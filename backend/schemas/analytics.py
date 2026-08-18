from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_claims: int
    total_providers: int
    total_beneficiaries: int

    low_risk: int
    medium_risk: int
    high_risk: int
    critical_risk: int

    total_reimbursement: float
    average_claim_reimbursement: float
    average_provider_claims: float
    high_risk_percentage: float

    # Legacy fields for frontend compatibility
    fraud_flagged: int | None = None
    not_flagged: int | None = None
    fraud_rate: float | None = None
    threshold: float | None = 0.5
    average_provider_average_reimbursement: float | None = None
    average_provider_inpatient_claims: float | None = None


class ChartItem(BaseModel):
    name: str
    value: float | int


class ReimbursementByRiskItem(BaseModel):
    risk: str
    amount: float


class AnalyticsCharts(BaseModel):
    risk_distribution: list[dict[str, Any]]
    reimbursement_by_risk: list[dict[str, Any]]
    claims_by_type: list[dict[str, Any]]
    top_risky_providers: list[dict[str, Any]]
    reimbursement_distribution: list[dict[str, Any]] = []
    claims_distribution: list[dict[str, Any]] = []
    top_providers_by_reimbursement: list[dict[str, Any]] = []
