from services.model.loader import ModelLoader
from services.model.predictor import FraudPredictor
from services.provider_data import ProviderDataService


class PredictionService:
    """Coordinates provider lookup and model inference."""

    def __init__(
        self,
        provider_data: ProviderDataService,
        predictor: FraudPredictor,
    ):
        self.provider_data = provider_data
        self.predictor = predictor

    def predict(self, provider_id: str) -> dict:
        """Generate a fraud-risk prediction for one provider."""

        features = self.provider_data.get_provider_features(provider_id)

        result = self.predictor.predict(features)

        return {
            "provider_id": provider_id,
            **result,
        }