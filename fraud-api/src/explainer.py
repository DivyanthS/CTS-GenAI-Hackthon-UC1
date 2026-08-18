"""
src/explainer.py

SHAP-based explainability for the fraud-risk detection model.

Notebook reference: cells 89–94.
  • Uses shap.TreeExplainer(final_model)
  • Per-provider: positive SHAP values → fraud-driving features
                  negative SHAP values → legitimacy-driving features
  • Returns structured top_factors list + a human-readable NL paragraph

The TreeExplainer is initialised once when the module is imported so that
repeated requests are fast.

NOTE: We do NOT label individual claims as fraudulent — only providers.
      Language in explanations reflects provider-level risk only.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
import shap

from src.predictor import MODEL, FEATURES

logger = logging.getLogger(__name__)

# Initialise SHAP explainer once at startup
try:
    _EXPLAINER = shap.TreeExplainer(MODEL)
    logger.info("SHAP TreeExplainer initialised successfully.")
except Exception as exc:
    logger.critical("Failed to initialise SHAP explainer: %s", exc)
    raise

# Human-readable feature descriptions for the NL explanation
_FEATURE_DESCRIPTIONS: dict[str, str] = {
    "TotalClaims": "total claim volume",
    "UniqueBeneficiaries": "number of unique patients",
    "TotalReimbursement": "total reimbursement amount",
    "AverageReimbursement": "average reimbursement per claim",
    "MaxReimbursement": "maximum single-claim reimbursement",
    "StdReimbursement": "variability in reimbursement amounts",
    "TotalDeductiblePaid": "total deductible paid by patients",
    "AverageDeductiblePaid": "average deductible per claim",
    "UniqueAttendingPhysicians": "number of distinct attending physicians",
    "UniqueOperatingPhysicians": "number of distinct operating physicians",
    "UniqueOtherPhysicians": "number of distinct other physicians",
    "ClaimsPerBeneficiary": "claims per patient ratio",
    "InpatientShare": "proportion of inpatient claims",
    "AveragePatientAge": "average patient age",
    "AverageChronicConditionCount": "average number of chronic conditions per patient",
    "AveragePartACoverage": "average Medicare Part A coverage months",
    "AveragePartBCoverage": "average Medicare Part B coverage months",
    "ChronicCond_Alzheimer": "prevalence of Alzheimer's disease",
    "ChronicCond_Heartfailure": "prevalence of heart failure",
    "ChronicCond_KidneyDisease": "prevalence of kidney disease",
    "ChronicCond_Cancer": "prevalence of cancer",
    "ChronicCond_ObstrPulmonary": "prevalence of obstructive pulmonary disease",
    "ChronicCond_Depression": "prevalence of depression",
    "ChronicCond_Diabetes": "prevalence of diabetes",
    "ChronicCond_IschemicHeart": "prevalence of ischemic heart disease",
    "ChronicCond_Osteoporasis": "prevalence of osteoporosis",
    "ChronicCond_rheumatoidarthritis": "prevalence of rheumatoid arthritis",
    "ChronicCond_stroke": "prevalence of stroke",
    "AverageDeductiblePaid_Missing": "missing deductible data indicator",
    "StdReimbursement_Missing": "missing reimbursement variance indicator",
}


def explain_provider(
    provider_id: str,
    feature_row: pd.DataFrame,
    probability: float,
    risk_level: str,
    decision: str,
    top_n: int = 5,
) -> dict[str, Any]:
    """
    Generate SHAP-based explanation for a single provider.

    Parameters
    ----------
    provider_id : str
    feature_row : pd.DataFrame
        Single-row DataFrame with the 30 model features (Provider col excluded).
    probability : float
        Fraud probability already computed by predictor.
    risk_level : str
        "HIGH" | "MEDIUM" | "LOW"
    decision : str
        "FLAGGED" | "FLAGGED_FOR_REVIEW" | "NOT_FLAGGED"
    top_n : int
        Number of top positive / negative contributors to return (default 5).

    Returns
    -------
    dict with keys:
        top_factors  : list of factor dicts (feature, value, shap_value, direction)
        explanation  : human-readable paragraph string
    """
    X = feature_row[FEATURES].copy()

    # Compute SHAP values (returns array shape (1, n_features))
    raw_shap = _EXPLAINER.shap_values(X)

    if isinstance(raw_shap, list):
        # Older SHAP versions return a list for binary classification
        shap_row = np.array(raw_shap[1][0])
    else:
        shap_row = np.array(raw_shap[0])

    feature_values = X.iloc[0].values

    explanation_df = pd.DataFrame(
        {
            "feature": FEATURES,
            "value": feature_values,
            "shap_value": shap_row,
        }
    )

    # Positive SHAP → increases fraud probability
    positive = (
        explanation_df[explanation_df["shap_value"] > 0]
        .sort_values("shap_value", ascending=False)
        .head(top_n)
    )

    # Negative SHAP → decreases fraud probability (legitimacy signals)
    negative = (
        explanation_df[explanation_df["shap_value"] < 0]
        .sort_values("shap_value", ascending=True)
        .head(top_n)
    )

    top_factors = _build_factors(positive, "increases_risk") + _build_factors(
        negative, "decreases_risk"
    )

    nl_explanation = _generate_explanation(
        provider_id=provider_id,
        probability=probability,
        risk_level=risk_level,
        decision=decision,
        positive=positive,
        negative=negative,
    )

    return {
        "top_factors": top_factors,
        "explanation": nl_explanation,
    }


def _build_factors(df: pd.DataFrame, direction: str) -> list[dict]:
    factors = []
    for _, row in df.iterrows():
        factors.append(
            {
                "feature": row["feature"],
                "value": _safe_scalar(row["value"]),
                "shap_value": round(float(row["shap_value"]), 6),
                "direction": direction,
            }
        )
    return factors


def _safe_scalar(val) -> Any:
    """Convert numpy scalars to Python native types for JSON serialisation."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return round(float(val), 4)
    return val


