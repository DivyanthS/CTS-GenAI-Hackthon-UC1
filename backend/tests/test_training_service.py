from __future__ import annotations

import time
from services.model.training_service import ModelTrainingService
from services.provider_export_service import ProviderExportService


def test_model_training_service():
    export_svc = ProviderExportService()
    train_export = export_svc.export_for_training()

    training_svc = ModelTrainingService()
    res = training_svc.trigger_training_job(training_csv_path=train_export["file"])

    assert res["status"] == "QUEUED"
    job_id = res["job_id"]

    # Poll until job completes (typically < 3 seconds)
    max_wait = 15
    start = time.time()
    final_status = "QUEUED"
    while time.time() - start < max_wait:
        job = training_svc.get_job_status(job_id)
        final_status = job["status"]
        if final_status in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(0.3)

    assert final_status == "SUCCEEDED"
    assert "metrics" in job
    assert job["metrics"]["roc_auc"] >= 0.50


def test_model_status_endpoint(client):
    res = client.get("/api/v1/model/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "active_version" in data
    assert "feature_count" in data
    assert data["feature_count"] == 30


def test_model_train_endpoint(client):
    res = client.post("/api/v1/model/train", json={})
    assert res.status_code == 202
    data = res.get_json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"

    job_id = data["job_id"]
    status_res = client.get(f"/api/v1/model/train/{job_id}")
    assert status_res.status_code == 200
    assert status_res.get_json()["job_id"] == job_id
