from __future__ import annotations

import pandas as pd

from services.claim_data import ClaimDataService
from services.feature_engineering.provider_features import MODEL_FEATURES
from services.model.predictor import FraudPredictor
from services.provider_data import ProviderDataService


class AnalyticsService:
    """Provides dashboard-level fraud analytics."""

    def __init__(
        self,
        provider_data: ProviderDataService,
        claim_data: ClaimDataService,
        predictor: FraudPredictor,
    ):
        self.provider_data = provider_data
        self.claim_data = claim_data
        self.predictor = predictor

    def get_summary(self) -> dict:
        """Return overall fraud analytics."""

        if self.provider_data.provider_features is None:
            raise RuntimeError(
                "Provider data service has not been loaded."
            )

        if self.claim_data.claims is None:
            raise RuntimeError(
                "Claim data service has not been loaded."
            )

        provider_features = self.provider_data.provider_features

        # Run the already-trained fraud model against
        # the provider-level model features.
        predictions = self.predictor.predict_batch(
            provider_features[MODEL_FEATURES]
        )

        fraud_flagged = int(
            (
                predictions["decision"] == "FRAUD_FLAG"
            ).sum()
        )

        not_flagged = int(
            (
                predictions["decision"] == "NOT_FLAGGED"
            ).sum()
        )

        total_providers = len(provider_features)
        total_claims = len(self.claim_data.claims)

        fraud_rate = (
            fraud_flagged / total_providers
            if total_providers
            else 0.0
        )

        claims = self.claim_data.claims

        total_reimbursement = float(
            pd.to_numeric(
                claims["InscClaimAmtReimbursed"],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

        # Compute dataset-level averages useful for frontend evidence calculations.
        avg_claim_reimbursement = (
            float(pd.to_numeric(claims["InscClaimAmtReimbursed"], errors="coerce").fillna(0).mean())
            if len(claims) > 0
            else 0.0
        )

        avg_provider_claims = float(provider_features["TotalClaims"].mean()) if len(provider_features) > 0 else 0.0
        avg_provider_avg_reimbursement = float(provider_features["AverageReimbursement"].mean()) if len(provider_features) > 0 else 0.0
        avg_provider_inpatient_share = float(provider_features["InpatientShare"].mean()) if len(provider_features) > 0 else 0.0
        avg_provider_inpatient_claims = avg_provider_claims * avg_provider_inpatient_share

        return {
            "total_claims": total_claims,
            "total_providers": total_providers,
            "fraud_flagged": fraud_flagged,
            "not_flagged": not_flagged,
            "fraud_rate": fraud_rate,
            "threshold": float(
                self.predictor.model_loader.threshold
            ),
            "total_reimbursement": total_reimbursement,
            "average_claim_reimbursement": avg_claim_reimbursement,
            "average_provider_claims": avg_provider_claims,
            "average_provider_average_reimbursement": avg_provider_avg_reimbursement,
            "average_provider_inpatient_claims": avg_provider_inpatient_claims,
        }