from __future__ import annotations

from pathlib import Path
from services.provider_export_service import ProviderExportService, INFERENCE_COLUMNS, TRAINING_COLUMNS


def test_provider_export_for_inference():
    export_svc = ProviderExportService()
    res = export_svc.export_for_inference()

    assert res["status"] == "success"
    assert res["purpose"] == "inference"
    assert res["columns"] == 31
    assert "PotentialFraud" not in res["column_list"]
    assert Path(res["file"]).is_file()


def test_provider_export_for_training():
    export_svc = ProviderExportService()
    res = export_svc.export_for_training()

    assert res["status"] == "success"
    assert res["purpose"] == "training"
    assert res["columns"] == 32
    assert "PotentialFraud" in res["column_list"]
    assert Path(res["file"]).is_file()


def test_provider_export_endpoint(client):
    response = client.post(
        "/api/v1/providers/export",
        json={"purpose": "training"},
    )
    assert response.status_code == 200
    res = response.get_json()
    assert res["status"] == "success"
    assert res["purpose"] == "training"
    assert res["columns"] == 32
