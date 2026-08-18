from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
import logging

from config.settings import (
    KAGGLE_USERNAME,
    KAGGLE_KEY,
    KAGGLE_DATASET_SLUG,
    KAGGLE_KERNEL_SLUG,
)

logger = logging.getLogger("kaggle_service")


class KaggleService:
    """
    Secure client for Kaggle CLI / API interaction.
    Reads credentials strictly from environment variables and provides
    safe execution of training workflows, dataset updates, and artifact retrieval.
    """

    def __init__(
        self,
        username: str = KAGGLE_USERNAME,
        key: str = KAGGLE_KEY,
        dataset_slug: str = KAGGLE_DATASET_SLUG,
        kernel_slug: str = KAGGLE_KERNEL_SLUG,
    ):
        self.username = username or os.getenv("KAGGLE_USERNAME", "")
        self.key = key or os.getenv("KAGGLE_KEY", "")
        self.dataset_slug = dataset_slug
        self.kernel_slug = kernel_slug

    @property
    def is_configured(self) -> bool:
        """Check whether valid Kaggle credentials are provided."""
        return bool(self.username and self.key)

    def get_environment_metadata(self) -> dict[str, Any]:
        """Return non-sensitive metadata regarding Kaggle integration status."""
        return {
            "configured": self.is_configured,
            "username_set": bool(self.username),
            "key_set": bool(self.key),
            "dataset_slug": self.dataset_slug,
            "kernel_slug": self.kernel_slug,
            "mode": "kaggle_cli" if self.is_configured else "local_execution",
        }

    def _get_subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.username:
            env["KAGGLE_USERNAME"] = self.username
        if self.key:
            env["KAGGLE_KEY"] = self.key
        return env

    def upload_dataset(self, csv_file_path: str) -> dict[str, Any]:
        """
        Uploads or updates the training dataset on Kaggle.
        """
        target_path = Path(csv_file_path)
        if not target_path.is_file():
            raise FileNotFoundError(f"Training dataset file not found: {csv_file_path}")

        if not self.is_configured:
            logger.info("Kaggle credentials not configured; operating in local mode.")
            return {
                "status": "local_mock_success",
                "message": "Kaggle credentials not set; dataset validated locally.",
                "file": str(target_path),
                "dataset_slug": self.dataset_slug,
            }

        try:
            # Invoking kaggle datasets version command safely
            cmd = [
                "kaggle",
                "datasets",
                "version",
                "-p",
                str(target_path.parent),
                "-m",
                "Auto updated training data",
            ]
            result = subprocess.run(
                cmd,
                env=self._get_subprocess_env(),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Kaggle dataset upload returned code {result.returncode}: {result.stderr.strip()}")

            return {
                "status": "success" if result.returncode == 0 else "kaggle_cli_warning",
                "stdout": result.stdout.strip(),
                "dataset_slug": self.dataset_slug,
            }

        except FileNotFoundError:
            return {
                "status": "cli_unavailable",
                "message": "Kaggle CLI tool not installed in PATH; continuing in local mode.",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Kaggle upload failed: {str(exc)}",
            }

    def trigger_kernel(self) -> dict[str, Any]:
        """
        Triggers execution of the remote Kaggle training kernel.
        """
        if not self.is_configured:
            return {
                "status": "local_mock_success",
                "message": "Kaggle credentials not set; training executing via local pipeline.",
                "kernel_slug": self.kernel_slug,
            }

        try:
            cmd = ["kaggle", "kernels", "push", "-p", "."]
            result = subprocess.run(
                cmd,
                env=self._get_subprocess_env(),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            return {
                "status": "success" if result.returncode == 0 else "kaggle_kernel_warning",
                "stdout": result.stdout.strip(),
                "kernel_slug": self.kernel_slug,
            }
        except FileNotFoundError:
            return {
                "status": "cli_unavailable",
                "message": "Kaggle CLI not found; local pipeline active.",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Kaggle kernel trigger failed: {str(exc)}",
            }
