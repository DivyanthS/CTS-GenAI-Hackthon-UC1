from __future__ import annotations

from flask import Blueprint, jsonify, request
from utils.json_utils import make_json_safe
from services.upload_service import UploadService
from services.dataset_service import DatasetService


def create_upload_routes(
    upload_service: UploadService,
    dataset_service: DatasetService,
) -> Blueprint:
    upload_bp = Blueprint("upload", __name__, url_prefix="/api/v1")

    @upload_bp.post("/validate")
    def validate_dataset():
        """
        Validate an uploaded CSV dataset and return data quality checks, health score, and schema.
        Accepts: multipart/form-data with 'file'
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
                "message": "Only CSV files are supported for validation.",
            }), 400

        try:
            file_bytes = uploaded_file.read()
            result = dataset_service.validate_csv_bytes(file_bytes, filename)
            return jsonify(make_json_safe(result)), 200

        except Exception as exc:
            return jsonify({
                "error": "VALIDATION_ERROR",
                "message": f"Unable to validate CSV: {str(exc)}",
            }), 500

    @upload_bp.post("/analyze")
    @upload_bp.post("/analyze/csv")
    def analyze_csv():
        """
        Ingest, score, and persist uploaded CSV claims dataset.
        Accepts: multipart/form-data with 'file'
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
                "message": "Only CSV files are supported by this endpoint.",
            }), 400

        try:
            file_bytes = uploaded_file.read()
            result = upload_service.process_csv_upload(file_bytes, filename)
            return jsonify(make_json_safe(result)), 200

        except ValueError as exc:
            return jsonify({
                "error": "ANALYSIS_VALIDATION_ERROR",
                "message": str(exc),
            }), 400

        except Exception as exc:
            print(f"CSV analysis error: {exc}")
            return jsonify({
                "error": "ANALYSIS_ERROR",
                "message": f"Unable to analyze the uploaded CSV dataset: {str(exc)}",
            }), 500

    return upload_bp
