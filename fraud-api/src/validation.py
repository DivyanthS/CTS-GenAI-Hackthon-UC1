"""
src/validation.py

Input validation helpers for the /predict endpoint.

All validation errors produce structured JSON error responses with
a consistent shape:

    {
        "status": "error",
        "error_type": "<ERROR_TYPE>",
        "message": "<human-readable message>"
    }

No stack traces or internal paths are ever included in error responses.
"""

import io
import logging
import os
from typing import Optional

import pandas as pd
from flask import Response, jsonify

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Configuration
# ------------------------------------------------------------------ #

MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS: set[str] = {".csv"}


# ------------------------------------------------------------------ #
# Error response factory
# ------------------------------------------------------------------ #

def error_response(
    error_type: str,
    message: str,
    http_status: int = 400,
) -> tuple[Response, int]:
    """Return a structured JSON error response."""
    return (
        jsonify(
            {
                "status": "error",
                "error_type": error_type,
                "message": message,
            }
        ),
        http_status,
    )


# ------------------------------------------------------------------ #
# File-level validation
# ------------------------------------------------------------------ #

def validate_upload(request) -> Optional[tuple[Response, int]]:
    """
    Check that the uploaded file is present, is a CSV, and is within
    the size limit.

    Returns None if validation passes, or an error response tuple.
    """
    if "file" not in request.files:
        return error_response(
            "MISSING_FILE",
            "No file uploaded. Use multipart/form-data with field name 'file'.",
        )

    file = request.files["file"]

    if file.filename == "" or file.filename is None:
        return error_response(
            "EMPTY_FILENAME",
            "Uploaded file has no filename.",
        )

    # Extension check
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        return error_response(
            "INVALID_FILE_TYPE",
            f"Only CSV files are accepted. Received: '{file.filename}'.",
        )

    # Size check — read into memory once
    raw = file.read()
    if len(raw) == 0:
        return error_response(
            "EMPTY_FILE",
            "The uploaded CSV file is empty.",
        )

    if len(raw) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return error_response(
            "FILE_TOO_LARGE",
            f"Upload exceeds the {limit_mb} MB limit.",
        )

    # Stash raw bytes back so the caller can read them
    request._validated_csv_bytes = raw  # type: ignore[attr-defined]
    return None


# ------------------------------------------------------------------ #
# CSV parsing
# ------------------------------------------------------------------ #

def parse_csv(raw_bytes: bytes) -> tuple[Optional[pd.DataFrame], Optional[tuple[Response, int]]]:
    """
    Parse raw CSV bytes into a DataFrame.

    Returns (df, None) on success or (None, error_tuple) on failure.
    """
    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        logger.warning("CSV parsing failed: %s", exc)
        return None, error_response(
            "MALFORMED_CSV",
            "The uploaded file could not be parsed as a CSV. "
            "Ensure it is a valid, UTF-8 encoded CSV file.",
        )

    if df.empty or len(df.columns) == 0:
        return None, error_response(
            "EMPTY_CSV",
            "The uploaded CSV contains no data rows.",
        )

    return df, None


# ------------------------------------------------------------------ #
# Post-preprocessing / post-feature-engineering validation
# ------------------------------------------------------------------ #

def validate_provider_features(
    provider_df: pd.DataFrame,
    required_features: list[str],
) -> Optional[tuple[Response, int]]:
    """
    Validate that the engineered provider DataFrame is usable by the model.

    Checks:
    - At least one provider present
    - All required model features present
    - No entirely-NaN feature columns (would indicate aggregation failure)
    """
    if provider_df.empty:
        return error_response(
            "NO_PROVIDERS",
            "No valid providers found after processing the uploaded data.",
        )

    missing_features = [f for f in required_features if f not in provider_df.columns]
    if missing_features:
        return error_response(
            "MISSING_MODEL_FEATURES",
            f"Could not calculate required model features: {missing_features}. "
            "Ensure the CSV contains the necessary raw columns.",
        )

    # Check for completely-null feature columns
    feature_df = provider_df[required_features]
    all_null_cols = feature_df.columns[feature_df.isnull().all()].tolist()
    if all_null_cols:
        return error_response(
            "INSUFFICIENT_DATA",
            f"Features are entirely missing (all NaN) for: {all_null_cols}. "
            "The uploaded data may not contain sufficient claim records.",
        )

    return None
