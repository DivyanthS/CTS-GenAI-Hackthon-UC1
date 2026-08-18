from __future__ import annotations

from flask import Blueprint, jsonify, request
from utils.json_utils import make_json_safe
from services.provider_data import ProviderDataService
from services.provider_import_service import ProviderImportService
from services.provider_export_service import ProviderExportService
from services.prediction.prediction_service import PredictionService


def create_provider_routes(
    provider_data_service: ProviderDataService,
    import_service: ProviderImportService | None = None,
    export_service: ProviderExportService | None = None,
    prediction_service: PredictionService | None = None,
) -> Blueprint:
    providers_bp = Blueprint("providers", __name__, url_prefix="/api/v1")

    import_svc = import_service or ProviderImportService()
    export_svc = export_service or ProviderExportService()

    @providers_bp.get("/providers")
    def get_providers():
        """
        Return paginated, sorted, and filtered provider records with risk predictions.
        Query params: page, page_size, risk_level, search, sort_by, sort_order, run_id
        """
        try:
            page = request.args.get("page", default=1, type=int)
            page_size = request.args.get("page_size", default=50, type=int)
            risk_level = request.args.get("risk_level", default=None, type=str)
            search = request.args.get("search", default=None, type=str)
            sort_by = request.args.get("sort_by", default="risk_score", type=str)
            sort_order = request.args.get("sort_order", default="desc", type=str)
            run_id = request.args.get("run_id", default=None, type=str)

            providers, total = provider_data_service.get_providers(
                page=page,
                page_size=page_size,
                risk_level=risk_level,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                run_id=run_id,
            )

            total_pages = (
                (total + page_size - 1) // page_size
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
            return jsonify({
                "error": "INVALID_PAGINATION",
                "message": str(exc),
            }), 400

        except Exception as exc:
            print(f"Providers API error: {exc}")
            return jsonify({
                "error": "PROVIDERS_ERROR",
                "message": f"Unable to retrieve providers: {str(exc)}",
            }), 500

    @providers_bp.get("/providers/<provider_id>")
    def get_provider(provider_id: str):
        """
        Return detailed provider profile, risk assessment, risk factors, and summary statistics.
        """
        try:
            result = provider_data_service.get_provider(provider_id)
            return jsonify(make_json_safe(result)), 200

        except KeyError:
            return jsonify({
                "error": "PROVIDER_NOT_FOUND",
                "message": f"Provider '{provider_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"Provider API error for {provider_id}: {exc}")
            return jsonify({
                "error": "PROVIDER_ERROR",
                "message": f"Unable to retrieve provider: {str(exc)}",
            }), 500

    @providers_bp.post("/providers/import")
    def import_providers():
        """
        Import 32-column provider dataset CSV into PostgreSQL / database.
        Accepts multipart/form-data with 'file'.
        """
        if "file" not in request.files:
            return jsonify({
                "error": "FILE_REQUIRED",
                "message": "Please upload a CSV file using the 'file' field.",
            }), 400

        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return jsonify({
                "error": "FILE_REQUIRED",
                "message": "No file was selected.",
            }), 400

        filename = uploaded_file.filename
        if not filename.lower().endswith(".csv"):
            return jsonify({
                "error": "INVALID_FILE_TYPE",
                "message": "Only CSV files are supported.",
            }), 400

        try:
            file_bytes = uploaded_file.read()
            run_id = request.form.get("run_id")
            result = import_svc.import_dataset(file_bytes, filename=filename, run_id=run_id)
            return jsonify(make_json_safe(result)), 200

        except ValueError as exc:
            return jsonify({
                "error": "IMPORT_VALIDATION_ERROR",
                "message": str(exc),
            }), 400
        except Exception as exc:
            print(f"Provider import error: {exc}")
            return jsonify({
                "error": "IMPORT_ERROR",
                "message": f"Unable to import provider dataset: {str(exc)}",
            }), 500

    @providers_bp.post("/providers/export")
    def export_providers():
        """
        Export provider data to CSV from database.
        JSON payload:
          {
            "purpose": "inference" | "training",
            "run_id": optional run_id filter,
            "trigger_training": optional boolean
          }
        """
        data = request.get_json(silent=True) or {}
        purpose = data.get("purpose", "inference")
        run_id = data.get("run_id")
        trigger_training = data.get("trigger_training")

        try:
            result = export_svc.export_providers_to_csv(
                purpose=purpose,
                run_id=run_id,
                trigger_training=trigger_training,
            )
            return jsonify(make_json_safe(result)), 200

        except ValueError as exc:
            return jsonify({
                "error": "EXPORT_ERROR",
                "message": str(exc),
            }), 400
        except Exception as exc:
            print(f"Provider export error: {exc}")
            return jsonify({
                "error": "EXPORT_ERROR",
                "message": f"Unable to export provider records: {str(exc)}",
            }), 500

    @providers_bp.post("/providers/predict")
    def predict_provider_route():
        """
        Run inference for a specific provider.
        JSON payload: { "provider_id": "PRV51001" }
        """
        if prediction_service is None:
            return jsonify({
                "error": "PREDICTION_UNAVAILABLE",
                "message": "Prediction service not configured.",
            }), 500

        data = request.get_json(silent=True) or {}
        provider_id = data.get("provider_id")
        if not provider_id:
            return jsonify({
                "error": "PROVIDER_ID_REQUIRED",
                "message": "Field 'provider_id' is required.",
            }), 400

        try:
            result = prediction_service.predict(provider_id)
            return jsonify(make_json_safe(result)), 200
        except KeyError:
            return jsonify({
                "error": "PROVIDER_NOT_FOUND",
                "message": f"Provider '{provider_id}' not found.",
            }), 404
        except Exception as exc:
            print(f"Prediction error for {provider_id}: {exc}")
            return jsonify({
                "error": "PREDICTION_ERROR",
                "message": f"Unable to predict risk: {str(exc)}",
            }), 500

    return providers_bp
