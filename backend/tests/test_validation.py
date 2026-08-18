from __future__ import annotations

import io
from tests.conftest import SAMPLE_CSV_DATA


def test_validate_valid_csv(client):
    data = {
        "file": (io.BytesIO(SAMPLE_CSV_DATA.encode("utf-8")), "valid_test.csv")
    }
    response = client.post(
        "/api/v1/validate",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    res = response.get_json()
    assert res["valid"] is True
    assert res["health_score"] >= 80
    assert res["rows"] == 10
    assert res["providers"] == 5
    assert len(res["checks"]) > 0
    assert len(res["schema"]) > 0


def test_validate_missing_file(client):
    response = client.post(
        "/api/v1/validate",
        data={},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    res = response.get_json()
    assert res["error"] == "FILE_REQUIRED"


def test_validate_empty_file(client):
    data = {
        "file": (io.BytesIO(b""), "empty.csv")
    }
    response = client.post(
        "/api/v1/validate",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    res = response.get_json()
    assert res["valid"] is False
    assert res["health_score"] == 0


def test_validate_invalid_file_extension(client):
    data = {
        "file": (io.BytesIO(b"hello world"), "data.txt")
    }
    response = client.post(
        "/api/v1/validate",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    res = response.get_json()
    assert res["error"] == "INVALID_FILE_TYPE"
