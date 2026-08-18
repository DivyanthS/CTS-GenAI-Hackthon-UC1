from __future__ import annotations

from flask import Blueprint, jsonify, request
from utils.json_utils import make_json_safe
from services.analytics_service import AnalyticsService


def create_analytics_routes(
    analytics_service: AnalyticsService,
) -> Blueprint:
    analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1")

    @analytics_bp.get("/analytics")
    def get_analytics():
        """
        Return dashboard-level fraud analytics summary.
        Query params: run_id
        """
        try:
            run_id = request.args.get("run_id", default=None, type=str)
            summary = analytics_service.get_summary(run_id=run_id)
            return jsonify(make_json_safe(summary)), 200

        except Exception as exc:
            print(f"Analytics API error: {exc}")
            return jsonify({
                "error": "ANALYTICS_ERROR",
                "message": f"Unable to retrieve analytics: {str(exc)}",
            }), 500

    @analytics_bp.get("/analytics/charts")
    def get_charts():
        """
        Return frontend-ready graph datasets for Recharts components.
        Query params: run_id
        """
        try:
            run_id = request.args.get("run_id", default=None, type=str)
            charts = analytics_service.get_charts(run_id=run_id)
            return jsonify(make_json_safe(charts)), 200

        except Exception as exc:
            print(f"Charts API error: {exc}")
            return jsonify({
                "error": "CHARTS_ERROR",
                "message": f"Unable to retrieve chart data: {str(exc)}",
            }), 500

    return analytics_bp
