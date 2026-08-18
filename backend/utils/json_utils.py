from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any


def make_json_safe(value: Any) -> Any:
    """
    Recursively convert values that are not standard JSON serializable
    into clean JSON-safe Python values.

    - NaN / Infinity / -Infinity -> None
    - NumPy/Pandas scalar values -> Python int/float/str/bool
    - datetime/date -> ISO format string
    - Dict / List / Tuple -> Recursively cleaned structures
    """
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]

    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value

    # Handle NumPy / Pandas scalar values
    if hasattr(value, "item"):
        try:
            val = value.item()
            return make_json_safe(val)
        except (ValueError, TypeError):
            pass

    return value
