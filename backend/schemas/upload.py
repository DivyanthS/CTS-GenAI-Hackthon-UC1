from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class ValidationCheckSchema(BaseModel):
    name: str
    status: str  # PASS, WARNING, FAIL / pass, warn, fail
    message: str


class SchemaFieldSchema(BaseModel):
    field: str
    type: str
    required: bool
    status: str
    note: str


class ValidationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    health_score: int
    rows: int
    columns: int
    providers: int
    beneficiaries: int
    checks: list[ValidationCheckSchema]
    schema_fields: list[SchemaFieldSchema] = Field(default_factory=list, alias="schema")


class DatasetMeta(BaseModel):
    filename: str
    rows: int
    columns: int
    providers: int
    beneficiaries: int


class RiskSummary(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class UploadAnalysisResponse(BaseModel):
    run_id: str
    dataset: DatasetMeta
    risk_summary: RiskSummary
    top_risky_providers: list[dict[str, Any]]
    analytics: dict[str, Any]
    status: str = "completed"
