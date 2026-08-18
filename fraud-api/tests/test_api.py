"""
tests/test_api.py

Flask test-client integration tests for all API endpoints.

Run with:
    pytest tests/test_api.py -v
"""

import io
import json

import pandas as pd
import pytest

from app import app


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _make_minimal_csv(n_claims: int = 3, provider: str = "PROV001") -> bytes:
    """
    Build a minimal valid claims CSV with the 25 required raw columns.
    All providers are identical for simplicity.
    """
    rows = []
    for i in range(n_claims):
        rows.append(
            {
                "Provider": provider,
                "BeneID": f"BENE{i:03d}",
                "ClaimID": f"CLM{i:03d}",
                "InscClaimAmtReimbursed": 5000.0 + i * 1000,
                "DeductibleAmtPaid": 200.0,
                "AttendingPhysician": "DOC001",
                "OperatingPhysician": "DOC002",
                "OtherPhysician": "DOC003",
                "ClaimType": "Inpatient" if i % 2 == 0 else "Outpatient",
                "Age": 70 + i,
                "ChronicConditionCount": 3,
                "NoOfMonths_PartACov": 12,
                "NoOfMonths_PartBCov": 12,
                "ChronicCond_Alzheimer": 0,
                "ChronicCond_Heartfailure": 1,
                "ChronicCond_KidneyDisease": 0,
                "ChronicCond_Cancer": 0,
                "ChronicCond_ObstrPulmonary": 1,
                "ChronicCond_Depression": 0,
                "ChronicCond_Diabetes": 1,
                "ChronicCond_IschemicHeart": 0,
                "ChronicCond_Osteoporasis": 0,
                "ChronicCond_rheumatoidarthritis": 0,
                "ChronicCond_stroke": 0,
                # PotentialFraud is NOT required for inference
            }
        )
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


def _upload(client, csv_bytes: bytes, filename: str = "test.csv"):
    return client.post(
        "/predict",
        data={"file": (io.BytesIO(csv_bytes), filename)},
        content_type="multipart/form-data",
    )


# ------------------------------------------------------------------ #
# GET /health
# ------------------------------------------------------------------ #

class TestHealth:
    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_response_shape(self, client):
        data = resp = client.get("/health").get_json()
        assert data["status"] == "healthy"
        assert "model_version" in data
        assert "threshold" in data
        assert "thresholds" in data

    def test_threshold_is_023(self, client):
        data = client.get("/health").get_json()
        assert data["threshold"] == pytest.approx(0.23)


# ------------------------------------------------------------------ #
# GET /model-info
# ------------------------------------------------------------------ #

class TestModelInfo:
    def test_returns_200(self, client):
        resp = client.get("/model-info")
        assert resp.status_code == 200

    def test_has_performance_metrics(self, client):
        data = client.get("/model-info").get_json()
        perf = data.get("performance", {})
        assert "roc_auc" in perf
        assert perf["roc_auc"] == pytest.approx(0.9575, abs=0.001)

    def test_has_30_features(self, client):
        data = client.get("/model-info").get_json()
        assert data["n_features"] == 30
        assert len(data["features"]) == 30


# ------------------------------------------------------------------ #
# POST /predict — happy path
# ------------------------------------------------------------------ #

