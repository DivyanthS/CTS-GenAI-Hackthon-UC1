import sys
import joblib
import pandas as pd

from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)

from preprocess_training_data import preprocess_training_data
from feature_engineering import create_provider_features, FEATURES


def evaluate_candidate(input_path, model_path):
    print("Loading training data...")
    df = preprocess_training_data(input_path)

    print("Creating provider-level features...")
    provider_features = create_provider_features(df)

    provider_target = (
        df.groupby("Provider")["PotentialFraud"]
        .first()
        .reset_index()
    )

    data = provider_features.merge(
        provider_target,
        on="Provider",
        how="inner",
    )

    X = data[FEATURES]
    y = data["PotentialFraud"]

    print("Providers:", len(data))
    print("Features:", len(FEATURES))
    print("Loading candidate model...")

    model = joblib.load(model_path)

    print("Running 5-fold cross-validation...")

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    probabilities = cross_val_predict(
        model,
        X,
        y,
        cv=cv,
        method="predict_proba",
        n_jobs=1,
    )[:, 1]

    # Use the project's locked threshold.
    threshold = 0.23
    predictions = (probabilities >= threshold).astype(int)

    print()
    print("=" * 50)
    print("CANDIDATE MODEL EVALUATION")
    print("=" * 50)
    print(f"Threshold : {threshold:.2f}")
    print(f"Accuracy  : {accuracy_score(y, predictions):.4f}")
    print(
        f"Precision : "
        f"{precision_score(y, predictions, zero_division=0):.4f}"
    )
    print(
        f"Recall    : "
        f"{recall_score(y, predictions, zero_division=0):.4f}"
    )
    print(
        f"F1        : "
        f"{f1_score(y, predictions, zero_division=0):.4f}"
    )
    print(
        f"ROC-AUC   : "
        f"{roc_auc_score(y, probabilities):.4f}"
    )
    print(
        f"PR-AUC    : "
        f"{average_precision_score(y, probabilities):.4f}"
    )
    print("=" * 50)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(
            "Usage: python evaluate_candidate.py "
            "<input_csv> <candidate_model>"
        )
        raise SystemExit(1)

    evaluate_candidate(
        sys.argv[1],
        sys.argv[2],
    )
