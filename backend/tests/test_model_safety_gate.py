from __future__ import annotations

import time
from unittest.mock import MagicMock
from services.model.training_service import ModelTrainingService
from services.kaggle.kaggle_service import KaggleService
from services.provider_export_service import ProviderExportService


def test_model_training_safety_gate_success():
    export_svc = ProviderExportService()
    train_export = export_svc.export_for_training()

    # Mock Kaggle Service to simulate safe external execution
    mock_kaggle = MagicMock(spec=KaggleService)
    mock_kaggle.is_configured = True
    mock_kaggle.upload_dataset.return_value = {"status": "success"}
    mock_kaggle.trigger_kernel.return_value = {"status": "success"}

    training_svc = ModelTrainingService(kaggle_service=mock_kaggle)
    res = training_svc.trigger_training_job(training_csv_path=train_export["file"])
    job_id = res["job_id"]

    # Poll until job completes
    for _ in range(30):
        job = training_svc.get_job_status(job_id)
        if job["status"] in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(0.2)

    assert job["status"] == "SUCCEEDED"
    assert "metrics" in job
    assert job["metrics"]["roc_auc"] >= 0.50
    assert job["promoted_version"] is not None
    mock_kaggle.upload_dataset.assert_called_once()
    mock_kaggle.trigger_kernel.assert_called_once()
