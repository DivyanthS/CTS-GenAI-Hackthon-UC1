from __future__ import annotations

from typing import Any

import pandas as pd

from services.claim_data import ClaimDataService
from services.prediction_service import PredictionService
from services.provider_data import ProviderDataService


class ClaimEvidenceService:
    """Build deterministic claim context from the loaded claim/provider data.

    The model is provider-level. This service exposes its prediction only as
    provider risk and keeps claim observations separate.
    """

    def __init__(
        self,
        claim_data_service: ClaimDataService,
        provider_data_service: ProviderDataService,
        prediction_service: PredictionService,
    ):
        self.claim_data_service = claim_data_service
        self.provider_data_service = provider_data_service
        self.prediction_service = prediction_service

    @staticmethod
    def _number(value: Any) -> float | None:
        number = pd.to_numeric(value, errors="coerce")
        return float(number) if pd.notna(number) else None

    @staticmethod
    def _factor(
        name: str,
        value: float,
        peer_value: float,
        note: str,
        *,
        claim_value: bool = False,
    ) -> dict[str, Any]:
        difference_percent = (
            ((value - peer_value) / peer_value) * 100
            if peer_value != 0
            else None
        )
        return {
            "name": name,
            **({"claim_value": value} if claim_value else {"provider_value": value}),
            "peer_value": peer_value,
            "difference_percent": difference_percent,
            "direction": (
                "above" if difference_percent is not None and difference_percent > 0
                else "below" if difference_percent is not None and difference_percent < 0
                else "equal"
            ),
            "impact": "contextual",
            "note": note,
        }

    def get_explanation(self, claim_id: str) -> dict[str, Any]:
        claim = self.claim_data_service.get_claim(claim_id)
        provider_id = str(claim["Provider"]).strip()
        provider = self.provider_data_service.get_provider(provider_id)
        provider_features = self.provider_data_service.provider_features
        if provider_features is None:
            raise RuntimeError("Provider data service has not been loaded.")

        # The only supported peer cohort is every other scored provider.
        peers = provider_features[
            provider_features["Provider"].astype("string") != provider_id
        ]
        cohort_size = int(len(peers))
        provider_claim_count = self._number(provider.get("TotalClaims"))
        provider_average_reimbursement = self._number(provider.get("AverageReimbursement"))
        peer_claim_count = self._number(peers["TotalClaims"].mean())
        peer_average_reimbursement = self._number(peers["AverageReimbursement"].mean())
        claim_reimbursement = self._number(claim.get("InscClaimAmtReimbursed"))

        factors: list[dict[str, Any]] = []
        if provider_claim_count is not None and peer_claim_count is not None:
            factors.append(self._factor(
                "Provider claim volume", provider_claim_count, peer_claim_count,
                "Provider total claims compared with the mean for all other scored providers.",
            ))
        if provider_average_reimbursement is not None and peer_average_reimbursement is not None:
            factors.append(self._factor(
                "Average reimbursement", provider_average_reimbursement,
                peer_average_reimbursement,
                "Provider average reimbursement compared with the mean for all other scored providers.",
            ))
        if claim_reimbursement is not None and provider_average_reimbursement is not None:
            factors.append(self._factor(
                "Claim reimbursement", claim_reimbursement, provider_average_reimbursement,
                "Selected claim reimbursement compared with this provider's average reimbursement per claim.",
                claim_value=True,
            ))

        prediction = self.prediction_service.predict(provider_id)
        related, _ = self.claim_data_service.get_claims(1, 100, provider_id)
        related_claims = [
            {
                "claim_id": item.get("ClaimID"),
                "claim_type": item.get("ClaimType"),
                "reimbursement": item.get("InscClaimAmtReimbursed"),
                "claim_start_date": item.get("ClaimStartDt"),
                "claim_end_date": item.get("ClaimEndDt"),
            }
            for item in related
            if str(item.get("ClaimID")) != str(claim.get("ClaimID"))
        ][:5]

        review_focus = [
            f"Review {factor['name'].lower()}, which is {factor['difference_percent']:.1f}% above its stated comparison value."
            for factor in factors
            if factor["difference_percent"] is not None and factor["difference_percent"] >= 20
        ]
        if prediction["decision"] == "FRAUD_FLAG":
            review_focus.append(
                "Review the provider-level model risk signal alongside the dataset-derived context."
            )

        factor_names = ", ".join(factor["name"].lower() for factor in factors)
        return {
            "claim_id": claim.get("ClaimID"),
            "provider_id": provider_id,
            "risk": {"scope": "provider", **prediction},
            "summary": (
                f"This claim is associated with provider {provider_id}. The provider-level model "
                f"returned {prediction['decision']} at a probability of {prediction['fraud_probability']:.3f}. "
                f"The returned context compares {factor_names or 'available dataset metrics'} for investigator review; "
                "it does not assign a claim-level fraud probability."
            ),
            "evidence_basis": {
                "peer_definition": "mean of all other scored providers",
                "provider_cohort_size": cohort_size,
            },
            "factors": factors,
            # The model does not expose validated feature-attribution values.
            "model_contributions": [],
            "related_claims": related_claims,
            "review_focus": review_focus,
            "disclaimer": "Risk assessment is not a determination of fraud.",
        }
