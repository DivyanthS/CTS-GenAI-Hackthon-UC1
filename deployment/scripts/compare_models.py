import sys
import joblib
import pandas as pd

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


THRESHOLD = 0.23


def evaluate_model(model, X, y):
    probabilities = model.predict_proba(X)[:, 1]
    predictions = (probabilities >= THRESHOLD).astype(int)

    return {
        "Accuracy": accuracy_score(y, predictions),
        "Precision": precision_score(
            y, predictions, zero_division=0
        ),
        "Recall": recall_score(
            y, predictions, zero_division=0
        ),
        "F1": f1_score(
            y, predictions, zero_division=0
        ),
        "ROC-AUC": roc_auc_score(y, probabilities),
        "PR-AUC": average_precision_score(
            y, probabilities
        ),
    }


def compare_models(
    input_path,
    current_model_path,
    candidate_model_path,
):
    print("Loading and preprocessing data...")

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
    print("Threshold:", THRESHOLD)

    print()
    print("Loading current model...")
    current_model = joblib.load(current_model_path)

    print("Loading candidate model...")
    candidate_model = joblib.load(candidate_model_path)

    current_results = evaluate_model(
        current_model,
        X,
        y,
    )

    candidate_results = evaluate_model(
        candidate_model,
        X,
        y,
    )

    comparison = pd.DataFrame(
        {
            "Current Model": current_results,
            "Candidate Model": candidate_results,
        }
    )

    comparison["Candidate - Current"] = (
        comparison["Candidate Model"]
        - comparison["Current Model"]
    )

    print()
    print("=" * 70)
    print("CURRENT vs CANDIDATE MODEL")
    print("=" * 70)

    print(comparison.to_string(float_format=lambda x: f"{x:.4f}"))

    print()
    print("=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    for metric in comparison.index:
        difference = comparison.loc[
            metric,
            "Candidate - Current",
        ]

        if difference > 0:
            result = "BETTER"
        elif difference < 0:
            result = "LOWER"
        else:
            result = "SAME"

        print(
            f"{metric:12s}: "
            f"{result:6s} "
            f"({difference:+.4f})"
        )

    print()
    print(
        "NOTE: This comparison uses the existing project dataset."
    )
    print(
        "The current model was trained using this dataset, so"
    )
    print(
        "these results should not be treated as an unseen-data"
    )
    print(
        "production benchmark."
    )


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print(
            "Usage: python compare_models.py "
            "<input_csv> <current_model> <candidate_model>"
        )
        raise SystemExit(1)

    compare_models(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
    )
