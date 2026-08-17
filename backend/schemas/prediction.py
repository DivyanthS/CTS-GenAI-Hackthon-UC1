from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    provider_id: str = Field(
        min_length=1,
        description="Provider identifier",
    )