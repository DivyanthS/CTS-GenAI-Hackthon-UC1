from __future__ import annotations

import pandas as pd
from services.risk.dummy_risk_engine import DummyRiskEngine
from services.feature_engineering.provider_features import build_provider_features
import io
from tests.conftest import SAMPLE_CSV_DATA


def test_dummy_risk_engine_batch():
    df = pd.read_csv(io.BytesIO(SAMPLE_CSV_DATA.encode("utf-8")))
    features = build_provider_features(df)

    engine = DummyRiskEngine()
    results = engine.predict_batch(features, df)

    assert len(results) == 5
    assert (results["risk_score"] >= 0.0).all()
    assert (results["risk_score"] <= 100.0).all()
    assert (results["risk_probability"] >= 0.0).all()
    assert (results["risk_probability"] <= 1.0).all()
    assert results["risk_level"].isin(["Low", "Medium", "High", "Critical"]).all()
    assert results["decision"].isin(["NORMAL", "MONITOR", "REVIEW", "URGENT_REVIEW"]).all()


def test_dummy_risk_engine_deterministic():
    df = pd.read_csv(io.BytesIO(SAMPLE_CSV_DATA.encode("utf-8")))
    features = build_provider_features(df)

    engine1 = DummyRiskEngine()
    engine2 = DummyRiskEngine()

    res1 = engine1.predict_batch(features, df)
    res2 = engine2.predict_batch(features, df)

    pd.testing.assert_series_equal(res1["risk_score"], res2["risk_score"])
    pd.testing.assert_series_equal(res1["risk_probability"], res2["risk_probability"])


def test_single_provider_prediction():
    engine = DummyRiskEngine()
    features = {
        "Provider": "PRV9999",
        "TotalClaims": 150,
        "AverageReimbursement": 8500.0,
        "TotalReimbursement": 1275000.0,
        "InpatientShare": 0.65,
        "ClaimsPerBeneficiary": 3.2,
    }
    result = engine.predict_provider(features)
    assert result["provider_id"] == "PRV9999"
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["risk_level"] in ["Low", "Medium", "High", "Critical"]
    assert result["decision"] in ["NORMAL", "MONITOR", "REVIEW", "URGENT_REVIEW"]
    assert isinstance(result["risk_factors"], list)
