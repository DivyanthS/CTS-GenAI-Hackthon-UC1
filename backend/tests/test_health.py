from __future__ import annotations


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "fraud-detection-backend"
    assert data["database"] == "connected"
    assert data["risk_engine"] in ["dummy", "xgboost"]
    assert "version" in data
