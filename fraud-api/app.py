"""
app.py — Healthcare Fraud-Risk Detection API

Endpoints
---------
POST /predict
    Accept a raw claims CSV (multipart/form-data, field: file).
    Returns per-provider fraud probability, risk level, decision, and SHAP explanation.

GET  /health
    Liveness / readiness probe.

GET  /model-info
    Model metadata: version, features, validated performance metrics.

Environment variables
---------------------
ACTIVE_MODEL_VERSION   Model subdirectory under models/ to load (default: v1)
FRAUD_THRESHOLD        Binary classification threshold (default: 0.23)
RISK_LOW_MAX           Upper bound for LOW risk band (default: FRAUD_THRESHOLD)
RISK_MEDIUM_MAX        Upper bound for MEDIUM risk band (default: 0.60)
MAX_UPLOAD_MB          CSV upload size cap in megabytes (default: 50)
PORT                   Server port (default: 7860 for Hugging Face Spaces)
CORS_ORIGINS           Comma-separated allowed origins (default: *)
"""

import logging
import os
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

from src import explainer as exp_module  # noqa: F401 — triggers SHAP init at import
from src import predictor, risk, validation
from src.feature_engineering import FEATURES, FeatureEngineeringError, create_provider_features
from src.predictor import FEATURES as MODEL_FEATURES, get_model_info
from src.preprocessing import PreprocessingError, preprocess
from src.risk import classify, get_thresholds
from src.validation import error_response, parse_csv, validate_provider_features, validate_upload

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Flask app
# ------------------------------------------------------------------

app = Flask(__name__)

# CORS — configurable for frontend integration
_cors_origins = os.getenv("CORS_ORIGINS", "*")
CORS(app, resources={r"/*": {"origins": _cors_origins}})

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _build_provider_result(
    provider_id: str,
    feature_row,
    model_version: str,
    threshold: float,
) -> dict:
    """Run prediction + SHAP for one provider row and return the result dict."""
    from src.explainer import explain_provider
    from src.predictor import predict_single_provider

    probability = predict_single_provider(feature_row)
    classification = classify(probability)

    shap_result = explain_provider(
        provider_id=provider_id,
        feature_row=feature_row,
        probability=probability,
        risk_level=classification["risk_level"],
        decision=classification["decision"],
    )

    return {
        "provider_id": provider_id,
        "fraud_probability": round(probability, 6),
        "risk_level": classification["risk_level"],
        "decision": classification["decision"],
        "explanation": shap_result["explanation"],
        "top_factors": shap_result["top_factors"],
    }


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Liveness / readiness probe."""
    info = get_model_info()
    return jsonify(
        {
            "status": "healthy",
            "model_version": info["model_version"],
            "threshold": info["threshold"],
            "n_features": info["n_features"],
            "thresholds": get_thresholds(),
        }
    )


@app.route("/model-info", methods=["GET"])
def model_info():
    """Return model metadata and validated performance figures."""
    return jsonify(get_model_info())


@app.route("/predict", methods=["POST"])
def predict():
    """
    POST /predict

    Accepts a raw claims CSV (multipart/form-data, field: file).

    The CSV should contain individual claim records (one row per claim).
    The API aggregates them to the provider level, applies the same
    feature engineering used during training, and returns per-provider
    fraud-risk predictions.

    Returns
    -------
    JSON with structure:
    {
        "status": "success",
        "model_version": "v1",
        "threshold": 0.23,
        "n_providers": 3,
        "providers": [ { ... }, ... ]
    }
    """
    # -- 1. File upload validation --
    file_err = validate_upload(request)
    if file_err:
        return file_err

    raw_bytes = request._validated_csv_bytes  # type: ignore[attr-defined]

    # -- 2. CSV parsing --
    df, parse_err = parse_csv(raw_bytes)
    if parse_err:
        return parse_err

    # -- 3. Preprocessing --
    try:
        df_clean = preprocess(df)
    except PreprocessingError as exc:
        return error_response("PREPROCESSING_ERROR", str(exc))
    except Exception as exc:
        logger.error("Unexpected preprocessing error: %s", exc)
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred during data preprocessing.",
            http_status=500,
        )

    # -- 4. Feature engineering (117 → 30 provider-level features) --
    try:
        provider_features_df = create_provider_features(df_clean)
    except FeatureEngineeringError as exc:
        return error_response("FEATURE_ENGINEERING_ERROR", str(exc))
    except Exception as exc:
        logger.error("Unexpected feature engineering error: %s", exc)
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred during feature engineering.",
            http_status=500,
        )

    # -- 5. Validate engineered features --
    feat_err = validate_provider_features(provider_features_df, MODEL_FEATURES)
    if feat_err:
        return feat_err

    # -- 6. Predict + explain per provider --
    model_meta = get_model_info()
    results = []
    errors = []

    for _, row in provider_features_df.iterrows():
        provider_id = str(row["Provider"])
        feature_row = provider_features_df.loc[
            provider_features_df["Provider"] == provider_id,
            MODEL_FEATURES,
        ]

        try:
            result = _build_provider_result(
                provider_id=provider_id,
                feature_row=feature_row,
                model_version=model_meta["model_version"],
                threshold=model_meta["threshold"],
            )
            results.append(result)
        except Exception as exc:
            logger.warning(
                "Prediction failed for provider %s: %s", provider_id, exc
            )
            errors.append(
                {"provider_id": provider_id, "error": "Prediction could not be completed."}
            )

    if not results and errors:
        return error_response(
            "ALL_PREDICTIONS_FAILED",
            "Predictions could not be completed for any provider in the uploaded data.",
            http_status=500,
        )

    response = {
        "status": "success",
        "model_version": model_meta["model_version"],
        "threshold": model_meta["threshold"],
        "n_providers": len(results),
        "providers": results,
    }

    if errors:
        response["prediction_errors"] = errors

    return jsonify(response)


# ------------------------------------------------------------------
# Global error handlers — never expose stack traces to API users
# ------------------------------------------------------------------

@app.errorhandler(413)
def request_entity_too_large(e):
    return error_response("FILE_TOO_LARGE", "Uploaded file exceeds the server size limit.")


@app.errorhandler(404)
def not_found(e):
    return error_response("NOT_FOUND", "The requested endpoint does not exist.", http_status=404)


@app.errorhandler(405)
def method_not_allowed(e):
    return error_response(
        "METHOD_NOT_ALLOWED",
        "HTTP method not allowed for this endpoint.",
        http_status=405,
    )


@app.errorhandler(500)
def internal_error(e):
    logger.error("Unhandled server error: %s\n%s", e, traceback.format_exc())
    return error_response(
        "INTERNAL_ERROR",
        "An unexpected server error occurred.",
        http_status=500,
    )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    logger.info("Starting Fraud-Risk Detection API on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
