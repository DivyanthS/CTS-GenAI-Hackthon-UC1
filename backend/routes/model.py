from __future__ import annotations

from flask import Blueprint, jsonify, request
from utils.json_utils import make_json_safe
from services.model.training_service import ModelTrainingService
from services.risk.threshold_engine import threshold_engine


def create_model_routes(
    training_service: ModelTrainingService,
) -> Blueprint:
    model_bp = Blueprint("model", __name__, url_prefix="/api/v1")

    @model_bp.post("/model/train")
    def trigger_retraining():
        """
        Manually trigger asynchronous model retraining.
        Optional JSON body: { "training_csv_path": "path/to/csv" }
        """
        data = request.get_json(silent=True) or {}
        training_csv_path = data.get("training_csv_path")

        try:
            job = training_service.trigger_training_job(training_csv_path=training_csv_path)
            return jsonify(make_json_safe(job)), 202
        except Exception as exc:
            print(f"Trigger retraining error: {exc}")
            return jsonify({
                "error": "TRAINING_TRIGGER_ERROR",
                "message": f"Unable to trigger retraining: {str(exc)}",
            }), 500

    @model_bp.get("/model/train/<job_id>")
    def get_job_status(job_id: str):
        """
        Retrieve live status, logs, and validation metrics for a specific training job.
        """
        try:
            job = training_service.get_job_status(job_id)
            return jsonify(make_json_safe(job)), 200
        except KeyError:
            return jsonify({
                "error": "JOB_NOT_FOUND",
                "message": f"Training job '{job_id}' was not found.",
            }), 404
        except Exception as exc:
            return jsonify({
                "error": "JOB_STATUS_ERROR",
                "message": f"Unable to fetch job status: {str(exc)}",
            }), 500

    @model_bp.get("/model/train")
    def list_jobs():
        """List history of all retraining jobs."""
        try:
            jobs = training_service.list_jobs()
            return jsonify(make_json_safe({"jobs": jobs, "total": len(jobs)})), 200
        except Exception as exc:
            return jsonify({
                "error": "LIST_JOBS_ERROR",
                "message": f"Unable to list training jobs: {str(exc)}",
            }), 500

    @model_bp.get("/model/status")
    def get_model_status():
        """
        Return active model metadata, version, feature count, and threshold status.
        """
        try:
            status = training_service.get_model_status()
            return jsonify(make_json_safe(status)), 200
        except Exception as exc:
            return jsonify({
                "error": "MODEL_STATUS_ERROR",
                "message": f"Unable to retrieve model status: {str(exc)}",
            }), 500

    @model_bp.get("/model/threshold")
    def get_threshold():
        """
        Retrieve current probability-to-risk threshold configuration.
        """
        try:
            config = threshold_engine.get_configuration()
            return jsonify(make_json_safe(config)), 200
        except Exception as exc:
            return jsonify({
                "error": "THRESHOLD_ERROR",
                "message": f"Unable to fetch thresholds: {str(exc)}",
            }), 500

    @model_bp.put("/model/threshold")
    @model_bp.post("/model/threshold")
    def update_threshold():
        """
        Update probability-to-risk threshold parameters.
        JSON payload:
          {
            "low_threshold": 0.23,
            "high_threshold": 0.60,
            "critical_threshold": 0.80
          }
        """
        data = request.get_json(silent=True) or {}
        low = data.get("low_threshold")
        high = data.get("high_threshold")
        crit = data.get("critical_threshold")

        try:
            updated = threshold_engine.update_thresholds(
                low_threshold=low,
                high_threshold=high,
                critical_threshold=crit,
            )
            return jsonify(make_json_safe(updated)), 200
        except ValueError as exc:
            return jsonify({
                "error": "INVALID_THRESHOLDS",
                "message": str(exc),
            }), 400
        except Exception as exc:
            return jsonify({
                "error": "THRESHOLD_UPDATE_ERROR",
                "message": f"Unable to update thresholds: {str(exc)}",
            }), 500

    return model_bp
