from __future__ import annotations

from typing import Tuple


def classify_risk_score(score: float) -> Tuple[str, str, str]:
    """
    Classify a 0-100 risk score into:
    (risk_level, decision, priority)

    Thresholds:
    0–29   -> Low      -> NORMAL        -> P4
    30–59  -> Medium   -> MONITOR       -> P3
    60–79  -> High     -> REVIEW        -> P2
    80–100 -> Critical -> URGENT_REVIEW -> P1
    """
    clamped = max(0.0, min(100.0, float(score)))

    if clamped >= 80.0:
        return "Critical", "URGENT_REVIEW", "P1"
    elif clamped >= 60.0:
        return "High", "REVIEW", "P2"
    elif clamped >= 30.0:
        return "Medium", "MONITOR", "P3"
    else:
        return "Low", "NORMAL", "P4"


def get_factor_severity_and_impact(diff_percent: float) -> Tuple[str, str]:
    """
    Determine severity and impact based on difference percentage over benchmark.
    """
    if diff_percent >= 100.0:
        return "CRITICAL", "HIGH"
    elif diff_percent >= 50.0:
        return "HIGH", "HIGH"
    elif diff_percent >= 25.0:
        return "MEDIUM", "MEDIUM"
    elif diff_percent >= 10.0:
        return "LOW", "LOW"
    else:
        return "LOW", "CONTEXTUAL"
