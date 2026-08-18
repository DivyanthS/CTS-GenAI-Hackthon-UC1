"""
tests/test_features.py

Unit tests for src/feature_engineering.py.

These tests verify that the aggregation logic faithfully reproduces the
notebook pipeline without requiring the model to be loaded.

Run with:
    pytest tests/test_features.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.feature_engineering import (
    FEATURES,
    CHRONIC_COLUMNS,
    FeatureEngineeringError,
    create_provider_features,
)
from src.preprocessing import preprocess


# ------------------------------------------------------------------ #
# Fixtures — minimal synthetic claim data
# ------------------------------------------------------------------ #

def _make_claim_row(
    provider="PROV001",
    bene_id="BENE001",
    claim_id="CLM001",
    claim_type="Inpatient",
    reimbursement=5000.0,
    deductible=200.0,
    age=70,
    chronic_count=3,
    part_a=12,
    part_b=12,
    **kwargs,
) -> dict:
    """Build a minimal synthetic claim row with all required columns."""
    row = {
        "Provider": provider,
        "BeneID": bene_id,
        "ClaimID": claim_id,
        "ClaimType": claim_type,
        "InscClaimAmtReimbursed": reimbursement,
        "DeductibleAmtPaid": deductible,
        "AttendingPhysician": "DOC001",
        "OperatingPhysician": "DOC002",
        "OtherPhysician": "DOC003",
        "Age": age,
        "ChronicConditionCount": chronic_count,
        "NoOfMonths_PartACov": part_a,
        "NoOfMonths_PartBCov": part_b,
        # Chronic conditions — binary 0/1
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
    }
    row.update(kwargs)
    return row


def _make_df(*rows) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


# ------------------------------------------------------------------ #
# Tests: feature count and column ordering
# ------------------------------------------------------------------ #

class TestFeatureSchema:
    def test_feature_count_is_30(self):
        assert len(FEATURES) == 30

    def test_first_feature(self):
        assert FEATURES[0] == "TotalClaims"

    def test_last_two_features_are_missing_indicators(self):
        assert FEATURES[-2] == "AverageDeductiblePaid_Missing"
        assert FEATURES[-1] == "StdReimbursement_Missing"

    def test_inpatient_share_present_not_outpatient(self):
        assert "InpatientShare" in FEATURES
        assert "OutpatientShare" not in FEATURES

    def test_chronic_columns_all_present(self):
        for col in CHRONIC_COLUMNS:
            assert col in FEATURES


# ------------------------------------------------------------------ #
# Tests: aggregation correctness
# ------------------------------------------------------------------ #

class TestAggregation:
    def test_single_provider_single_claim(self):
        df = _make_df(
            _make_claim_row(
                provider="P001",
                bene_id="B001",
                claim_id="C001",
                reimbursement=10_000.0,
                deductible=500.0,
            )
        )
        df = preprocess(df)
        result = create_provider_features(df)

        assert len(result) == 1
        row = result.iloc[0]

        assert row["Provider"] == "P001"
        assert row["TotalClaims"] == 1
        assert row["UniqueBeneficiaries"] == 1
        assert row["TotalReimbursement"] == pytest.approx(10_000.0)
        assert row["AverageReimbursement"] == pytest.approx(10_000.0)
        assert row["MaxReimbursement"] == pytest.approx(10_000.0)
        assert row["ClaimsPerBeneficiary"] == pytest.approx(1.0)
        assert row["InpatientShare"] == pytest.approx(1.0)  # all inpatient

    def test_two_providers(self):
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001"),
            _make_claim_row(provider="P002", claim_id="C002"),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert len(result) == 2
        assert set(result["Provider"]) == {"P001", "P002"}

    def test_outpatient_share_not_in_output(self):
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001", claim_type="Outpatient"),
            _make_claim_row(provider="P001", claim_id="C002", claim_type="Inpatient"),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert "OutpatientShare" not in result.columns

    def test_inpatient_share_with_mixed_claims(self):
        # 1 inpatient out of 4 total → InpatientShare = 0.25
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001", claim_type="Inpatient"),
            _make_claim_row(provider="P001", claim_id="C002", claim_type="Outpatient"),
            _make_claim_row(provider="P001", claim_id="C003", claim_type="Outpatient"),
            _make_claim_row(provider="P001", claim_id="C004", claim_type="Outpatient"),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert result.iloc[0]["InpatientShare"] == pytest.approx(0.25)

    def test_claims_per_beneficiary(self):
        # 3 claims for 2 unique beneficiaries → 1.5
        df = _make_df(
            _make_claim_row(provider="P001", bene_id="B001", claim_id="C001"),
            _make_claim_row(provider="P001", bene_id="B001", claim_id="C002"),
            _make_claim_row(provider="P001", bene_id="B002", claim_id="C003"),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert result.iloc[0]["ClaimsPerBeneficiary"] == pytest.approx(1.5)

    def test_beneficiary_dedup_for_patient_features(self):
        # Same beneficiary with two claims — age should be counted only once
        df = _make_df(
            _make_claim_row(provider="P001", bene_id="B001", claim_id="C001", age=70),
            _make_claim_row(provider="P001", bene_id="B001", claim_id="C002", age=70),
            _make_claim_row(provider="P001", bene_id="B002", claim_id="C003", age=50),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        # After de-dup: B001 age=70, B002 age=50 → average = 60
        assert result.iloc[0]["AveragePatientAge"] == pytest.approx(60.0)

    def test_chronic_condition_dedup(self):
        # Same beneficiary with two claims — condition rate shouldn't double-count
        df = _make_df(
            _make_claim_row(provider="P001", bene_id="B001", claim_id="C001",
                            ChronicCond_Diabetes=1),
            _make_claim_row(provider="P001", bene_id="B001", claim_id="C002",
                            ChronicCond_Diabetes=1),
            _make_claim_row(provider="P001", bene_id="B002", claim_id="C003",
                            ChronicCond_Diabetes=0),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        # After de-dup: B001 Diabetes=1, B002 Diabetes=0 → mean = 0.5
        assert result.iloc[0]["ChronicCond_Diabetes"] == pytest.approx(0.5)


# ------------------------------------------------------------------ #
# Tests: missing-value indicators (critical notebook logic)
# ------------------------------------------------------------------ #

class TestMissingValueIndicators:
    def test_std_reimbursement_missing_for_single_claim_provider(self):
        """
        A provider with only one claim cannot have a std deviation — pandas
        returns NaN for std of a single value.  The pipeline must flag this.
        """
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001", reimbursement=5000.0)
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert result.iloc[0]["StdReimbursement_Missing"] == 1
        assert result.iloc[0]["StdReimbursement"] == pytest.approx(0.0)

    def test_std_reimbursement_present_for_multi_claim_provider(self):
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001", reimbursement=5000.0),
            _make_claim_row(provider="P001", claim_id="C002", reimbursement=7000.0),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert result.iloc[0]["StdReimbursement_Missing"] == 0
        assert result.iloc[0]["StdReimbursement"] > 0

    def test_average_deductible_missing_when_all_deductible_null(self):
        """
        If all DeductibleAmtPaid values are NaN, AverageDeductiblePaid is NaN
        and the missing flag should be 1.
        """
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001", deductible=None),
            _make_claim_row(provider="P001", claim_id="C002", deductible=None),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert result.iloc[0]["AverageDeductiblePaid_Missing"] == 1
        assert result.iloc[0]["AverageDeductiblePaid"] == pytest.approx(0.0)

    def test_average_deductible_present(self):
        df = _make_df(
            _make_claim_row(provider="P001", claim_id="C001", deductible=200.0),
        )
        df = preprocess(df)
        result = create_provider_features(df)
        assert result.iloc[0]["AverageDeductiblePaid_Missing"] == 0
        assert result.iloc[0]["AverageDeductiblePaid"] == pytest.approx(200.0)


# ------------------------------------------------------------------ #
# Tests: feature ordering
# ------------------------------------------------------------------ #

class TestFeatureOrdering:
    def test_output_columns_match_exact_training_order(self):
        df = _make_df(_make_claim_row())
        df = preprocess(df)
        result = create_provider_features(df)
        actual_features = list(result.columns[1:])  # skip Provider
        assert actual_features == FEATURES

    def test_no_extra_columns_in_output(self):
        df = _make_df(_make_claim_row())
        df = preprocess(df)
        result = create_provider_features(df)
        assert set(result.columns) == {"Provider"} | set(FEATURES)


# ------------------------------------------------------------------ #
# Tests: preprocessing — chronic condition re-encoding
# ------------------------------------------------------------------ #

class TestChronicConditionEncoding:
    def test_medicare_1_2_encoding_remapped_to_0_1(self):
        """
        Medicare raw data uses 1=Yes, 2=No.
        preprocess() should re-map to binary 0/1.
        """
        df = _make_df(
            _make_claim_row(
                ChronicCond_Diabetes=1,      # Yes → 1
                ChronicCond_Alzheimer=2,     # No  → 0
                ChronicCond_Cancer=1,
            )
        )
        # Artificially set to 1/2 encoding
        df["ChronicCond_Diabetes"] = 1
        df["ChronicCond_Alzheimer"] = 2

        processed = preprocess(df)
        assert processed["ChronicCond_Diabetes"].iloc[0] == 1
        assert processed["ChronicCond_Alzheimer"].iloc[0] == 0
