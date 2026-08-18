from __future__ import annotations

import threading
from typing import Any
from config.settings import (
    DEFAULT_LOW_THRESHOLD,
    DEFAULT_HIGH_THRESHOLD,
    DEFAULT_CRITICAL_THRESHOLD,
)


class ThresholdEngine:
    """
    Dedicated threshold and risk classification engine.
    Converts ML model probabilities (0.0 to 1.0) into risk tiers:
    LOW, MEDIUM, HIGH, CRITICAL and operational decisions.

    Changing thresholds alters risk classification without requiring model retraining.
    """

    def __init__(
        self,
        low_threshold: float = DEFAULT_LOW_THRESHOLD,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
        critical_threshold: float = DEFAULT_CRITICAL_THRESHOLD,
    ):
        self._lock = threading.Lock()
        self.low_threshold = float(low_threshold)
        self.high_threshold = float(high_threshold)
        self.critical_threshold = float(critical_threshold)

    def classify(self, probability: float) -> tuple[str, str, int]:
        """
        Classify a probability (0.0 to 1.0) into (risk_level, decision, priority).
        """
        prob = float(probability)
        if prob < 0.0:
            prob = 0.0
        elif prob > 1.0:
            prob = 1.0

        with self._lock:
            low_t = self.low_threshold
            high_t = self.high_threshold
            crit_t = self.critical_threshold

        if prob >= crit_t:
            return "Critical", "URGENT_REVIEW", 1
        elif prob >= high_t:
            return "High", "REVIEW", 2
        elif prob >= low_t:
            return "Medium", "MONITOR", 3
        else:
            return "Low", "NORMAL", 4

    def get_configuration(self) -> dict[str, Any]:
        """Return the current threshold parameters and operational metadata."""
        with self._lock:
            return {
                "low_threshold": self.low_threshold,
                "high_threshold": self.high_threshold,
                "critical_threshold": self.critical_threshold,
                "tiers": {
                    "low": f"< {self.low_threshold:.2f}",
                    "medium": f"{self.low_threshold:.2f} - {self.high_threshold:.2f}",
                    "high": f"{self.high_threshold:.2f} - {self.critical_threshold:.2f}",
                    "critical": f">= {self.critical_threshold:.2f}",
                },
                "note": "Thresholds classify probability into risk levels; updating thresholds does not retrain ML models.",
            }

    def update_thresholds(
        self,
        low_threshold: float | None = None,
        high_threshold: float | None = None,
        critical_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Safely update threshold boundaries."""
        with self._lock:
            new_low = float(low_threshold) if low_threshold is not None else self.low_threshold
            new_high = float(high_threshold) if high_threshold is not None else self.high_threshold
            new_crit = float(critical_threshold) if critical_threshold is not None else self.critical_threshold

            if not (0.0 <= new_low <= new_high <= new_crit <= 1.0):
                raise ValueError(
                    f"Invalid threshold ordering: must satisfy 0.0 <= low ({new_low}) <= high ({new_high}) <= critical ({new_crit}) <= 1.0"
                )

            self.low_threshold = new_low
            self.high_threshold = new_high
            self.critical_threshold = new_crit

        return self.get_configuration()


# Global singleton instance
threshold_engine = ThresholdEngine()
