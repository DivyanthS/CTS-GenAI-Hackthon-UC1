from routes.upload import create_upload_routes
from routes.providers import create_provider_routes
from routes.claims import create_claim_routes
from routes.prediction import create_prediction_routes
from routes.analytics import create_analytics_routes
from routes.reports import create_report_routes
from routes.runs import create_run_routes
from routes.model import create_model_routes

__all__ = [
    "create_upload_routes",
    "create_provider_routes",
    "create_claim_routes",
    "create_prediction_routes",
    "create_analytics_routes",
    "create_report_routes",
    "create_run_routes",
    "create_model_routes",
]
