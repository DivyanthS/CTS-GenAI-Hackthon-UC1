import type { CaseStatus, Investigation, RiskLevel } from "@/types";
import { mockClaims } from "./mockClaims";

const analysts = ["A. Whitfield", "R. Nandakumar", "J. Okafor", "M. Petrova", "S. Lindqvist"];
const statuses: CaseStatus[] = ["New", "Under Review", "Escalated", "Resolved"];

const priorityFor = (score: number): RiskLevel =>
  score >= 90 ? "Critical" : score >= 75 ? "High" : score >= 50 ? "Medium" : "Low";

export const mockInvestigations: Investigation[] = mockClaims
  .slice(0, 48)
  .map((claim, i) => ({
    case_id: `INV-${String(i + 1).padStart(3, "0")}`,
    claim_id: claim.claim_id,
    provider_id: claim.provider_id,
    risk_score: claim.risk_score ?? 0,
    priority: priorityFor(claim.risk_score ?? 0),
    status: statuses[i % statuses.length]!,
    created_at: `2024-0${(i % 9) + 1}-${String((i % 27) + 1).padStart(2, "0")}`,
    assigned_to: analysts[i % analysts.length]!,
  }));

mockInvestigations[0] = {
  ...mockInvestigations[0]!,
  case_id: "INV-001",
  claim_id: "CLM001",
  provider_id: "PRV55912",
  risk_score: 96,
  priority: "Critical",
  status: "New",
  created_at: "2024-03-12",
  assigned_to: "A. Whitfield",
};

export const caseTimeline = [
  { label: "Case Created", detail: "Case generated from risk analysis run #4821", state: "done" },
  { label: "Risk Detected", detail: "ML model risk score 96% — Critical", state: "done" },
  { label: "Reviewed", detail: "Awaiting investigator review", state: "pending" },
  { label: "Escalated", detail: "Not yet escalated", state: "pending" },
  { label: "Resolved", detail: "Not yet resolved", state: "pending" },
] as const;
