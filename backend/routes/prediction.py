from __future__ import annotations

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from schemas.prediction import PredictionRequest
from services.prediction.prediction_service import PredictionService
from utils.json_utils import make_json_safe


def create_prediction_routes(
    prediction_service: PredictionService,
) -> Blueprint:
    prediction_bp = Blueprint("prediction", __name__, url_prefix="/api/v1")

    @prediction_bp.post("/predict")
    def predict():
        """
        Generate fraud risk prediction for a single provider.
        """
        try:
            payload = PredictionRequest.model_validate(
                request.get_json(silent=True) or {}
            )
        except ValidationError as exc:
            return jsonify({
                "error": "VALIDATION_ERROR",
                "message": "Invalid prediction request.",
                "details": exc.errors(),
            }), 400
        except Exception:
            return jsonify({
                "error": "INVALID_REQUEST",
                "message": "Request body must be valid JSON.",
            }), 400

        try:
            result = prediction_service.predict(payload.provider_id)
            return jsonify(make_json_safe(result)), 200

        except KeyError:
            return jsonify({
                "error": "PROVIDER_NOT_FOUND",
                "message": f"Provider '{payload.provider_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"Prediction error for {payload.provider_id}: {exc}")
            return jsonify({
                "error": "PREDICTION_ERROR",
                "message": f"Unable to generate prediction: {str(exc)}",
            }), 500

    return prediction_bp