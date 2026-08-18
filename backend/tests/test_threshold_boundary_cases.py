from __future__ import annotations

import pytest
from services.risk.threshold_engine import ThresholdEngine


def test_threshold_engine_exact_boundaries():
    engine = ThresholdEngine(low_threshold=0.23, high_threshold=0.60, critical_threshold=0.80)

    # Values strictly less than low
    assert engine.classify(0.00)[0] == "Low"
    assert engine.classify(0.2299)[0] == "Low"

    # Exactly at low threshold
    assert engine.classify(0.23)[0] == "Medium"
    assert engine.classify(0.5999)[0] == "Medium"

    # Exactly at high threshold
    assert engine.classify(0.60)[0] == "High"
    assert engine.classify(0.7999)[0] == "High"

    # Exactly at critical threshold
    assert engine.classify(0.80)[0] == "Critical"
    assert engine.classify(1.00)[0] == "Critical"


def test_threshold_engine_clamping():
    engine = ThresholdEngine(low_threshold=0.23, high_threshold=0.60, critical_threshold=0.80)

    # Negative values clamped to 0.0 -> Low
    assert engine.classify(-0.5)[0] == "Low"
    # Values above 1.0 clamped to 1.0 -> Critical
    assert engine.classify(1.5)[0] == "Critical"


def test_threshold_engine_validation_errors():
    engine = ThresholdEngine()

    # Low > High
    with pytest.raises(ValueError):
        engine.update_thresholds(low_threshold=0.70, high_threshold=0.50)

    # High > Critical
    with pytest.raises(ValueError):
        engine.update_thresholds(high_threshold=0.90, critical_threshold=0.80)

    # Negative bounds
    with pytest.raises(ValueError):
        engine.update_thresholds(low_threshold=-0.1)

    # Bounds > 1.0
    with pytest.raises(ValueError):
        engine.update_thresholds(critical_threshold=1.2)
