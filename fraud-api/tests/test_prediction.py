"""
tests/test_prediction.py

Model compatibility tests.

These tests verify that the deployed model produces probabilities that
are consistent with what the Kaggle notebook trained model would produce
when given the same engineered features.

Tests in this file load the actual model — they require the model artifact
to be present at models/v1/model.joblib.

Run with:
    pytest tests/test_prediction.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.feature_engineering import FEATURES
from src.predictor import MODEL, THRESHOLD, predict_single_provider, predict_batch
from src.risk import classify


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _make_feature_row(**overrides) -> pd.DataFrame:
    """
    Build a single-row DataFrame with the 30 model features.
    Defaults represent a low-risk provider profile.
    """
    defaults = {
        "TotalClaims": 50,
        "UniqueBeneficiaries": 40,
        "TotalReimbursement": 150_000.0,
        "AverageReimbursement": 3_000.0,
        "MaxReimbursement": 10_000.0,
        "StdReimbursement": 2_000.0,
        "TotalDeductiblePaid": 5_000.0,
        "AverageDeductiblePaid": 100.0,
        "UniqueAttendingPhysicians": 5,
        "UniqueOperatingPhysicians": 3,
        "UniqueOtherPhysicians": 2,
        "ClaimsPerBeneficiary": 1.25,
        "InpatientShare": 0.1,
        "AveragePatientAge": 72.0,
        "AverageChronicConditionCount": 3.5,
        "AveragePartACoverage": 11.5,
        "AveragePartBCoverage": 11.5,
        "ChronicCond_Alzheimer": 0.1,
        "ChronicCond_Heartfailure": 0.15,
        "ChronicCond_KidneyDisease": 0.2,
        "ChronicCond_Cancer": 0.05,
        "ChronicCond_ObstrPulmonary": 0.1,
        "ChronicCond_Depression": 0.2,
        "ChronicCond_Diabetes": 0.35,
        "ChronicCond_IschemicHeart": 0.25,
        "ChronicCond_Osteoporasis": 0.1,
        "ChronicCond_rheumatoidarthritis": 0.08,
        "ChronicCond_stroke": 0.05,
        "AverageDeductiblePaid_Missing": 0,
        "StdReimbursement_Missing": 0,
    }
    defaults.update(overrides)
    return pd.DataFrame([defaults])


# ------------------------------------------------------------------ #
# Model loading sanity checks
# ------------------------------------------------------------------ #

class TestModelLoading:
    def test_model_loaded(self):
        assert MODEL is not None

    def test_threshold_is_locked(self):
        assert THRESHOLD == pytest.approx(0.23)

    def test_model_has_30_features(self):
        # XGBoost booster knows how many features it was trained on
        assert MODEL.n_features_in_ == 30


# ------------------------------------------------------------------ #
# Prediction correctness
# ------------------------------------------------------------------ #

class TestPrediction:
    def test_probability_in_range(self):
        row = _make_feature_row()
        prob = predict_single_provider(row)
        assert 0.0 <= prob <= 1.0

    def test_high_risk_profile_above_threshold(self):
        """
        A provider with extreme values (very high reimbursement, many claims,
        high inpatient share) should receive a probability above threshold.
        """
        row = _make_feature_row(
            TotalClaims=5000,
            TotalReimbursement=10_000_000.0,
            AverageReimbursement=2_000.0,
            MaxReimbursement=50_000.0,
            InpatientShare=0.9,
            ClaimsPerBeneficiary=8.0,
            UniqueAttendingPhysicians=2,
        )
        prob = predict_single_provider(row)
        assert prob >= THRESHOLD, (
            f"Expected high-risk profile to be ≥ {THRESHOLD}, got {prob:.4f}"
        )

    def test_low_risk_profile_below_threshold(self):
        """
        A provider with modest, typical Medicare values should be below threshold.
        """
        row = _make_feature_row(
            TotalClaims=30,
            TotalReimbursement=50_000.0,
            AverageReimbursement=1_667.0,
            InpatientShare=0.05,
            ClaimsPerBeneficiary=1.0,
        )
        prob = predict_single_provider(row)
        assert prob < THRESHOLD, (
            f"Expected low-risk profile to be < {THRESHOLD}, got {prob:.4f}"
        )

    def test_prediction_deterministic(self):
        """The same input should always produce the same probability."""
        row = _make_feature_row()
        prob1 = predict_single_provider(row)
        prob2 = predict_single_provider(row)
        assert prob1 == pytest.approx(prob2, abs=1e-9)

    def test_batch_matches_single(self):
        """Batch prediction must equal single-row prediction for each row."""
        row1 = _make_feature_row(TotalClaims=100, TotalReimbursement=300_000.0)
        row2 = _make_feature_row(TotalClaims=20, TotalReimbursement=40_000.0)

        prob1_single = predict_single_provider(row1)
        prob2_single = predict_single_provider(row2)

        batch_df = pd.concat([row1, row2], ignore_index=True)
        batch_probs = predict_batch(batch_df)

        assert batch_probs[0] == pytest.approx(prob1_single, abs=1e-9)
        assert batch_probs[1] == pytest.approx(prob2_single, abs=1e-9)


# ------------------------------------------------------------------ #
# Risk banding
# ------------------------------------------------------------------ #

class TestRiskBanding:
    def test_probability_below_threshold_is_low(self):
        result = classify(0.10)
        assert result["risk_level"] == "LOW"
        assert result["decision"] == "NOT_FLAGGED"

    def test_probability_at_threshold_is_medium(self):
        result = classify(0.23)
        assert result["risk_level"] == "MEDIUM"
        assert result["decision"] == "FLAGGED_FOR_REVIEW"

    def test_probability_above_medium_max_is_high(self):
        result = classify(0.75)
        assert result["risk_level"] == "HIGH"
        assert result["decision"] == "FLAGGED"

    def test_boundary_exactly_at_medium_max(self):
        result = classify(0.60)
        assert result["risk_level"] == "HIGH"
        assert result["decision"] == "FLAGGED"


# ------------------------------------------------------------------ #
# Input validation
# ------------------------------------------------------------------ #

class TestPredictionInputValidation:
    def test_raises_on_missing_feature(self):
        from src.predictor import PredictionError

        row = _make_feature_row()
        row = row.drop(columns=["TotalClaims"])
        with pytest.raises(PredictionError, match="Missing model features"):
            predict_single_provider(row)

    def test_raises_on_nan_feature(self):
        from src.predictor import PredictionError

        row = _make_feature_row()
        row["TotalReimbursement"] = float("nan")
        with pytest.raises(PredictionError, match="NaN values"):
            predict_single_provider(row)
