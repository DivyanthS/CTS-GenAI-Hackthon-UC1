from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(64), ForeignKey("providers.provider_id"), nullable=False, index=True)
    analysis_run_id = Column(String(64), ForeignKey("analysis_runs.run_id"), nullable=True, index=True)

    risk_probability = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="Low")  # Low, Medium, High, Critical
    decision = Column(String(32), default="NORMAL")  # NORMAL, MONITOR, REVIEW, URGENT_REVIEW

    model_type = Column(String(64), default="dummy")
    model_version = Column(String(32), default="1.0")

    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="risk_assessments")
    provider = relationship("Provider", back_populates="risk_assessments", foreign_keys=[provider_id], primaryjoin="RiskAssessment.provider_id==Provider.provider_id")
    risk_factors = relationship("RiskFactor", back_populates="risk_assessment", cascade="all, delete-orphan")
