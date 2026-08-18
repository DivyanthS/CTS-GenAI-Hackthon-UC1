from __future__ import annotations

import io
import math
from utils.json_utils import make_json_safe


def test_json_safe_no_nan_or_inf():
    payload = {
        "score": float("nan"),
        "ratio": float("inf"),
        "neg_ratio": float("-inf"),
        "list": [1.0, float("nan"), {"nested": float("inf")}],
    }
    safe_payload = make_json_safe(payload)

    assert safe_payload["score"] is None
    assert safe_payload["ratio"] is None
    assert safe_payload["neg_ratio"] is None
    assert safe_payload["list"][1] is None
    assert safe_payload["list"][2]["nested"] is None


def test_health_no_credentials_exposed(client):
    res = client.get("/health")
    data = res.get_json()

    # Verify no secret passwords or tokens are in response
    serialized = str(data).lower()
    assert "password" not in serialized
    assert "secret" not in serialized
    assert "key" not in serialized or "risk_engine" in serialized


def test_export_security_path_traversal(client):
    # Attempt path traversal in filename or parameters
    res = client.post(
        "/api/v1/providers/export",
        json={"purpose": "training"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert ".." not in data["filename"]
