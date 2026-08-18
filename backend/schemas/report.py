from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class ReportSummary(BaseModel):
    run_id: str
    summary: dict[str, Any]
    risk_distribution: dict[str, Any]
    high_risk_providers: list[dict[str, Any]]
    medium_risk_providers: list[dict[str, Any]]
    low_risk_providers: list[dict[str, Any]]
    critical_providers: list[dict[str, Any]]
    top_risk_factors: list[dict[str, Any]]
    charts: dict[str, Any]
