from __future__ import annotations

from flask import Blueprint, jsonify, request
from utils.json_utils import make_json_safe
from services.claim_data import ClaimDataService
from services.evidence.claim_evidence_service import ClaimEvidenceService


def create_claim_routes(
    claim_data_service: ClaimDataService,
    claim_evidence_service: ClaimEvidenceService,
) -> Blueprint:
    claims_bp = Blueprint("claims", __name__, url_prefix="/api/v1")

    @claims_bp.get("/claims")
    def get_claims():
        """
        Return paginated claim records.
        Query params: page, page_size, provider_id, claim_type, search, run_id
        """
        try:
            page = request.args.get("page", default=1, type=int)
            page_size = request.args.get("page_size", default=50, type=int)
            provider_id = request.args.get("provider_id", default=None, type=str)
            claim_type = request.args.get("claim_type", default=None, type=str)
            search = request.args.get("search", default=None, type=str)
            run_id = request.args.get("run_id", default=None, type=str)

            claims, total = claim_data_service.get_claims(
                page=page,
                page_size=page_size,
                provider_id=provider_id,
                claim_type=claim_type,
                search=search,
                run_id=run_id,
            )

            total_pages = (
                (total + page_size - 1) // page_size
                if total > 0
                else 0
            )

            return jsonify(
                make_json_safe(
                    {
                        "page": page,
                        "page_size": page_size,
                        "provider_id": provider_id,
                        "total": total,
                        "total_pages": total_pages,
                        "claims": claims,
                    }
                )
            ), 200

        except ValueError as exc:
            return jsonify({
                "error": "INVALID_PAGINATION",
                "message": str(exc),
            }), 400

        except Exception as exc:
            print(f"Claims API error: {exc}")
            return jsonify({
                "error": "CLAIMS_ERROR",
                "message": f"Unable to retrieve claims: {str(exc)}",
            }), 500

    @claims_bp.get("/claims/<claim_id>")
    def get_claim(claim_id: str):
        """
        Return a single claim record.
        """
        try:
            claim = claim_data_service.get_claim(claim_id)
            return jsonify(
                make_json_safe(
                    {
                        "claim": claim,
                    }
                )
            ), 200

        except KeyError:
            return jsonify({
                "error": "CLAIM_NOT_FOUND",
                "message": f"Claim '{claim_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"Claim API error for {claim_id}: {exc}")
            return jsonify({
                "error": "CLAIM_ERROR",
                "message": f"Unable to retrieve claim: {str(exc)}",
            }), 500

    @claims_bp.get("/claims/<claim_id>/explanation")
    def get_claim_explanation(claim_id: str):
        """
        Return dataset-grounded context and risk evidence for a specific claim.
        """
        try:
            explanation = claim_evidence_service.get_explanation(claim_id)
            return jsonify(make_json_safe(explanation)), 200

        except KeyError:
            return jsonify({
                "error": "CLAIM_NOT_FOUND",
                "message": f"Claim '{claim_id}' was not found.",
            }), 404

        except Exception as exc:
            print(f"Claim explanation error for {claim_id}: {exc}")
            return jsonify({
                "error": "EXPLANATION_ERROR",
                "message": f"Unable to generate claim explanation: {str(exc)}",
            }), 500

    return claims_bp
