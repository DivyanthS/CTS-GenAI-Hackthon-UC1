from __future__ import annotations

from flask import Blueprint, jsonify, request, Response
from utils.json_utils import make_json_safe
from services.report_service import ReportService


def create_report_routes(
    report_service: ReportService,
) -> Blueprint:
    reports_bp = Blueprint("reports", __name__, url_prefix="/api/v1")

    @reports_bp.get("/reports/<run_id>")
    @reports_bp.get("/reports/<run_id>/json")
    def get_report_json(run_id: str):
        """
        Return structured 13-section report JSON for an analysis run.
        """
        try:
            report_data = report_service.generate_json_report(run_id)
            return jsonify(make_json_safe(report_data)), 200

        except KeyError:
            return jsonify({
                "error": "RUN_NOT_FOUND",
                "message": f"Analysis run '{run_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"Report generation error for {run_id}: {exc}")
            return jsonify({
                "error": "REPORT_ERROR",
                "message": f"Unable to generate report: {str(exc)}",
            }), 500

    @reports_bp.get("/reports/<run_id>/pdf")
    def get_report_pdf(run_id: str):
        """
        Return downloadable multi-page PDF report for an analysis run.
        """
        try:
            pdf_bytes = report_service.generate_pdf_report(run_id)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=Fraud_Report_{run_id}.pdf"
                },
            )

        except KeyError:
            return jsonify({
                "error": "RUN_NOT_FOUND",
                "message": f"Analysis run '{run_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"PDF generation error for {run_id}: {exc}")
            return jsonify({
                "error": "PDF_REPORT_ERROR",
                "message": f"Unable to generate PDF report: {str(exc)}",
            }), 500

    return reports_bp
