from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from models.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)

    total_rows = Column(Integer, default=0)
    total_columns = Column(Integer, default=0)

    total_providers = Column(Integer, default=0)
    total_claims = Column(Integer, default=0)
    total_beneficiaries = Column(Integer, default=0)

    low_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)

    total_reimbursement = Column(Float, default=0.0)

    status = Column(String(32), default="completed")

    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, default=utc_now)

    # Relationships
    providers = relationship("Provider", back_populates="analysis_run", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="analysis_run", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="analysis_run", cascade="all, delete-orphan")
