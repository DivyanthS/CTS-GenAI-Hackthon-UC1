from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import numpy as np
import pandas as pd


PROVIDER_AFFIXES = [
    "Healthcare Group",
    "Medical Center",
    "Health Services",
    "Memorial Hospital",
    "Regional Health",
    "Clinical Associates",
    "Physicians Network",
    "Community Clinic",
]


def generate_provider_name(provider_id: str, existing_name: str | None = None) -> str:
    """
    Generate a deterministic dummy provider name if absent.
    """
    if existing_name and str(existing_name).strip() and str(existing_name).lower() != "nan":
        return str(existing_name).strip()

    clean_id = str(provider_id).strip()
    # Deterministic index derived from hash of provider ID
    hash_val = int(hashlib.md5(clean_id.encode("utf-8")).hexdigest(), 16)
    affix = PROVIDER_AFFIXES[hash_val % len(PROVIDER_AFFIXES)]

    # Strip PRV or non-digits if present for clean suffix
    digits = "".join(filter(str.isdigit, clean_id))
    suffix = digits if digits else clean_id

    return f"Provider {affix} {suffix}"


def generate_run_id(prefix: str = "RUN") -> str:
    """
    Generate a unique run ID formatted as RUN-YYYYMMDD-HHMMSS.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{date_str}"