def _generate_explanation(
    provider_id: str,
    probability: float,
    risk_level: str,
    decision: str,
    positive: pd.DataFrame,
    negative: pd.DataFrame,
) -> str:
    """
    Produce a natural-language paragraph based on actual SHAP values.
    Language always refers to the provider level, never individual claims.
    """
    prob_pct = round(probability * 100, 1)

    # Build narrative lists
    pos_descriptions = _feature_list_narrative(positive)
    neg_descriptions = _feature_list_narrative(negative)

    # Opening sentence
    opening = (
        f"Provider {provider_id} received a fraud probability of "
        f"{probability:.2f} ({prob_pct}%) and was classified as "
        f"{risk_level} RISK."
    )

    # Risk-driving factors sentence
    if pos_descriptions:
        risk_sentence = (
            f"The strongest factors increasing the fraud risk were "
            f"{pos_descriptions}."
        )
    else:
        risk_sentence = (
            "No features were identified as strongly increasing the fraud risk."
        )

    # Legitimacy-driving factors sentence
    if neg_descriptions:
        legit_sentence = (
            f"These were partially offset by {neg_descriptions}, "
            "which are consistent with legitimate provider behaviour."
        )
    else:
        legit_sentence = ""

    # Decision sentence
    if decision == "FLAGGED":
        action = (
            "This provider should be prioritised for immediate further investigation."
        )
    elif decision == "FLAGGED_FOR_REVIEW":
        action = (
            "This provider has been flagged for review and should be examined "
            "by a compliance investigator."
        )
    else:
        action = (
            "No immediate action is required, though the provider should remain "
            "subject to routine monitoring."
        )

    parts = [opening, risk_sentence]
    if legit_sentence:
        parts.append(legit_sentence)
    parts.append(action)

    return " ".join(parts)


def _feature_list_narrative(df: pd.DataFrame) -> str:
    """Convert top SHAP features into a human-readable comma-separated phrase."""
    if df.empty:
        return ""
    descriptions = [
        _FEATURE_DESCRIPTIONS.get(row["feature"], row["feature"])
        for _, row in df.iterrows()
    ]
    if len(descriptions) == 1:
        return descriptions[0]
    return ", ".join(descriptions[:-1]) + " and " + descriptions[-1]
