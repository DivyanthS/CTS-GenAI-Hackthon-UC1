from __future__ import annotations

import logging
from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import (
    APP_NAME,
    APP_ENV,
    HOST,
    PORT,
    FRONTEND_URL,
    RISK_ENGINE,
    RISK_MODEL_VERSION,
    MAX_CONTENT_LENGTH,
)
from models.database import init_db, get_db
from services.risk.dummy_risk_engine import DummyRiskEngine
from services.risk.real_model_engine import RealModelRiskEngine
from services.risk.threshold_engine import threshold_engine
from services.model.loader import ModelLoader
from services.kaggle.kaggle_service import KaggleService
from services.model.training_service import ModelTrainingService
from services.provider_import_service import ProviderImportService
from services.provider_export_service import ProviderExportService
from services.prediction.prediction_service import PredictionService
from services.upload_service import UploadService
from services.dataset_service import DatasetService
from services.provider_data import ProviderDataService
from services.claim_data import ClaimDataService
from services.evidence.claim_evidence_service import ClaimEvidenceService
from services.analytics_service import AnalyticsService
from services.report_service import ReportService
from routes.upload import create_upload_routes
from routes.providers import create_provider_routes
from routes.claims import create_claim_routes
from routes.prediction import create_prediction_routes
from routes.analytics import create_analytics_routes
from routes.reports import create_report_routes
from routes.runs import create_run_routes
from routes.model import create_model_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fraud_backend")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # ---------------------------------------------------------
    # 1. Initialize Database Tables
    # ---------------------------------------------------------
    init_db()
    logger.info("Database tables initialized successfully.")

    # ---------------------------------------------------------
    # 2. Configure CORS
    # ---------------------------------------------------------
    allowed_origins = [url.strip() for url in FRONTEND_URL.split(",") if url.strip()]
    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins if allowed_origins else "*"}},
        supports_credentials=True,
    )

    # ---------------------------------------------------------
    # 3. Initialize Model Loader & Training Services
    # ---------------------------------------------------------
    model_loader = None
    try:
        model_loader = ModelLoader().load()
        logger.info("ModelLoader initialized with trained artifacts.")
    except Exception as exc:
        logger.info(f"Model artifacts not loaded: {exc}")

    kaggle_service = KaggleService()
    training_service = ModelTrainingService(kaggle_service=kaggle_service, model_loader=model_loader)
    export_service = ProviderExportService(training_service=training_service)
    import_service = ProviderImportService()

    # ---------------------------------------------------------
    # 4. Initialize Risk Engine
    # ---------------------------------------------------------
    active_risk_engine = None
    if RISK_ENGINE == "real":
        try:
            active_risk_engine = RealModelRiskEngine(loader=model_loader)
            logger.info("Initialized RealModelRiskEngine (XGBoost).")
        except Exception as exc:
            logger.warning(f"Could not initialize RealModelRiskEngine: {exc}. Falling back to DummyRiskEngine.")
            active_risk_engine = DummyRiskEngine(version=RISK_MODEL_VERSION)
    else:
        active_risk_engine = DummyRiskEngine(version=RISK_MODEL_VERSION)
        logger.info(f"Initialized DummyRiskEngine (v{RISK_MODEL_VERSION}).")

    # ---------------------------------------------------------
    # 5. Instantiate Backend Services
    # ---------------------------------------------------------
    prediction_service = PredictionService(risk_engine=active_risk_engine)
    upload_service = UploadService(risk_engine=active_risk_engine)
    dataset_service = DatasetService()
    provider_data_service = ProviderDataService()
    claim_data_service = ClaimDataService()
    claim_evidence_service = ClaimEvidenceService(prediction_service=prediction_service)
    analytics_service = AnalyticsService()
    report_service = ReportService()

    # ---------------------------------------------------------
    # 6. Register Routes & Blueprints
    # ---------------------------------------------------------
    app.register_blueprint(create_upload_routes(upload_service, dataset_service))
    app.register_blueprint(
        create_provider_routes(
            provider_data_service=provider_data_service,
            import_service=import_service,
            export_service=export_service,
            prediction_service=prediction_service,
        )
    )
    app.register_blueprint(create_claim_routes(claim_data_service, claim_evidence_service))
    app.register_blueprint(create_prediction_routes(prediction_service))
    app.register_blueprint(create_analytics_routes(analytics_service))
    app.register_blueprint(create_report_routes(report_service))
    app.register_blueprint(create_run_routes(report_service))
    app.register_blueprint(create_model_routes(training_service))

    # ---------------------------------------------------------
    # 7. Health Check Endpoint
    # ---------------------------------------------------------
    @app.get("/health")
    def health():
        db_status = "connected"
        try:
            with get_db() as db:
                db.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception as exc:
            db_status = f"error: {str(exc)}"

        return jsonify(
            {
                "status": "ok" if db_status == "connected" else "degraded",
                "service": "fraud-detection-backend",
                "database": db_status,
                "risk_engine": active_risk_engine.engine_type,
                "version": active_risk_engine.version,
                "active_model_version": training_service.active_version,
                "thresholds": threshold_engine.get_configuration()["tiers"],
            }
        ), 200

    # ---------------------------------------------------------
    # 8. Global Error Handlers
    # ---------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "BAD_REQUEST",
            "message": getattr(error, "description", "The request was invalid."),
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "NOT_FOUND",
            "message": getattr(error, "description", "The requested resource was not found."),
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "METHOD_NOT_ALLOWED",
            "message": "The HTTP method is not allowed for this endpoint.",
        }), 405

    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({
            "error": "FILE_TOO_LARGE",
            "message": "The uploaded file exceeds the allowed size limit.",
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred on the server.",
        }), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=(APP_ENV == "development"),
    )