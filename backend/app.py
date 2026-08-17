import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from routes.prediction import create_prediction_routes
from services.analysis_service import AnalysisService
from services.analytics_service import AnalyticsService
from services.claim_data import ClaimDataService
from services.model.loader import ModelLoader
from services.model.predictor import FraudPredictor
from services.prediction_service import PredictionService
from services.provider_data import ProviderDataService


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    CORS(app)

    # ---------------------------------------------------------
    # 1. Load model once during application startup
    # ---------------------------------------------------------
    model_loader = ModelLoader().load()
    predictor = FraudPredictor(model_loader)

    # ---------------------------------------------------------
    # 2. Load provider-level data
    # ---------------------------------------------------------
    provider_data = ProviderDataService().load()

    # ---------------------------------------------------------
    # 3. Load claim-level data
    # ---------------------------------------------------------
    claim_data = ClaimDataService().load()

    # ---------------------------------------------------------
    # 4. Existing single-provider prediction service
    # ---------------------------------------------------------
    prediction_service = PredictionService(
        provider_data=provider_data,
        predictor=predictor,
    )

    # ---------------------------------------------------------
    # 5. CSV analysis service
    # ---------------------------------------------------------
    analysis_service = AnalysisService(
        predictor=predictor,
    )

    # ---------------------------------------------------------
    # 6. Analytics service
    # ---------------------------------------------------------
    analytics_service = AnalyticsService(
        provider_data=provider_data,
        claim_data=claim_data,
        predictor=predictor,
    )

    # ---------------------------------------------------------
    # 7. Store claim service in Flask extensions
    # ---------------------------------------------------------
    app.extensions["claim_data"] = claim_data

    # ---------------------------------------------------------
    # 8. Register routes
    # ---------------------------------------------------------
    app.register_blueprint(
        create_prediction_routes(
            prediction_service,
            analysis_service,
            claim_data,
            provider_data,
            analytics_service,
        )
    )

    # ---------------------------------------------------------
    # 9. Health check
    # ---------------------------------------------------------
    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "cts-genai-uc1-backend",
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    app.run(
        host=host,
        port=port,
        debug=False,
    )