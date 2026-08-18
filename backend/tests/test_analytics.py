from __future__ import annotations


def test_get_analytics_summary(client):
    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    res = response.get_json()
    assert res["total_claims"] >= 10
    assert res["total_providers"] >= 5
    assert res["total_reimbursement"] > 0
    assert res["average_claim_reimbursement"] > 0
    assert "low_risk" in res
    assert "medium_risk" in res
    assert "high_risk" in res
    assert "critical_risk" in res
    # Legacy fields
    assert "fraud_flagged" in res
    assert "not_flagged" in res


def test_get_analytics_charts(client):
    response = client.get("/api/v1/analytics/charts")
    assert response.status_code == 200
    res = response.get_json()
    assert "risk_distribution" in res
    assert "reimbursement_by_risk" in res
    assert "claims_by_type" in res
    assert "top_risky_providers" in res
    assert len(res["risk_distribution"]) == 4
