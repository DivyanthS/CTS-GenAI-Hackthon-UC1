import pandas as pd

from services.feature_engineering.provider_features import (
    MODEL_FEATURES,
    build_provider_features,
)


CSV_PATH = "data/All_Datasets_Combined1.csv"


print("Loading combined dataset...")
df = pd.read_csv(CSV_PATH)

print("\n=== RAW DATASET ===")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Unique providers:", df["Provider"].nunique())
print("Unique beneficiaries:", df["BeneID"].nunique())

print("\nBuilding provider features...")
provider_features = build_provider_features(df)

print("\n=== PROVIDER FEATURE MATRIX ===")
print("Rows:", len(provider_features))
print("Columns:", len(provider_features.columns))
print("Expected providers:", df["Provider"].nunique())
print("Expected model features:", len(MODEL_FEATURES))

print("\n=== FEATURE COLUMNS ===")
print(provider_features.columns.tolist())

print("\n=== MISSING VALUES ===")
missing = provider_features[MODEL_FEATURES].isna().sum()
print(missing[missing > 0])

print("\n=== VALIDATION ===")

assert len(provider_features) == df["Provider"].nunique(), (
    "Provider count mismatch"
)

assert len(MODEL_FEATURES) == 30, (
    "Expected exactly 30 model features"
)

assert provider_features.shape[1] == 31, (
    "Expected Provider + 30 model features"
)

assert provider_features[MODEL_FEATURES].isna().sum().sum() == 0, (
    "Model feature matrix still contains NaN values"
)

assert provider_features["Provider"].nunique() == len(provider_features), (
    "Provider rows are not unique"
)

assert provider_features.columns.tolist() == [
    "Provider"
] + MODEL_FEATURES, (
    "Feature order does not match MODEL_FEATURES"
)

print("\nREAL PROVIDER FEATURE VALIDATION PASSED")