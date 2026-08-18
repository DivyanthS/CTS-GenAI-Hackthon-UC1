from __future__ import annotations

from typing import Any
from sqlalchemy import func
from models.database import get_db
from models.provider import Provider
from models.claim import Claim
from models.analysis_run import AnalysisRun


class AnalyticsService:
    """
    Computes dataset analytics, exposure metrics, and frontend-ready graph datasets
    from the database.
    """

    def get_summary(self, run_id: str | None = None) -> dict[str, Any]:
        """
        Return comprehensive dataset-derived analytics summary.
        """
        with get_db() as db:
            p_query = db.query(Provider)
            c_query = db.query(Claim)

            if run_id:
                p_query = p_query.filter(Provider.analysis_run_id == run_id)
                c_query = c_query.filter(Claim.analysis_run_id == run_id)

            total_providers = p_query.count()
            total_claims = c_query.count()

            # Unique beneficiaries
            total_bene = c_query.with_entities(func.count(func.distinct(Claim.beneficiary_id))).scalar() or 0

            # Risk counts
            low_count = p_query.filter(Provider.risk_level == "Low").count()
            med_count = p_query.filter(Provider.risk_level == "Medium").count()
            high_count = p_query.filter(Provider.risk_level == "High").count()
            crit_count = p_query.filter(Provider.risk_level == "Critical").count()

            # Total reimbursement
            total_reimb = c_query.with_entities(func.sum(Claim.reimbursement_amount)).scalar() or 0.0

            avg_claim_reimb = (
                total_reimb / total_claims
                if total_claims > 0
                else 0.0
            )

            avg_provider_claims = (
                total_claims / total_providers
                if total_providers > 0
                else 0.0
            )

            high_risk_pct = (
                ((high_count + crit_count) / total_providers) * 100.0
                if total_providers > 0
                else 0.0
            )

            # Averages across providers
            avg_prov_avg_reimb = (
                p_query.with_entities(func.avg(Provider.average_reimbursement)).scalar() or 0.0
            )
            avg_prov_inpatient_share = (
                p_query.with_entities(func.avg(Provider.inpatient_share)).scalar() or 0.0
            )
            avg_prov_inpatient_claims = avg_provider_claims * avg_prov_inpatient_share

            # Legacy compatibility
            fraud_flagged = high_count + crit_count
            not_flagged = low_count + med_count
            fraud_rate = (fraud_flagged / total_providers) if total_providers > 0 else 0.0

            return {
                "total_claims": total_claims,
                "total_providers": total_providers,
                "total_beneficiaries": total_bene,
                "low_risk": low_count,
                "medium_risk": med_count,
                "high_risk": high_count,
                "critical_risk": crit_count,
                "total_reimbursement": round(float(total_reimb), 2),
                "average_claim_reimbursement": round(float(avg_claim_reimb), 2),
                "average_provider_claims": round(float(avg_provider_claims), 1),
                "high_risk_percentage": round(float(high_risk_pct), 1),
                # Legacy fields for existing frontend pages
                "fraud_flagged": fraud_flagged,
                "not_flagged": not_flagged,
                "fraud_rate": round(float(fraud_rate), 4),
                "threshold": 0.5,
                "average_provider_average_reimbursement": round(float(avg_prov_avg_reimb), 2),
                "average_provider_inpatient_claims": round(float(avg_prov_inpatient_claims), 1),
            }

    def get_charts(self, run_id: str | None = None) -> dict[str, Any]:
        """
        Return frontend-ready graph datasets for Recharts components.
        """
        with get_db() as db:
            p_query = db.query(Provider)
            c_query = db.query(Claim)

            if run_id:
                p_query = p_query.filter(Provider.analysis_run_id == run_id)
                c_query = c_query.filter(Claim.analysis_run_id == run_id)

            providers = p_query.all()
            claims = c_query.all()

            # 1. Risk Distribution
            low_count = sum(1 for p in providers if p.risk_level == "Low")
            med_count = sum(1 for p in providers if p.risk_level == "Medium")
            high_count = sum(1 for p in providers if p.risk_level == "High")
            crit_count = sum(1 for p in providers if p.risk_level == "Critical")

            risk_distribution = [
                {"name": "Low", "value": low_count},
                {"name": "Medium", "value": med_count},
                {"name": "High", "value": high_count},
                {"name": "Critical", "value": crit_count},
            ]

            # 2. Reimbursement by Risk Level
            reimb_by_risk_dict = {"Low": 0.0, "Medium": 0.0, "High": 0.0, "Critical": 0.0}
            for p in providers:
                level = p.risk_level if p.risk_level in reimb_by_risk_dict else "Low"
                reimb_by_risk_dict[level] += float(p.total_reimbursement or 0.0)

            reimbursement_by_risk = [
                {"risk": "Low", "amount": round(reimb_by_risk_dict["Low"], 2)},
                {"risk": "Medium", "amount": round(reimb_by_risk_dict["Medium"], 2)},
                {"risk": "High", "amount": round(reimb_by_risk_dict["High"], 2)},
                {"risk": "Critical", "amount": round(reimb_by_risk_dict["Critical"], 2)},
            ]

            # 3. Claims by Type
            inpatient_claims = sum(1 for c in claims if str(c.claim_type).lower() == "inpatient")
            outpatient_claims = len(claims) - inpatient_claims

            claims_by_type = [
                {"name": "Inpatient", "value": inpatient_claims},
                {"name": "Outpatient", "value": outpatient_claims},
            ]

            # 4. Top Risky Providers
            sorted_by_risk = sorted(providers, key=lambda p: float(p.risk_score or 0.0), reverse=True)[:10]
            top_risky_providers = [
                {
                    "provider_id": p.provider_id,
                    "provider_name": p.provider_name,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "total_claims": p.total_claims,
                    "total_reimbursement": p.total_reimbursement,
                    "average_reimbursement": p.average_reimbursement,
                }
                for p in sorted_by_risk
            ]

            # 5. Top Providers by Total Reimbursement
            sorted_by_reimb = sorted(providers, key=lambda p: float(p.total_reimbursement or 0.0), reverse=True)[:10]
            top_providers_by_reimbursement = [
                {
                    "provider_id": p.provider_id,
                    "provider_name": p.provider_name,
                    "total_reimbursement": p.total_reimbursement,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                }
                for p in sorted_by_reimb
            ]

            # 6. Reimbursement Distribution histogram brackets
            reimb_buckets = {"< $10k": 0, "$10k - $50k": 0, "$50k - $100k": 0, "$100k - $500k": 0, "> $500k": 0}
            for p in providers:
                amt = float(p.total_reimbursement or 0.0)
                if amt < 10000:
                    reimb_buckets["< $10k"] += 1
                elif amt < 50000:
                    reimb_buckets["$10k - $50k"] += 1
                elif amt < 100000:
                    reimb_buckets["$50k - $100k"] += 1
                elif amt < 500000:
                    reimb_buckets["$100k - $500k"] += 1
                else:
                    reimb_buckets["> $500k"] += 1

            reimbursement_distribution = [
                {"bracket": k, "count": v} for k, v in reimb_buckets.items()
            ]

            return {
                "risk_distribution": risk_distribution,
                "reimbursement_by_risk": reimbursement_by_risk,
                "claims_by_type": claims_by_type,
                "top_risky_providers": top_risky_providers,
                "top_providers_by_reimbursement": top_providers_by_reimbursement,
                "reimbursement_distribution": reimbursement_distribution,
            }