from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict, AliasChoices


class PredictionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    provider_id: str = Field(
        ...,
        validation_alias=AliasChoices("provider_id", "Provider"),
        min_length=1,
    )


class RiskFactorSchema(BaseModel):
    name: str
    provider_value: float | None = None
    benchmark: float | None = None
    difference_percent: float | None = None
    impact: str = "MEDIUM"
    severity: str = "MEDIUM"
    explanation: str


class RiskDetails(BaseModel):
    score: float
    probability: float
    level: str  # Low, Medium, High, Critical
    decision: str  # NORMAL, MONITOR, REVIEW, URGENT_REVIEW


class ModelInfo(BaseModel):
    type: str = "dummy"
    version: str = "1.0"


class NormalizedPredictionResponse(BaseModel):
    provider_id: str
    provider_name: str | None = None
    risk_score: float
    risk_probability: float
    risk_level: str
    decision: str
    model_type: str = "dummy"
    model_version: str = "1.0"
    risk: RiskDetails | None = None
    model: ModelInfo | None = None
    risk_factors: list[RiskFactorSchema] = []

    # Backward compatibility with existing frontend expectations:
    fraud_probability: float | None = None
    threshold: float | None = 0.5


# Alias for legacy compatibility
PredictionResponse = NormalizedPredictionResponse