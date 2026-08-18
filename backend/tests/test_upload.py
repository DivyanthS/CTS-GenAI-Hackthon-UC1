from __future__ import annotations

import io
from tests.conftest import SAMPLE_CSV_DATA


def test_upload_csv_success(client):
    data = {
        "file": (io.BytesIO(SAMPLE_CSV_DATA.encode("utf-8")), "upload_success.csv")
    }
    response = client.post(
        "/api/v1/analyze/csv",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    res = response.get_json()
    assert "run_id" in res
    assert res["status"] == "completed"
    assert res["dataset"]["rows"] == 10
    assert res["dataset"]["providers"] == 5
    assert "risk_summary" in res
    assert isinstance(res["top_risky_providers"], list)
    assert "analytics" in res


def test_upload_empty_csv(client):
    data = {
        "file": (io.BytesIO(b""), "empty.csv")
    }
    response = client.post(
        "/api/v1/analyze/csv",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    res = response.get_json()
    assert res["error"] == "ANALYSIS_VALIDATION_ERROR"


def test_upload_missing_file_field(client):
    response = client.post(
        "/api/v1/analyze/csv",
        data={},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    res = response.get_json()
    assert res["error"] == "FILE_REQUIRED"
