from __future__ import annotations

from flask import Blueprint, jsonify
from utils.json_utils import make_json_safe
from services.report_service import ReportService


def create_run_routes(
    report_service: ReportService,
) -> Blueprint:
    runs_bp = Blueprint("runs", __name__, url_prefix="/api/v1")

    @runs_bp.get("/runs")
    def get_runs():
        """
        Return list of all analysis runs.
        """
        try:
            runs = report_service.get_runs()
            return jsonify(make_json_safe({"runs": runs, "total": len(runs)})), 200

        except Exception as exc:
            print(f"Runs API error: {exc}")
            return jsonify({
                "error": "RUNS_ERROR",
                "message": f"Unable to retrieve analysis runs: {str(exc)}",
            }), 500

    @runs_bp.get("/runs/<run_id>")
    def get_run(run_id: str):
        """
        Return metadata for a specific analysis run.
        """
        try:
            run = report_service.get_run(run_id)
            return jsonify(make_json_safe({"run": run})), 200

        except KeyError:
            return jsonify({
                "error": "RUN_NOT_FOUND",
                "message": f"Analysis run '{run_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"Run API error for {run_id}: {exc}")
            return jsonify({
                "error": "RUN_ERROR",
                "message": f"Unable to retrieve analysis run: {str(exc)}",
            }), 500

    return runs_bp
