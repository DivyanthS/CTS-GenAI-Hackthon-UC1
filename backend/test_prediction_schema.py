from pydantic import ValidationError

from schemas.prediction import PredictionRequest, PredictionResponse


request = PredictionRequest(
    provider_id="PRV51459"
)

print("Valid request:")
print(request.model_dump())


response = PredictionResponse(
    provider_id="PRV51459",
    fraud_probability=0.9496932,
    threshold=0.23,
    decision="FRAUD_FLAG",
)

print("\nValid response:")
print(response.model_dump())


try:
    PredictionRequest(provider_id="")
except ValidationError:
    print("\nEmpty provider_id validation: PASSED")


try:
    PredictionRequest(
        provider_id="PRV51459",
        unexpected_field="test",
    )
except ValidationError:
    print("Unexpected field validation: PASSED")


print("\nPrediction schema test PASSED")