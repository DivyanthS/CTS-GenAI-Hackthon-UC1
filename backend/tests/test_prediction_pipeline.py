from __future__ import annotations

from models.database import get_db
from models.provider import Provider
from models.risk_assessment import RiskAssessment
from services.risk.dummy_risk_engine import DummyRiskEngine
from services.prediction.prediction_service import PredictionService


def test_prediction_service_database_persistence():
    # Insert test provider into DB
    with get_db() as db:
        prov = Provider(
            provider_id="PRV_PRED_TEST_1",
            potential_fraud=1,
            total_claims=80,
            unique_beneficiaries=30,
            total_reimbursement=240000.0,
            average_reimbursement=3000.0,
            inpatient_share=0.55,
        )
        db.add(prov)
        db.flush()

    engine = DummyRiskEngine()
    pred_svc = PredictionService(risk_engine=engine)
    res = pred_svc.predict("PRV_PRED_TEST_1")

    assert res["provider_id"] == "PRV_PRED_TEST_1"
    assert 0.0 <= res["risk_score"] <= 100.0
    assert 0.0 <= res["risk_probability"] <= 1.0
    assert res["risk_level"] in ("Low", "Medium", "High", "Critical")
    assert res["decision"] in ("NORMAL", "MONITOR", "REVIEW", "URGENT_REVIEW")

    # Verify RiskAssessment stored in DB
    with get_db() as db:
        saved_ra = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.provider_id == "PRV_PRED_TEST_1")
            .first()
        )
        assert saved_ra is not None
        assert saved_ra.risk_level == res["risk_level"]
        assert saved_ra.decision == res["decision"]

        # Clean up
        db.delete(saved_ra)
        p_to_del = db.query(Provider).filter(Provider.provider_id == "PRV_PRED_TEST_1").first()
        if p_to_del:
            db.delete(p_to_del)
