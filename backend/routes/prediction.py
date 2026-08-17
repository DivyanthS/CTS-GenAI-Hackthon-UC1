from __future__ import annotations

import math

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from schemas.prediction import PredictionRequest
from services.analysis_service import AnalysisService
from services.claim_data import ClaimDataService
from services.prediction_service import PredictionService
from services.provider_data import ProviderDataService
from services.analytics_service import AnalyticsService
from services.evidence.claim_evidence_service import ClaimEvidenceService


prediction_bp = Blueprint(
    "prediction",
    __name__,
    url_prefix="/api/v1",
)


def make_json_safe(value):
    """
    Recursively convert values that are not valid JSON
    into JSON-safe Python values.

    NaN / Infinity -> None

    NumPy/Pandas scalar values are converted
    into normal Python values.
    """

    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

        return value

    # Handle NumPy/Pandas scalar values.
    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except (ValueError, TypeError):
            pass

    return value


def create_prediction_routes(
    prediction_service: PredictionService,
    analysis_service: AnalysisService,
    claim_data_service: ClaimDataService,
    provider_data_service: ProviderDataService,
    analytics_service: AnalyticsService,
):
    # ============================================================
    # SINGLE PROVIDER PREDICTION
    # ============================================================

    @prediction_bp.post("/predict")
    def predict():

        try:
            payload = PredictionRequest.model_validate(
                request.get_json(silent=True)
            )

        except ValidationError as exc:
            return jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid prediction request.",
                    "details": exc.errors(),
                }
            ), 400

        except Exception:
            return jsonify(
                {
                    "error": "INVALID_REQUEST",
                    "message": "Request body must be valid JSON.",
                }
            ), 400

        try:
            result = prediction_service.predict(
                payload.provider_id
            )

            return jsonify(
                make_json_safe(result)
            ), 200

        except KeyError:
            return jsonify(
                {
                    "error": "PROVIDER_NOT_FOUND",
                    "message": (
                        f"Provider '{payload.provider_id}' "
                        "was not found."
                    ),
                }
            ), 404

        except Exception as exc:
            print(f"Prediction error: {exc}")

            return jsonify(
                {
                    "error": "PREDICTION_ERROR",
                    "message": "Unable to generate prediction.",
                }
            ), 500

    # ============================================================
    # CSV ANALYSIS
    # ============================================================

    @prediction_bp.post("/analyze")
    @prediction_bp.post("/analyze/csv")
    def analyze_csv():
        """
        Analyze an uploaded CSV dataset.

        Expected:
            multipart/form-data

        Field:
            file
        """

        if "file" not in request.files:
            return jsonify(
                {
                    "error": "FILE_REQUIRED",
                    "message": (
                        "Please upload a CSV file "
                        "using the 'file' field."
                    ),
                }
            ), 400

        uploaded_file = request.files["file"]

        if not uploaded_file.filename:
            return jsonify(
                {
                    "error": "FILE_REQUIRED",
                    "message": "No file was selected.",
                }
            ), 400

        filename = uploaded_file.filename

        if not filename.lower().endswith(".csv"):
            return jsonify(
                {
                    "error": "INVALID_FILE_TYPE",
                    "message": (
                        "Only CSV files are supported "
                        "by this endpoint."
                    ),
                }
            ), 400

        try:
            file_bytes = uploaded_file.read()

            if not file_bytes:
                return jsonify(
                    {
                        "error": "EMPTY_FILE",
                        "message": (
                            "The uploaded CSV file is empty."
                        ),
                    }
                ), 400

            result = analysis_service.analyze_file(
                file_bytes,
                filename,
            )

            return jsonify(
                make_json_safe(result)
            ), 200

        except ValueError as exc:
            return jsonify(
                {
                    "error": "ANALYSIS_VALIDATION_ERROR",
                    "message": str(exc),
                }
            ), 400

        except Exception as exc:
            print(f"CSV analysis error: {exc}")

            return jsonify(
                {
                    "error": "ANALYSIS_ERROR",
                    "message": (
                        "Unable to analyze the uploaded "
                        "CSV dataset."
                    ),
                }
            ), 500

    # ============================================================
    # CLAIMS
    # ============================================================

     # ============================================================
    # CLAIMS
    # ============================================================

    @prediction_bp.get("/claims")
    def get_claims():
        """
        Return paginated claim-level data.

        Query parameters:

            page:
                1-based page number.
                Default: 1.

            page_size:
                Number of claims per page.
                Default: 50.
                Maximum: 100.

            provider_id:
                Optional provider ID filter.
        """

        try:
            page = request.args.get(
                "page",
                default=1,
                type=int,
            )

            page_size = request.args.get(
                "page_size",
                default=50,
                type=int,
            )

            provider_id = request.args.get(
                "provider_id",
                default=None,
                type=str,
            )

            claims, total = (
                claim_data_service.get_claims(
                    page=page,
                    page_size=page_size,
                    provider_id=provider_id,
                )
            )

            total_pages = (
                (total + page_size - 1)
                // page_size
                if page_size > 0
                else 0
            )

            return jsonify(
                make_json_safe(
                    {
                        "page": page,
                        "page_size": page_size,
                        "provider_id": provider_id,
                        "total": total,
                        "total_pages": total_pages,
                        "claims": claims,
                    }
                )
            ), 200

        except ValueError as exc:

            return jsonify(
                {
                    "error": "INVALID_PAGINATION",
                    "message": str(exc),
                }
            ), 400

        except Exception as exc:

            print(
                f"Claims API error: {exc}"
            )

            return jsonify(
                {
                    "error": "CLAIMS_ERROR",
                    "message": (
                        "Unable to retrieve claims."
                    ),
                }
            ), 500
    # ============================================================
    # PROVIDERS
    # ============================================================

    @prediction_bp.get("/providers")
    def get_providers():
        """
        Return paginated provider-level data
        together with fraud predictions.
        """

        try:
            page = request.args.get(
                "page",
                default=1,
                type=int,
            )

            page_size = request.args.get(
                "page_size",
                default=50,
                type=int,
            )

            providers, total = (
                provider_data_service.get_providers(
                    page=page,
                    page_size=page_size,
                )
            )

            # ProviderDataService already built
            # the model features during startup.
            #
            # NO additional feature engineering occurs here.

            for provider in providers:

                provider_id = provider.get("Provider")

                if not provider_id:
                    continue

                try:
                    prediction = (
                        prediction_service.predict(
                            provider_id
                        )
                    )

                    provider["fraud_probability"] = (
                        prediction["fraud_probability"]
                    )

                    provider["threshold"] = (
                        prediction["threshold"]
                    )

                    provider["decision"] = (
                        prediction["decision"]
                    )

                except KeyError:

                    provider["fraud_probability"] = None
                    provider["threshold"] = None
                    provider["decision"] = "UNKNOWN"

                except Exception as exc:

                    print(
                        f"Provider prediction error "
                        f"for {provider_id}: {exc}"
                    )

                    provider["fraud_probability"] = None
                    provider["threshold"] = None
                    provider["decision"] = "ERROR"

            total_pages = (
                (total + page_size - 1)
                // page_size
                if total > 0
                else 0
            )

            return jsonify(
                make_json_safe(
                    {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": total_pages,
                        "providers": providers,
                    }
                )
            ), 200

        except ValueError as exc:
            return jsonify(
                {
                    "error": "INVALID_PAGINATION",
                    "message": str(exc),
                }
            ), 400

        except Exception as exc:
            print(f"Providers API error: {exc}")

            return jsonify(
                {
                    "error": "PROVIDERS_ERROR",
                    "message": (
                        "Unable to retrieve providers."
                    ),
                }
            ), 500

    # ============================================================
    # SINGLE PROVIDER
    # ============================================================

    @prediction_bp.get("/providers/<provider_id>")
    def get_provider(provider_id: str):
        """
        Return complete provider-level model features
        together with the fraud prediction.
        """

        try:
            provider = (
                provider_data_service.get_provider(
                    provider_id
                )
            )

            prediction = (
                prediction_service.predict(
                    provider_id
                )
            )

            provider["fraud_probability"] = (
                prediction["fraud_probability"]
            )

            provider["threshold"] = (
                prediction["threshold"]
            )

            provider["decision"] = (
                prediction["decision"]
            )

            return jsonify(
                make_json_safe(
                    {
                        "provider": provider,
                    }
                )
            ), 200

        except KeyError:
            return jsonify(
                {
                    "error": "PROVIDER_NOT_FOUND",
                    "message": (
                        f"Provider '{provider_id}' "
                        "was not found."
                    ),
                }
            ), 404

        except Exception as exc:
            print(f"Provider API error: {exc}")

            return jsonify(
                {
                    "error": "PROVIDER_ERROR",
                    "message": (
                        "Unable to retrieve provider."
                    ),
                }
            ), 500

    # ============================================================
    # ANALYTICS
    # ============================================================

    @prediction_bp.get("/analytics")
    def get_analytics():
        """
        Return dashboard-level fraud analytics.
        """

        try:
            result = (
                analytics_service.get_summary()
            )

            return jsonify(
                make_json_safe(result)
            ), 200

        except Exception as exc:
            print(f"Analytics API error: {exc}")

            return jsonify(
                {
                    "error": "ANALYTICS_ERROR",
                    "message": (
                        "Unable to retrieve analytics."
                    ),
                }
            ), 500
    # ============================================================
    # SINGLE CLAIM
    # ============================================================

    @prediction_bp.get("/claims/<claim_id>")
    def get_claim(claim_id: str):
        """
        Return one complete claim by ClaimID.

        This endpoint returns the raw mapped claim record from
        the combined dataset.

        It does NOT claim that the individual claim was directly
        classified by the provider-level XGBoost model.
        """

        try:

            claim = claim_data_service.get_claim(
                claim_id
            )

            return jsonify(
                make_json_safe(
                    {
                        "claim": claim,
                    }
                )
            ), 200

        except KeyError:

            return jsonify(
                {
                    "error": "CLAIM_NOT_FOUND",
                    "message": (
                        f"Claim '{claim_id}' "
                        "was not found."
                    ),
                }
            ), 404

        except Exception as exc:

            print(
                f"Claim API error for {claim_id}: {exc}"
            )

            return jsonify(
                {
                    "error": "CLAIM_ERROR",
                    "message": (
                        "Unable to retrieve claim."
                    ),
                }
            ), 500

    # ============================================================
    # CLAIM EXPLANATION / EVIDENCE
    # ============================================================

    @prediction_bp.get("/claims/<claim_id>/explanation")
    def get_claim_explanation(claim_id: str):
        """
        Return a deterministic, dataset-grounded explanation for one claim.

        Uses the ClaimDataService for claim lookup, the ProviderDataService
        to obtain provider features where needed, and the existing
        PredictionService to surface provider-level model signals. This
        endpoint intentionally does not fabricate claim-level probabilities.
        """
        try:
            service = ClaimEvidenceService(
                claim_data_service,
                provider_data_service,
                prediction_service,
            )

            result = service.get_explanation(claim_id)

            return jsonify(make_json_safe(result)), 200

        except KeyError:
            return jsonify(
                {
                    "error": "CLAIM_NOT_FOUND",
                    "message": (
                        f"Claim '{claim_id}' was not found."
                    ),
                }
            ), 404

        except Exception as exc:
            print(f"Claim explanation error for {claim_id}: {exc}")
            return jsonify(
                {
                    "error": "EXPLANATION_ERROR",
                    "message": (
                        "Unable to generate claim explanation."
                    ),
                }
            ), 500

    # ============================================================
    # RETURN BLUEPRINT
    # ============================================================

    return prediction_bp