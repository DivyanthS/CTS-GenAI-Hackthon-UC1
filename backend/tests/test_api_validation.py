from __future__ import annotations


def test_predict_endpoint_validation_empty_id(client):
    res = client.post("/api/v1/predict", json={"provider_id": ""})
    assert res.status_code == 400
    assert res.get_json()["error"] == "VALIDATION_ERROR"


def test_predict_endpoint_missing_json(client):
    res = client.post("/api/v1/predict", data="not json", content_type="text/plain")
    assert res.status_code in (400, 415)


def test_provider_detail_nonexistent_id(client):
    res = client.get("/api/v1/providers/NON_EXISTENT_ID_XYZ")
    assert res.status_code == 404
    assert res.get_json()["error"] == "PROVIDER_NOT_FOUND"


def test_claim_detail_nonexistent_id(client):
    res = client.get("/api/v1/claims/NON_EXISTENT_CLAIM_XYZ")
    assert res.status_code == 404
    assert res.get_json()["error"] == "CLAIM_NOT_FOUND"


def test_claim_explanation_nonexistent_id(client):
    res = client.get("/api/v1/claims/NON_EXISTENT_CLAIM_XYZ/explanation")
    assert res.status_code == 404
    assert res.get_json()["error"] == "CLAIM_NOT_FOUND"


def test_run_detail_nonexistent_id(client):
    res = client.get("/api/v1/runs/RUN-NONEXISTENT-999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "RUN_NOT_FOUND"


def test_report_json_nonexistent_id(client):
    res = client.get("/api/v1/reports/RUN-NONEXISTENT-999/json")
    assert res.status_code == 404
    assert res.get_json()["error"] == "RUN_NOT_FOUND"


def test_report_pdf_nonexistent_id(client):
    res = client.get("/api/v1/reports/RUN-NONEXISTENT-999/pdf")
    assert res.status_code == 404
    assert res.get_json()["error"] == "RUN_NOT_FOUND"


def test_training_job_nonexistent_id(client):
    res = client.get("/api/v1/model/train/JOB-NONEXISTENT-999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "JOB_NOT_FOUND"


def test_update_threshold_invalid_bounds(client):
    res = client.put(
        "/api/v1/model/threshold",
        json={"low_threshold": 0.85, "high_threshold": 0.30},
    )
    assert res.status_code == 400
    assert res.get_json()["error"] == "INVALID_THRESHOLDS"


def test_providers_invalid_pagination(client):
    res = client.get("/api/v1/providers?page=-1")
    assert res.status_code == 400
    assert res.get_json()["error"] == "INVALID_PAGINATION"

    res_size = client.get("/api/v1/providers?page_size=1000")
    assert res_size.status_code == 400
    assert res_size.get_json()["error"] == "INVALID_PAGINATION"
