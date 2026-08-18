from __future__ import annotations

from typing import Any
from models.database import get_db
from models.claim import Claim
from models.provider import Provider
from models.risk_assessment import RiskAssessment
from services.prediction.prediction_service import PredictionService


class ClaimEvidenceService:
    """
    Builds dataset-grounded claim explanation and context from the database.
    """

    def __init__(self, prediction_service: PredictionService):
        self.prediction_service = prediction_service

    @staticmethod
    def _factor(
        name: str,
        value: float,
        peer_value: float,
        note: str,
        *,
        claim_value: bool = False,
    ) -> dict[str, Any]:
        diff_percent = (
            ((value - peer_value) / peer_value) * 100.0
            if peer_value != 0
            else 0.0
        )
        return {
            "name": name,
            **({"claim_value": round(value, 2)} if claim_value else {"provider_value": round(value, 2)}),
            "peer_value": round(peer_value, 2),
            "difference_percent": round(diff_percent, 1),
            "direction": (
                "above" if diff_percent > 0
                else "below" if diff_percent < 0
                else "equal"
            ),
            "impact": "HIGH" if abs(diff_percent) > 50 else "MEDIUM" if abs(diff_percent) > 20 else "LOW",
            "note": note,
        }

    def get_explanation(self, claim_id: str) -> dict[str, Any]:
        clean_cid = str(claim_id).strip()

        with get_db() as db:
            claim = db.query(Claim).filter(Claim.claim_id == clean_cid).order_by(Claim.id.desc()).first()
            if not claim:
                raise KeyError(f"Claim not found: {clean_cid}")

            target_claim_id = str(claim.claim_id)
            provider_id = str(claim.provider_id)
            provider = db.query(Provider).filter(Provider.provider_id == provider_id).first()

            # Dataset benchmarks
            all_providers = db.query(Provider).all()
            peer_providers = [p for p in all_providers if p.provider_id != provider_id]
            cohort_size = len(peer_providers)

            if peer_providers:
                peer_claim_count = sum(p.total_claims for p in peer_providers) / len(peer_providers)
                peer_avg_reimb = sum(p.average_reimbursement for p in peer_providers) / len(peer_providers)
            else:
                peer_claim_count = provider.total_claims if provider else 1.0
                peer_avg_reimb = provider.average_reimbursement if provider else 0.0

            claim_reimb = float(claim.reimbursement_amount or 0.0)
            prov_avg_reimb = float(provider.average_reimbursement if provider else 0.0)
            prov_tot_claims = float(provider.total_claims if provider else 0.0)

            factors: list[dict[str, Any]] = []

            # 1. Provider Claim Volume vs Peer Average
            factors.append(self._factor(
                "Provider claim volume",
                float(prov_tot_claims),
                float(peer_claim_count),
                "Provider total claims compared with the mean for all other scored providers.",
            ))

            # 2. Average Reimbursement vs Peer Average
            factors.append(self._factor(
                "Average reimbursement",
                float(prov_avg_reimb),
                float(peer_avg_reimb),
                "Provider average reimbursement compared with the mean for all other scored providers.",
            ))

            # 3. Claim Reimbursement vs Provider Average
            factors.append(self._factor(
                "Claim reimbursement",
                float(claim_reimb),
                float(prov_avg_reimb) if prov_avg_reimb > 0 else float(peer_avg_reimb),
                "Selected claim reimbursement compared with this provider's average reimbursement per claim.",
                claim_value=True,
            ))

            # Related claims from this provider
            related_db = (
                db.query(Claim)
                .filter(Claim.provider_id == provider_id, Claim.claim_id != clean_cid)
                .limit(5)
                .all()
            )
            related_claims = [
                {
                    "claim_id": str(r.claim_id),
                    "claim_type": str(r.claim_type),
                    "reimbursement": float(r.reimbursement_amount or 0.0),
                    "claim_start_date": str(r.claim_start_date or ""),
                    "claim_end_date": str(r.claim_end_date or ""),
                }
                for r in related_db
            ]

        # Prediction details for provider
        prediction = self.prediction_service.predict(provider_id)

        review_focus = [
            f"Review {factor['name'].lower()}, which is {factor['difference_percent']:.1f}% above its comparison value."
            for factor in factors
            if factor["difference_percent"] is not None and factor["difference_percent"] >= 20.0
        ]

        if prediction.get("risk_level") in ["High", "Critical"]:
            review_focus.append(
                f"Review provider-level {prediction.get('risk_level')} risk signal ({prediction.get('risk_score')}/100) alongside claim specifics."
            )

        factor_names = ", ".join(factor["name"].lower() for factor in factors)

        return {
            "claim_id": target_claim_id,
            "provider_id": provider_id,
            "risk": {
                "scope": "provider",
                "risk_score": prediction.get("risk_score"),
                "risk_probability": prediction.get("risk_probability"),
                "risk_level": prediction.get("risk_level"),
                "decision": prediction.get("decision"),
                "fraud_probability": prediction.get("fraud_probability"),
                "threshold": prediction.get("threshold"),
            },
            "summary": (
                f"This claim is associated with provider {provider_id}. The provider is assessed as "
                f"{prediction.get('risk_level')} risk (Score: {prediction.get('risk_score'):.1f}/100). "
                f"Dataset evidence evaluates {factor_names} for investigator review; "
                "this does not assign an independent claim-level fraud verdict."
            ),
            "evidence_basis": {
                "peer_definition": "mean of all other scored providers in dataset",
                "provider_cohort_size": cohort_size,
            },
            "factors": factors,
            "model_contributions": [],
            "related_claims": related_claims,
            "review_focus": review_focus,
            "disclaimer": "Risk assessment is dataset-derived and not a legal determination of fraud.",
        }
