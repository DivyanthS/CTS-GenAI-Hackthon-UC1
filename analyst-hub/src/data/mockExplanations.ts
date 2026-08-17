import type { Evidence, Explanation, RiskResult } from "@/types";
import { mockClaims } from "./mockClaims";
import { peerAverages } from "./mockProviders";

export const DISCLAIMER =
  "Risk assessment is not a determination of fraud. This explanation summarizes model-derived signals and supporting evidence for investigator review.";

export function buildEvidence(
  claimReimbursement: number,
  providerClaims: number,
  providerAvgReimbursement: number,
): Evidence[] {
  const pct = (a: number, b: number) => `${a >= b ? "+" : ""}${Math.round(((a - b) / b) * 100)}%`;
  return [
    {
      factor: "Provider Claim Volume",
      provider_value: providerClaims,
      peer_value: peerAverages.claim_count,
      difference: pct(providerClaims, peerAverages.claim_count),
      unit: "count",
      note: "Submitted claim count over the observation window compared with providers of similar specialty and size.",
    },
    {
      factor: "Average Reimbursement",
      provider_value: providerAvgReimbursement,
      peer_value: peerAverages.average_reimbursement,
      difference: pct(providerAvgReimbursement, peerAverages.average_reimbursement),
      unit: "currency",
      note: "Mean reimbursed amount per claim for this provider versus the peer group mean.",
    },
    {
      factor: "Claim Reimbursement",
      provider_value: claimReimbursement,
      peer_value: peerAverages.average_reimbursement,
      difference: pct(claimReimbursement, peerAverages.average_reimbursement),
      unit: "currency",
      note: "Reimbursed amount on this specific claim relative to the peer-group average claim.",
    },
  ];
}

export function buildExplanation(providerId: string, level: string): Explanation {
  return {
    summary:
      level === "Low"
        ? `This claim did not receive an elevated risk score. Provider ${providerId} bills within the range observed across comparable providers, and no individual feature contributed a material amount to the model output.`
        : `This claim received a ${level.toLowerCase()}-risk score because provider ${providerId}'s billing patterns differ substantially from comparable providers. The provider has significantly higher claim volume and reimbursement levels than the peer group, and the reimbursed amount on this claim sits above the peer distribution for the same claim type.`,
    reasons: [
      "Provider claim volume exceeds the peer-group average for the observation window.",
      "Average reimbursement per claim is materially above the peer-group mean.",
      "This claim's reimbursed amount is high relative to comparable claims of the same type.",
    ],
    disclaimer: DISCLAIMER,
    generated_at: "2024-03-12T09:41:00Z",
    model: "explainer-v1 (evidence-grounded)",
  };
}

export function buildRiskResult(claimId: string): RiskResult | undefined {
  const claim = mockClaims.find((c) => c.claim_id === claimId);
  if (!claim) return undefined;
  const providerClaims = 1284;
  const providerAvg = 9650;
  return {
    claim_id: claim.claim_id,
    provider_id: claim.provider_id,
    risk_score: claim.risk_score ?? 0,
    risk_level: claim.risk_level ?? "Low",
    prediction:
      (claim.risk_score ?? 0) >= 90
        ? "Potential Fraud"
        : (claim.risk_score ?? 0) >= 50
          ? "Elevated Risk"
          : "No Elevated Risk",
    top_risk_factors: [
      "Provider claim volume",
      "Average reimbursement",
      "Claim reimbursement",
    ],
    evidence: buildEvidence(claim.reimbursement, providerClaims, providerAvg),
    explanation: buildExplanation(claim.provider_id, claim.risk_level ?? "Low"),
  };
}