class TestPredictSuccess:
    def test_returns_200_with_valid_csv(self, client):
        resp = _upload(client, _make_minimal_csv())
        assert resp.status_code == 200

    def test_response_envelope(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        assert data["status"] == "success"
        assert "model_version" in data
        assert "threshold" in data
        assert "n_providers" in data
        assert "providers" in data

    def test_returns_one_provider(self, client):
        data = _upload(client, _make_minimal_csv(provider="PROV001")).get_json()
        assert data["n_providers"] == 1

    def test_provider_result_shape(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        provider = data["providers"][0]
        assert "provider_id" in provider
        assert "fraud_probability" in provider
        assert "risk_level" in provider
        assert "decision" in provider
        assert "explanation" in provider
        assert "top_factors" in provider

    def test_fraud_probability_in_range(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        prob = data["providers"][0]["fraud_probability"]
        assert 0.0 <= prob <= 1.0

    def test_risk_level_valid_values(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        assert data["providers"][0]["risk_level"] in {"LOW", "MEDIUM", "HIGH"}

    def test_decision_valid_values(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        assert data["providers"][0]["decision"] in {
            "NOT_FLAGGED", "FLAGGED_FOR_REVIEW", "FLAGGED"
        }

    def test_explanation_is_string_and_not_empty(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        explanation = data["providers"][0]["explanation"]
        assert isinstance(explanation, str)
        assert len(explanation) > 20

    def test_top_factors_structure(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        factors = data["providers"][0]["top_factors"]
        assert isinstance(factors, list)
        assert len(factors) > 0
        for factor in factors:
            assert "feature" in factor
            assert "value" in factor
            assert "shap_value" in factor
            assert factor["direction"] in {"increases_risk", "decreases_risk"}

    def test_multiple_providers(self, client):
        csv_p1 = _make_minimal_csv(provider="PROV001")
        csv_p2 = _make_minimal_csv(provider="PROV002")
        df1 = pd.read_csv(io.StringIO(csv_p1.decode()))
        df2 = pd.read_csv(io.StringIO(csv_p2.decode()))
        combined = pd.concat([df1, df2], ignore_index=True)
        csv_bytes = combined.to_csv(index=False).encode()

        data = _upload(client, csv_bytes).get_json()
        assert data["n_providers"] == 2
        provider_ids = {p["provider_id"] for p in data["providers"]}
        assert provider_ids == {"PROV001", "PROV002"}

    def test_threshold_in_response_matches_config(self, client):
        data = _upload(client, _make_minimal_csv()).get_json()
        assert data["threshold"] == pytest.approx(0.23)

    def test_csv_with_potentialfraud_column_accepted(self, client):
        """Training CSVs that include PotentialFraud should still be accepted."""
        csv_bytes = _make_minimal_csv()
        df = pd.read_csv(io.StringIO(csv_bytes.decode()))
        df["PotentialFraud"] = "No"
        csv_bytes = df.to_csv(index=False).encode()
        resp = _upload(client, csv_bytes)
        assert resp.status_code == 200


# ------------------------------------------------------------------ #
# POST /predict — error cases
# ------------------------------------------------------------------ #

class TestPredictErrors:
    def test_no_file_returns_400(self, client):
        resp = client.post("/predict")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["error_type"] == "MISSING_FILE"

    def test_empty_file_returns_400(self, client):
        resp = _upload(client, b"")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error_type"] == "EMPTY_FILE"

    def test_non_csv_returns_400(self, client):
        resp = _upload(client, b"fake content", filename="model.pkl")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error_type"] == "INVALID_FILE_TYPE"

    def test_malformed_csv_returns_400(self, client):
        # CSV with inconsistent columns (not parseable properly)
        garbage = b"col1,col2\n1,2,3,4,5\n,,,,\n"
        # This may parse but fail column validation
        resp = _upload(client, garbage)
        data = resp.get_json()
        assert resp.status_code in (400, 500)
        assert data["status"] == "error"

    def test_missing_required_columns_returns_400(self, client):
        df = pd.DataFrame({"Provider": ["P001"], "BeneID": ["B001"]})
        csv_bytes = df.to_csv(index=False).encode()
        resp = _upload(client, csv_bytes)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error_type"] == "PREPROCESSING_ERROR"

    def test_csv_with_no_valid_providers_returns_400(self, client):
        """All rows missing Provider → validation should fail."""
        df = pd.read_csv(io.StringIO(_make_minimal_csv().decode()))
        df["Provider"] = None
        csv_bytes = df.to_csv(index=False).encode()
        resp = _upload(client, csv_bytes)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"

    def test_header_only_csv_returns_400(self, client):
        """CSV with headers but zero data rows."""
        df = pd.read_csv(io.StringIO(_make_minimal_csv().decode()))
        header_only = df.iloc[0:0].to_csv(index=False).encode()
        resp = _upload(client, header_only)
        assert resp.status_code == 400

    def test_error_response_has_no_stack_trace(self, client):
        resp = client.post("/predict")
        body = resp.get_data(as_text=True)
        assert "Traceback" not in body
        assert "/app/" not in body


# ------------------------------------------------------------------ #
# 404 and method-not-allowed
# ------------------------------------------------------------------ #

class TestRouting:
    def test_unknown_route_returns_404(self, client):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404

    def test_get_on_predict_returns_405(self, client):
        resp = client.get("/predict")
        assert resp.status_code == 405
