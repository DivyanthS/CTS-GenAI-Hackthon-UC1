from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from models.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(64), nullable=False, index=True)
    provider_id = Column(String(64), ForeignKey("providers.provider_id"), nullable=False, index=True)
    analysis_run_id = Column(String(64), ForeignKey("analysis_runs.run_id"), nullable=True, index=True)

    beneficiary_id = Column(String(64), nullable=True, index=True)
    claim_type = Column(String(32), default="Outpatient")  # Inpatient, Outpatient

    claim_start_date = Column(String(64), nullable=True)
    claim_end_date = Column(String(64), nullable=True)

    reimbursement_amount = Column(Float, default=0.0)
    deductible_amount = Column(Float, default=0.0)

    attending_physician = Column(String(64), nullable=True)
    operating_physician = Column(String(64), nullable=True)
    other_physician = Column(String(64), nullable=True)

    potential_fraud = Column(String(32), nullable=True)

    # Preserve original row data as JSON
    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="claims")
    provider = relationship("Provider", back_populates="claims", foreign_keys=[provider_id], primaryjoin="Claim.provider_id==Provider.provider_id")
