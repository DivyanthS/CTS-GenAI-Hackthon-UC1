from __future__ import annotations

from models.database import get_db
from models.provider import Provider
from models.claim import Claim
from models.risk_assessment import RiskAssessment
from models.risk_factor import RiskFactor
from models.analysis_run import AnalysisRun


def test_provider_crud_and_properties():
    with get_db() as db:
        p = Provider(
            provider_id="TEST_PRV_9999",
            potential_fraud=1,
            total_claims=100,
            unique_beneficiaries=50,
            total_reimbursement=50000.0,
            average_reimbursement=500.0,
            inpatient_share=0.35,
            chronic_cond_alzheimer=0.2,
        )
        db.add(p)
        db.flush()

        # Retrieve
        fetched = db.query(Provider).filter(Provider.provider_id == "TEST_PRV_9999").first()
        assert fetched is not None
        assert fetched.potential_fraud == 1
        assert fetched.total_claims == 100
        assert fetched.inpatient_share == 0.35
        # Verify derived properties
        assert fetched.outpatient_share == 0.65
        assert "Provider" in fetched.provider_name
        assert "9999" in fetched.provider_name

        # Clean up
        db.delete(fetched)


def test_risk_assessment_and_factors_relationship():
    with get_db() as db:
        p = Provider(
            provider_id="TEST_PRV_8888",
            total_claims=20,
            total_reimbursement=10000.0,
        )
        db.add(p)
        db.flush()

        ra = RiskAssessment(
            provider_id="TEST_PRV_8888",
            risk_score=75.5,
            risk_probability=0.755,
            risk_level="High",
            decision="REVIEW",
            model_type="XGBoost",
            model_version="1.0",
            summary="High risk signal detected.",
        )
        db.add(ra)
        db.flush()

        rf = RiskFactor(
            risk_assessment_id=ra.id,
            factor_name="Reimbursement anomaly",
            factor_value=10000.0,
            benchmark_value=5000.0,
            difference_percent=100.0,
            impact="HIGH",
            severity="HIGH",
            explanation="Reimbursement is 100% higher than peer benchmark.",
        )
        db.add(rf)
        db.flush()

        # Verify relationship lookup
        fetched_ra = db.query(RiskAssessment).filter(RiskAssessment.id == ra.id).first()
        assert fetched_ra is not None
        assert len(fetched_ra.risk_factors) == 1
        assert fetched_ra.risk_factors[0].factor_name == "Reimbursement anomaly"
        assert fetched_ra.risk_factors[0].difference_percent == 100.0

        # Cascade delete verification
        db.delete(fetched_ra)
        db.flush()
        orphaned_rf = db.query(RiskFactor).filter(RiskFactor.risk_assessment_id == ra.id).first()
        assert orphaned_rf is None

        # Clean up provider
        db.delete(p)


def test_analysis_run_relationships():
    with get_db() as db:
        run = AnalysisRun(
            run_id="RUN-TEST-001",
            filename="test_dataset.csv",
            total_rows=100,
            total_providers=10,
            total_claims=90,
            status="completed",
        )
        db.add(run)
        db.flush()

        p = Provider(
            provider_id="PRV_RUN_01",
            analysis_run_id="RUN-TEST-001",
            total_claims=10,
        )
        db.add(p)
        db.flush()

        fetched_run = db.query(AnalysisRun).filter(AnalysisRun.run_id == "RUN-TEST-001").first()
        assert fetched_run is not None
        assert len(fetched_run.providers) == 1
        assert fetched_run.providers[0].provider_id == "PRV_RUN_01"

        # Cleanup
        db.delete(fetched_run)
