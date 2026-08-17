import os
import sys
import shutil
import joblib
import pandas as pd

from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    precision_score,
    recall_score,
    average_precision_score,
)

from preprocess_training_data import preprocess_training_data
from feature_engineering import create_provider_features, FEATURES


THRESHOLD = 0.23


def evaluate_model(model, X, y):
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

    predictions = (
        probabilities >= THRESHOLD
    ).astype(int)

    return {
        "PR-AUC": average_precision_score(
            y,
            probabilities,
        ),
        "Precision": precision_score(
            y,
            predictions,
            zero_division=0,
        ),
        "Recall": recall_score(
            y,
            predictions,
            zero_division=0,
        ),
    }


def update_if_better(
    input_path,
    current_model_path,
    candidate_model_path,
):
    print("Loading training data...")

    df = preprocess_training_data(
        input_path
    )

    print("Creating provider-level features...")

    provider_features = create_provider_features(
        df
    )

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
    current_model = joblib.load(
        current_model_path
    )

    print("Loading candidate model...")
    candidate_model = joblib.load(
        candidate_model_path
    )

    print()
    print("Evaluating current model...")
    current = evaluate_model(
        current_model,
        X,
        y,
    )

    print("Evaluating candidate model...")
    candidate = evaluate_model(
        candidate_model,
        X,
        y,
    )

    print()
    print("=" * 60)
    print("MODEL UPDATE DECISION")
    print("=" * 60)

    for metric in [
        "PR-AUC",
        "Precision",
        "Recall",
    ]:
        print(
            f"{metric:10s} | "
            f"Current: {current[metric]:.4f} | "
            f"Candidate: {candidate[metric]:.4f}"
        )

    candidate_is_better = (
        candidate["PR-AUC"] >= current["PR-AUC"]
        and candidate["Precision"] >= current["Precision"]
        and candidate["Recall"] >= current["Recall"]
        and (
            candidate["PR-AUC"] > current["PR-AUC"]
            or candidate["Precision"] > current["Precision"]
            or candidate["Recall"] > current["Recall"]
        )
    )

    print()

    if candidate_is_better:
        backup_path = (
            current_model_path
            + ".backup"
        )

        print(
            "Candidate model passed the update criteria."
        )

        print(
            "Creating backup:",
            backup_path,
        )

        shutil.copy2(
            current_model_path,
            backup_path,
        )

        print(
            "Activating candidate model..."
        )

        shutil.copy2(
            candidate_model_path,
            current_model_path,
        )

        print()
        print(
            "MODEL UPDATE: SUCCESS"
        )
        print(
            "Candidate model is now the active model."
        )
        print(
            "Previous model backup:",
            backup_path,
        )

    else:
        print(
            "Candidate model did NOT pass the update criteria."
        )
        print(
            "MODEL UPDATE: NOT PERFORMED"
        )
        print(
            "Current model remains active."
        )


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print(
            "Usage: python update_model_if_better.py "
            "<input_csv> <current_model> <candidate_model>"
        )
        raise SystemExit(1)

    update_if_better(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
    )
