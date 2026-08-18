from __future__ import annotations

import hashlib
from typing import Any
import numpy as np
import pandas as pd

from services.risk.base import RiskEngine
from services.risk.risk_classifier import classify_risk_score, get_factor_severity_and_impact


class DummyRiskEngine(RiskEngine):
    """
    Dataset-grounded heuristic risk engine.
    Calculates deterministic risk scores, probabilities, risk tiers, and explainable
    factors derived directly from actual dataset characteristics and statistical benchmarks.
    """

    def __init__(self, version: str = "1.0"):
        self._version = version

    @property
    def engine_type(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return self._version

    @staticmethod
    def _compute_percentile_ranks(series: pd.Series) -> pd.Series:
        """Compute 0-100 percentile rank for a numeric series."""
        s = pd.to_numeric(series, errors="coerce").fillna(0.0)
        if len(s) <= 1 or s.nunique() <= 1:
            return pd.Series(50.0, index=series.index)
        ranks = s.rank(pct=True, method="average") * 100.0
        return ranks

    def _calculate_benchmarks(self, df: pd.DataFrame) -> dict[str, dict[str, float]]:
        """Calculate statistical benchmarks across all providers in the dataset."""
        benchmarks: dict[str, dict[str, float]] = {}
        numeric_cols = [
            "TotalClaims",
            "TotalReimbursement",
            "AverageReimbursement",
            "MaxReimbursement",
            "StdReimbursement",
            "TotalDeductiblePaid",
            "AverageDeductiblePaid",
            "ClaimsPerBeneficiary",
            "InpatientShare",
            "UniqueAttendingPhysicians",
            "AveragePatientAge",
            "AverageChronicConditionCount",
        ]

        for col in numeric_cols:
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                benchmarks[col] = {
                    "mean": float(s.mean()),
                    "median": float(s.median()),
                    "std": float(s.std()) if len(s) > 1 else 0.0,
                    "min": float(s.min()),
                    "max": float(s.max()),
                    "p25": float(s.quantile(0.25)),
                    "p75": float(s.quantile(0.75)),
                    "p90": float(s.quantile(0.90)),
                    "p95": float(s.quantile(0.95)),
                }
            else:
                benchmarks[col] = {
                    "mean": 0.0,
                    "median": 0.0,
                    "std": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p25": 0.0,
                    "p75": 0.0,
                    "p90": 0.0,
                    "p95": 0.0,
                }

        return benchmarks

    def _generate_provider_risk_factors(
        self,
        row: pd.Series | dict[str, Any],
        benchmarks: dict[str, dict[str, float]],
        risk_level: str,
    ) -> list[dict[str, Any]]:
        """Generate explainable fraud risk factors comparing provider metrics to dataset benchmarks."""
        factors: list[dict[str, Any]] = []

        def get_val(key: str) -> float:
            v = row.get(key, 0.0)
            try:
                return float(v) if pd.notna(v) else 0.0
            except (ValueError, TypeError):
                return 0.0

        # Check 1: Average Reimbursement
        avg_reimb = get_val("AverageReimbursement")
        bm_avg_reimb = benchmarks.get("AverageReimbursement", {}).get("median", 0.0) or benchmarks.get("AverageReimbursement", {}).get("mean", 0.0)
        if bm_avg_reimb > 0:
            diff_pct = ((avg_reimb - bm_avg_reimb) / bm_avg_reimb) * 100.0
            if diff_pct > 15.0 or risk_level in ["High", "Critical"]:
                sev, imp = get_factor_severity_and_impact(max(0.0, diff_pct))
                explanation = (
                    f"Average reimbursement of ${avg_reimb:,.2f} is {abs(diff_pct):.1f}% "
                    f"{'above' if diff_pct >= 0 else 'below'} the dataset benchmark (${bm_avg_reimb:,.2f})."
                )
                factors.append({
                    "name": "Average Reimbursement",
                    "provider_value": round(avg_reimb, 2),
                    "benchmark": round(bm_avg_reimb, 2),
                    "difference_percent": round(diff_pct, 1),
                    "impact": imp,
                    "severity": sev,
                    "explanation": explanation,
                })

        # Check 2: Total Reimbursement Volume
        tot_reimb = get_val("TotalReimbursement")
        bm_tot_reimb = benchmarks.get("TotalReimbursement", {}).get("median", 0.0) or benchmarks.get("TotalReimbursement", {}).get("mean", 0.0)
        if bm_tot_reimb > 0:
            diff_pct = ((tot_reimb - bm_tot_reimb) / bm_tot_reimb) * 100.0
            if diff_pct > 25.0:
                sev, imp = get_factor_severity_and_impact(diff_pct)
                factors.append({
                    "name": "Total Reimbursement Exposure",
                    "provider_value": round(tot_reimb, 2),
                    "benchmark": round(bm_tot_reimb, 2),
                    "difference_percent": round(diff_pct, 1),
                    "impact": imp,
                    "severity": sev,
                    "explanation": f"Total reimbursement of ${tot_reimb:,.2f} is {diff_pct:.1f}% above the dataset benchmark.",
                })

        # Check 3: Claims Per Beneficiary
        cpb = get_val("ClaimsPerBeneficiary")
        bm_cpb = benchmarks.get("ClaimsPerBeneficiary", {}).get("median", 0.0) or benchmarks.get("ClaimsPerBeneficiary", {}).get("mean", 1.0)
        if bm_cpb > 0:
            diff_pct = ((cpb - bm_cpb) / bm_cpb) * 100.0
            if diff_pct > 20.0:
                sev, imp = get_factor_severity_and_impact(diff_pct)
                factors.append({
                    "name": "Claims Per Beneficiary Frequency",
                    "provider_value": round(cpb, 2),
                    "benchmark": round(bm_cpb, 2),
                    "difference_percent": round(diff_pct, 1),
                    "impact": imp,
                    "severity": sev,
                    "explanation": f"Claims per beneficiary frequency ({cpb:.2f}) is {diff_pct:.1f}% higher than peer average.",
                })

        # Check 4: Inpatient Share Concentration
        inpatient_share = get_val("InpatientShare")
        bm_inpatient = benchmarks.get("InpatientShare", {}).get("mean", 0.0)
        if inpatient_share > 0.35 and inpatient_share > bm_inpatient:
            diff_pct = ((inpatient_share - bm_inpatient) / (bm_inpatient or 0.1)) * 100.0
            sev, imp = get_factor_severity_and_impact(max(0.0, diff_pct))
            factors.append({
                "name": "Inpatient Claim Concentration",
                "provider_value": round(inpatient_share * 100.0, 1),
                "benchmark": round(bm_inpatient * 100.0, 1),
                "difference_percent": round(diff_pct, 1),
                "impact": imp,
                "severity": sev,
                "explanation": f"Inpatient claims represent {inpatient_share * 100.0:.1f}% of total claims (dataset average: {bm_inpatient * 100.0:.1f}%).",
            })

        # Check 5: Claim Volume
        tot_claims = get_val("TotalClaims")
        bm_claims = benchmarks.get("TotalClaims", {}).get("median", 0.0) or benchmarks.get("TotalClaims", {}).get("mean", 0.0)
        if bm_claims > 0 and tot_claims > bm_claims * 1.5:
            diff_pct = ((tot_claims - bm_claims) / bm_claims) * 100.0
            sev, imp = get_factor_severity_and_impact(diff_pct)
            factors.append({
                "name": "Claim Volume Anomaly",
                "provider_value": round(tot_claims, 0),
                "benchmark": round(bm_claims, 0),
                "difference_percent": round(diff_pct, 1),
                "impact": imp,
                "severity": sev,
                "explanation": f"Provider submitted {int(tot_claims)} claims, exceeding median peer volume by {diff_pct:.1f}%.",
            })

        # Check 6: Physician Concentration / Diversity
        unique_attending = get_val("UniqueAttendingPhysicians")
        if tot_claims > 20 and unique_attending <= 2:
            factors.append({
                "name": "Physician Concentration Pattern",
                "provider_value": round(unique_attending, 0),
                "benchmark": round(benchmarks.get("UniqueAttendingPhysicians", {}).get("median", 3.0), 0),
                "difference_percent": -50.0,
                "impact": "HIGH",
                "severity": "HIGH",
                "explanation": f"High claim volume ({int(tot_claims)} claims) concentrated across only {int(unique_attending)} attending physician(s).",
            })

        # Sort factors by difference_percent descending
        factors.sort(key=lambda x: abs(x.get("difference_percent") or 0.0), reverse=True)
        return factors

    def predict_batch(
        self,
        provider_features_df: pd.DataFrame,
        dataset_claims_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """
        Calculate dataset-grounded dummy risk scores for all providers in batch.
        """
        df = provider_features_df.copy()
        benchmarks = self._calculate_benchmarks(df)

        # 1. Percentile-based feature scores (0 - 100 scale)
        claim_volume_score = self._compute_percentile_ranks(df["TotalClaims"])
        reimbursement_score = self._compute_percentile_ranks(df["TotalReimbursement"])
        avg_reimb_score = self._compute_percentile_ranks(df["AverageReimbursement"])
        cpb_score = self._compute_percentile_ranks(df["ClaimsPerBeneficiary"])
        inpatient_score = self._compute_percentile_ranks(df["InpatientShare"])

        # Physician pattern: high claims per attending physician increases score
        attending_claims_ratio = (
            df["TotalClaims"] / df["UniqueAttendingPhysicians"].clip(lower=1)
        )
        physician_score = self._compute_percentile_ranks(attending_claims_ratio)

        deductible_score = self._compute_percentile_ranks(df["AverageDeductiblePaid"])

        # 2. Weighted conceptual formula:
        # risk_score = 0.20 * claim_volume + 0.25 * reimbursement + 0.15 * avg_reimbursement +
        #              0.15 * claims_per_beneficiary + 0.10 * inpatient + 0.10 * physician_pattern +
        #              0.05 * deductible
        composite_score = (
            0.20 * claim_volume_score
            + 0.25 * reimbursement_score
            + 0.15 * avg_reimb_score
            + 0.15 * cpb_score
            + 0.10 * inpatient_score
            + 0.10 * physician_score
            + 0.05 * deductible_score
        )

        # 3. Add small deterministic variation based on Provider ID to avoid identical ties
        deterministic_deltas = []
        for pid in df["Provider"].astype(str):
            h = int(hashlib.md5(pid.encode("utf-8")).hexdigest()[:6], 16)
            # deterministic delta in range [-3.0, +3.0]
            delta = ((h % 600) / 100.0) - 3.0
            deterministic_deltas.append(delta)

        adjusted_score = composite_score + pd.Series(deterministic_deltas, index=df.index)

        # 4. Calibration: Ensure meaningful spread across Low, Medium, High, Critical
        # Map percentiles of composite score so top ~5-15% are Critical, next 15-25% High,
        # middle 30-40% Medium, bottom 30-40% Low, while preserving individual metric correlations
        if len(adjusted_score) > 5:
            # Rank-based score calibration
            calibrated_percentiles = adjusted_score.rank(pct=True) * 100.0
            # Blend 50% raw composite and 50% percentile calibration for a balanced distribution
            final_raw = 0.50 * adjusted_score + 0.50 * calibrated_percentiles
        else:
            final_raw = adjusted_score

        # Clamp between 0 and 100
        risk_scores = np.clip(final_raw, 0.0, 100.0).round(2)
        risk_probabilities = (risk_scores / 100.0).round(4)

        # 5. Classify levels and generate factor explanations
        risk_levels = []
        decisions = []
        all_risk_factors = []

        for idx, row in df.iterrows():
            score = risk_scores.loc[idx]
            level, decision, _ = classify_risk_score(score)
            risk_levels.append(level)
            decisions.append(decision)

            factors = self._generate_provider_risk_factors(row, benchmarks, level)
            all_risk_factors.append(factors)

        results_df = pd.DataFrame(
            {
                "Provider": df["Provider"],
                "risk_score": risk_scores,
                "risk_probability": risk_probabilities,
                "risk_level": risk_levels,
                "decision": decisions,
                "risk_factors": all_risk_factors,
                "model_type": self.engine_type,
                "model_version": self.version,
                # Legacy compatibility fields
                "fraud_probability": risk_probabilities,
                "threshold": 0.5,
            },
            index=df.index,
        )

        return results_df

    def predict_provider(
        self,
        features: dict[str, Any],
        benchmarks: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Single provider prediction.
        """
        provider_id = str(features.get("Provider", "UNKNOWN")).strip()
        df_single = pd.DataFrame([features])
        if "Provider" not in df_single.columns:
            df_single["Provider"] = provider_id

        # Calculate or use provided benchmarks
        if benchmarks is None:
            benchmarks = self._calculate_benchmarks(df_single)

        # Compute simple score from single features
        avg_reimb = float(features.get("AverageReimbursement", 0.0) or 0.0)
        tot_claims = float(features.get("TotalClaims", 0.0) or 0.0)
        inpatient_share = float(features.get("InpatientShare", 0.0) or 0.0)
        cpb = float(features.get("ClaimsPerBeneficiary", 1.0) or 1.0)

        # Base score heuristic
        score = min(100.0, (
            (min(avg_reimb, 15000.0) / 150.0) * 0.40
            + (min(tot_claims, 500.0) / 5.0) * 0.30
            + (inpatient_share * 100.0) * 0.15
            + (min(cpb, 10.0) * 10.0) * 0.15
        ))

        # Deterministic delta
        h = int(hashlib.md5(provider_id.encode("utf-8")).hexdigest()[:6], 16)
        score = float(np.clip(score + (((h % 400) / 100.0) - 2.0), 0.0, 100.0))
        probability = round(score / 100.0, 4)
        level, decision, _ = classify_risk_score(score)

        factors = self._generate_provider_risk_factors(features, benchmarks, level)

        return {
            "provider_id": provider_id,
            "risk_score": round(score, 2),
            "risk_probability": probability,
            "risk_level": level,
            "decision": decision,
            "model_type": self.engine_type,
            "model_version": self.version,
            "risk_factors": factors,
            "fraud_probability": probability,
            "threshold": 0.5,
        }
