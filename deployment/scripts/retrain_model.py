import os
import sys
import joblib
import pandas as pd

from xgboost import XGBClassifier

from preprocess_training_data import preprocess_training_data
from feature_engineering import create_provider_features, FEATURES


def train_candidate_model(input_path, output_path):
    print("Loading and preprocessing training data...")
    df = preprocess_training_data(input_path)

    print("Creating provider-level features...")
    provider_features = create_provider_features(df)

    print("Preparing training data...")

    X = provider_features[FEATURES]

    # One target label per provider
    provider_target = (
        df.groupby("Provider")["PotentialFraud"]
        .first()
        .reset_index()
    )

    training_data = provider_features.merge(
        provider_target,
        on="Provider",
        how="inner",
    )

    X = training_data[FEATURES]
    y = training_data["PotentialFraud"]

    print("Providers:", len(training_data))
    print("Features:", len(FEATURES))
    print("Fraud labels:")
    print(y.value_counts().to_dict())

    print("Training XGBoost candidate model...")

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=1,
    )

    model.fit(X, y)

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True,
    )

    joblib.dump(model, output_path)

    print()
    print("Candidate model training completed successfully")
    print("Saved to:", output_path)
    print("Model type:", type(model))
    print("Feature count:", len(FEATURES))


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(
            "Usage: python retrain_model.py "
            "<input_csv> <output_model>"
        )
        raise SystemExit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    train_candidate_model(
        input_path,
        output_path,
    )
