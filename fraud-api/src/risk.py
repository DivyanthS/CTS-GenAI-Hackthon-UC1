"""
src/risk.py

Risk banding logic for the Fraud-Risk Detection API.

Classification decision
-----------------------
  probability >= FRAUD_THRESHOLD (0.23)  →  FLAGGED  (binary classifier decision)
  probability <  FRAUD_THRESHOLD         →  NOT_FLAGGED

Risk levels (for prioritisation / triage — NOT the binary decision)
--------------------------------------------------------------------
  probability < LOW_MAX (= FRAUD_THRESHOLD = 0.23)   →  LOW
  LOW_MAX <= probability < MEDIUM_MAX (0.60)          →  MEDIUM  (FLAGGED_FOR_REVIEW)
  probability >= MEDIUM_MAX                           →  HIGH    (FLAGGED)

All boundaries are configurable through environment variables so they can
be changed without touching application code:

  FRAUD_THRESHOLD   (default: 0.23)
  RISK_LOW_MAX      (default: same as FRAUD_THRESHOLD)
  RISK_MEDIUM_MAX   (default: 0.60)
"""

import os

# ------------------------------------------------------------------ #
# Configuration — read from environment with validated defaults
# ------------------------------------------------------------------ #

FRAUD_THRESHOLD: float = float(os.getenv("FRAUD_THRESHOLD", "0.23"))
RISK_LOW_MAX: float = float(os.getenv("RISK_LOW_MAX", str(FRAUD_THRESHOLD)))
RISK_MEDIUM_MAX: float = float(os.getenv("RISK_MEDIUM_MAX", "0.60"))


def classify(probability: float) -> dict:
    """
    Convert a raw fraud probability into a decision + risk level.

    Parameters
    ----------
    probability : float
        Fraud probability from the model (0.0 – 1.0).

    Returns
    -------
    dict with keys:
        decision   : "FLAGGED" | "FLAGGED_FOR_REVIEW" | "NOT_FLAGGED"
        risk_level : "HIGH" | "MEDIUM" | "LOW"
    """
    if probability >= RISK_MEDIUM_MAX:
        risk_level = "HIGH"
        decision = "FLAGGED"
    elif probability >= RISK_LOW_MAX:
        risk_level = "MEDIUM"
        decision = "FLAGGED_FOR_REVIEW"
    else:
        risk_level = "LOW"
        decision = "NOT_FLAGGED"

    return {
        "decision": decision,
        "risk_level": risk_level,
    }


def get_thresholds() -> dict:
    """Return the currently active threshold configuration."""
    return {
        "fraud_threshold": FRAUD_THRESHOLD,
        "risk_low_max": RISK_LOW_MAX,
        "risk_medium_max": RISK_MEDIUM_MAX,
    }
