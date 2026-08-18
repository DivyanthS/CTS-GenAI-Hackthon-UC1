from __future__ import annotations


def test_get_runs(client):
    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    res = response.get_json()
    assert "runs" in res
    assert res["total"] >= 1
    run_id = res["runs"][0]["run_id"]

    # Test single run
    run_resp = client.get(f"/api/v1/runs/{run_id}")
    assert run_resp.status_code == 200


def test_get_report_json(client):
    runs_resp = client.get("/api/v1/runs")
    run_id = runs_resp.get_json()["runs"][0]["run_id"]

    response = client.get(f"/api/v1/reports/{run_id}/json")
    assert response.status_code == 200
    res = response.get_json()
    assert "run_id" in res
    assert "executive_summary" in res
    assert "dataset_overview" in res
    assert "risk_distribution" in res
    assert "key_risk_factors" in res
    assert "methodology_disclaimer" in res


def test_get_report_pdf(client):
    runs_resp = client.get("/api/v1/runs")
    run_id = runs_resp.get_json()["runs"][0]["run_id"]

    response = client.get(f"/api/v1/reports/{run_id}/pdf")
    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert len(response.data) > 100
