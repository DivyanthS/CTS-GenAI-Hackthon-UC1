import json
from pathlib import Path
from typing import Any

try:
    import joblib
except ImportError:
    import pickle as joblib

from config.settings import (
    MODEL_CONFIG_PATH,
    MODEL_PATH,
    FEATURES_PATH,
)


class ModelLoader:
    """Loads and exposes the trained fraud detection model artifacts."""

    def __init__(
        self,
        model_path: Path | None = None,
        features_path: Path | None = None,
        config_path: Path | None = None,
    ):
        self.model_path = model_path or MODEL_PATH
        self.features_path = features_path or FEATURES_PATH
        self.config_path = config_path or MODEL_CONFIG_PATH

        self.model: Any = None
        self.features: list[str] = []
        self.config: dict[str, Any] = {}

    def load(self) -> "ModelLoader":
        """Load the model and its metadata from disk."""

        self._validate_artifacts()

        self.model = joblib.load(self.model_path)

        with self.features_path.open("r", encoding="utf-8") as file:
            feature_data = json.load(file)

        with self.config_path.open("r", encoding="utf-8") as file:
            self.config = json.load(file)

        self.features = feature_data["features"]

        return self

    def reload(self) -> "ModelLoader":
        """Alias for load() to hot-reload model in memory."""
        return self.load()


    def _validate_artifacts(self) -> None:
        """Ensure all required model artifacts exist."""

        required_files = [
            self.model_path,
            self.features_path,
            self.config_path,
        ]

        missing_files = [
            str(path)
            for path in required_files
            if not path.is_file()
        ]

        if missing_files:
            raise FileNotFoundError(
                "Required model artifacts are missing: "
                + ", ".join(missing_files)
            )

    @property
    def threshold(self) -> float:
        """Return the configured fraud decision threshold."""

        return float(self.config["threshold"])

    @property
    def feature_count(self) -> int:
        """Return the number of model features."""

        return len(self.features)