import pandas as pd

from services.feature_engineering.provider_features import (
    MODEL_FEATURES,
    build_provider_features,
)
from services.model.loader import ModelLoader


CSV_PATH = "data/All_Datasets_Combined1.csv"


print("Loading combined dataset...")
df = pd.read_csv(CSV_PATH, low_memory=False)

print("Rows:", len(df))
print("Providers:", df["Provider"].nunique())

print("\nBuilding provider features...")
provider_features = build_provider_features(df)

print("Provider feature matrix:", provider_features.shape)

print("\nLoading trained model...")
loader = ModelLoader().load()

print("Model:", type(loader.model).__name__)
print("Model features:", loader.feature_count)
print("Decision threshold:", loader.threshold)

# ---------------------------------------------------------
# Prepare exact model input
# ---------------------------------------------------------
X = provider_features[MODEL_FEATURES]

print("\nRunning XGBoost inference...")

probabilities = loader.model.predict_proba(X)

# Class 1 = positive/fraud-risk probability
fraud_probabilities = probabilities[:, 1]

results = provider_features[["Provider"]].copy()

results["fraud_probability"] = fraud_probabilities
results["threshold"] = loader.threshold
results["decision"] = (
    results["fraud_probability"] >= loader.threshold
).map(
    {
        True: "FRAUD_FLAG",
        False: "NOT_FLAGGED",
    }
)

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
print("\n=== INFERENCE RESULTS ===")

print("Providers scored:", len(results))
print(
    "Minimum probability:",
    results["fraud_probability"].min(),
)
print(
    "Maximum probability:",
    results["fraud_probability"].max(),
)
print(
    "Average probability:",
    results["fraud_probability"].mean(),
)

print("\nDecision counts:")
print(results["decision"].value_counts())

print("\nTop 10 highest-risk providers:")
print(
    results.sort_values(
        "fraud_probability",
        ascending=False,
    ).head(10).to_string(index=False)
)

print("\n=== VALIDATION ===")

assert len(results) == 5410, (
    f"Expected 5410 providers, got {len(results)}"
)

assert len(probabilities) == 5410, (
    "Model did not return one prediction per provider"
)

assert probabilities.shape[1] == 2, (
    "Expected binary classification probabilities"
)

assert ((fraud_probabilities >= 0) & (fraud_probabilities <= 1)).all(), (
    "Fraud probabilities must be between 0 and 1"
)

assert results["Provider"].nunique() == 5410, (
    "Provider IDs are not unique"
)

assert results["decision"].isin(
    ["FRAUD_FLAG", "NOT_FLAGGED"]
).all(), (
    "Unexpected decision value"
)

print("\nREAL MODEL INFERENCE VALIDATION PASSED")