from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Provider(Base):
    """
    ORM model for provider_data_aggregated.csv

    Dataset:
        5,410 rows
        32 columns

    Dataset columns are represented directly in this model.
    Risk/prediction fields are kept separately so model-generated
    results can be stored without modifying the original dataset fields.
    """

    __tablename__ = "providers"

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # DATASET COLUMNS
    # ------------------------------------------------------------------

    # Provider identifier
    provider_id = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Ground-truth / dataset fraud label
    # 0 = No potential fraud
    # 1 = Potential fraud
    potential_fraud = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    # ------------------------------------------------------------------
    # CLAIM STATISTICS
    # ------------------------------------------------------------------

    total_claims = Column(
        Integer,
        nullable=False,
        default=0,
    )

    unique_beneficiaries = Column(
        Integer,
        nullable=False,
        default=0,
    )

    total_reimbursement = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    average_reimbursement = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    max_reimbursement = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    std_reimbursement = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # DEDUCTIBLE STATISTICS
    # ------------------------------------------------------------------

    total_deductible_paid = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    average_deductible_paid = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # PHYSICIAN STATISTICS
    # ------------------------------------------------------------------

    unique_attending_physicians = Column(
        Integer,
        nullable=False,
        default=0,
    )

    unique_operating_physicians = Column(
        Integer,
        nullable=False,
        default=0,
    )

    unique_other_physicians = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ------------------------------------------------------------------
    # CLAIM / BENEFICIARY RATIOS
    # ------------------------------------------------------------------

    claims_per_beneficiary = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    inpatient_share = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # NOTE:
    # outpatient_share is NOT present in the dataset.
    # It can be derived as:
    #
    #     outpatient_share = 1 - inpatient_share
    #
    # Therefore it is intentionally NOT stored as a dataset column.

    # ------------------------------------------------------------------
    # PATIENT CHARACTERISTICS
    # ------------------------------------------------------------------

    average_patient_age = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    average_chronic_condition_count = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # COVERAGE
    # ------------------------------------------------------------------

    average_part_a_coverage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    average_part_b_coverage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # CHRONIC CONDITION FEATURES
    # ------------------------------------------------------------------

    chronic_cond_alzheimer = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_heartfailure = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_kidney_disease = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_cancer = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_obstr_pulmonary = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_depression = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_diabetes = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_ischemic_heart = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_osteoporasis = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_rheumatoidarthritis = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    chronic_cond_stroke = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # MISSING-VALUE INDICATORS
    # ------------------------------------------------------------------

    average_deductible_paid_missing = Column(
        Integer,
        nullable=False,
        default=0,
    )

    std_reimbursement_missing = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ------------------------------------------------------------------
    # ANALYSIS RUN
    # ------------------------------------------------------------------
    #
    # This is NOT part of the CSV dataset.
    # It identifies which upload/analysis produced this provider record.

    analysis_run_id = Column(
        String(64),
        ForeignKey("analysis_runs.run_id"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # MODEL / RISK OUTPUT
    # ------------------------------------------------------------------
    #
    # These are NOT source-dataset columns.
    # They store the output generated by the fraud detection model.

    risk_score = Column(
        Float,
        nullable=True,
    )

    risk_probability = Column(
        Float,
        nullable=True,
    )

    risk_level = Column(
        String(32),
        nullable=True,
    )

    risk_status = Column(
        String(32),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------------------

    created_at = Column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------------------------

    analysis_run = relationship(
        "AnalysisRun",
        back_populates="providers",
    )

    risk_assessments = relationship(
        "RiskAssessment",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    claims = relationship(
        "Claim",
        back_populates="provider",
    )

    @property
    def outpatient_share(self) -> float:
        """Derive outpatient share on the fly: 1.0 - inpatient_share."""
        return round(max(0.0, 1.0 - float(self.inpatient_share or 0.0)), 4)

    @property
    def provider_name(self) -> str:
        """Derive deterministic provider name on the fly."""
        from utils.risk_utils import generate_provider_name
        return generate_provider_name(self.provider_id)