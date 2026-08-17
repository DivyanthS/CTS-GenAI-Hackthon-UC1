from __future__ import annotations

import io
import json

import pandas as pd

from services.feature_engineering.provider_features import (
    MODEL_FEATURES,
    build_provider_features,
)
from services.model.predictor import FraudPredictor


class AnalysisService:
    def __init__(self, predictor: FraudPredictor):
        self.predictor = predictor

    def analyze_file(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict:
        """
        Analyze an uploaded CSV or JSON dataset.

        CSV:
            The file is read directly using pandas.

        JSON:
            The file must contain an array of claim records,
            which is converted into a pandas DataFrame.

        The complete dataset is returned in the `claims` field.
        Missing pandas values such as NaN are converted to None
        so that the response is valid JSON.
        """

        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        extension = filename.lower().rsplit(".", 1)[-1]

        # ---------------------------------------------------------
        # 1. Read uploaded dataset
        # ---------------------------------------------------------

        if extension == "csv":
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                low_memory=False,
            )

        elif extension == "json":
            try:
                json_data = json.loads(
                    file_bytes.decode("utf-8")
                )

            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ) as exc:
                raise ValueError(
                    "Invalid JSON file."
                ) from exc

            if not isinstance(json_data, list):
                raise ValueError(
                    "JSON dataset must contain an array of records."
                )

            if not json_data:
                raise ValueError(
                    "JSON dataset is empty."
                )

            df = pd.DataFrame(json_data)

        else:
            raise ValueError(
                "Only CSV and JSON files are supported."
            )

        # ---------------------------------------------------------
        # 2. Validate dataset
        # ---------------------------------------------------------

        if df.empty:
            raise ValueError(
                "Uploaded dataset is empty."
            )

        # ---------------------------------------------------------
        # 3. Build provider-level features
        # ---------------------------------------------------------

        provider_features = build_provider_features(df)

        # ---------------------------------------------------------
        # 4. Run fraud model
        # ---------------------------------------------------------

        predictions = self.predictor.predict_batch(
            provider_features[MODEL_FEATURES]
        )

        # ---------------------------------------------------------
        # 5. Combine provider IDs with predictions
        # ---------------------------------------------------------

        results = pd.concat(
            [
                provider_features[["Provider"]]
                .reset_index(drop=True),
                predictions.reset_index(drop=True),
            ],
            axis=1,
        )

        # Highest fraud probability first.
        results = results.sort_values(
            "fraud_probability",
            ascending=False,
        )

        # ---------------------------------------------------------
        # 6. Calculate summary statistics
        # ---------------------------------------------------------

        fraud_count = int(
            (
                results["decision"]
                == "FRAUD_FLAG"
            ).sum()
        )

        not_flagged_count = int(
            len(results) - fraud_count
        )

        # ---------------------------------------------------------
        

        # ---------------------------------------------------------
        # 8. Make prediction results JSON-safe
        # ---------------------------------------------------------

        safe_results = (
            results.astype(object)
            .where(pd.notna(results), None)
            .to_dict(orient="records")
        )

        # ---------------------------------------------------------
        # 9. Return analysis response
        # ---------------------------------------------------------

        return {
            "filename": filename,
            "file_type": extension.upper(),

            "rows_processed": int(
                len(df)
            ),

            "columns": int(
                len(df.columns)
            ),

            "providers_scored": int(
                len(results)
            ),

            "fraud_flagged": fraud_count,

            "not_flagged": not_flagged_count,

            "threshold": float(
                self.predictor.model_loader.threshold
            ),

            "results": safe_results,

            # Complete dataset.
            # No 1000-row limit.
            
        }

    def analyze_csv(
        self,
        file_bytes: bytes,
    ) -> dict:
        """
        Backward-compatible CSV analysis method.
        """

        return self.analyze_file(
            file_bytes,
            "uploaded.csv",
        )