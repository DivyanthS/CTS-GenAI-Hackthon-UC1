from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.database import Base


class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessments.id"), nullable=False, index=True)

    factor_name = Column(String(128), nullable=False)
    factor_value = Column(Float, nullable=True)
    benchmark_value = Column(Float, nullable=True)
    difference_percent = Column(Float, nullable=True)

    impact = Column(String(32), default="MEDIUM")  # HIGH, MEDIUM, LOW
    severity = Column(String(32), default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW

    explanation = Column(Text, nullable=False)

    # Relationships
    risk_assessment = relationship("RiskAssessment", back_populates="risk_factors")
