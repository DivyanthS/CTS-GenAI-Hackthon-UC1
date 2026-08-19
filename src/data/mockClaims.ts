import type { CaseStatus, Claim, ClaimType, RiskLevel } from "@/types";
import { mockProviders } from "./mockProviders";

const levelFor = (score: number): RiskLevel =>
  score >= 90 ? "Critical" : score >= 75 ? "High" : score >= 50 ? "Medium" : "Low";

const statuses: CaseStatus[] = ["New", "Under Review", "Escalated", "Resolved"];
const physicians = [
  "PHY330576",
  "PHY412132",
  "PHY214980",
  "PHY559011",
  "PHY108224",
  "PHY773401",
];
const diagnoses = ["I5030", "E1140", "N1830", "J9601", "M1710", "R0602", "Z9861"];
const procedures = ["3893", "8154", "0066", "9904", "4513"];

function pad(n: number, len = 3) {
  return String(n).padStart(len, "0");
}

export const mockClaims: Claim[] = Array.from({ length: 96 }, (_, i) => {
  const provider = mockProviders[i % mockProviders.length]!;
  const drift = ((i * 7) % 13) - 6;
  const score = Math.max(6, Math.min(98, provider.risk_score + drift));
  const type: ClaimType = i % 5 === 0 ? "Inpatient" : "Outpatient";
  const base = type === "Inpatient" ? 18_000 : 1_400;
  const startDay = (i % 27) + 1;
  const lengthDays = type === "Inpatient" ? (i % 6) + 2 : 1;
  return {
    claim_id: `CLM${pad(i + 1)}`,
    provider_id: provider.provider_id,
    bene_id: `BENE${pad(11000 + i * 13, 5)}`,
    claim_type: type,
    reimbursement: base + ((i * 971) % 9000),
    claim_start_date: `2024-0${(i % 9) + 1}-${pad(startDay, 2)}`,
    claim_end_date: `2024-0${(i % 9) + 1}-${pad(startDay + lengthDays, 2)}`,
    risk_score: score,
    risk_level: levelFor(score),
    status: statuses[i % statuses.length]!,
    attending_physician: physicians[i % physicians.length]!,
    operating_physician: physicians[(i + 2) % physicians.length]!,
    diagnosis_codes: [
      diagnoses[i % diagnoses.length]!,
      diagnoses[(i + 3) % diagnoses.length]!,
      diagnoses[(i + 5) % diagnoses.length]!,
    ],
    procedure_codes: [procedures[i % procedures.length]!],
  } satisfies Claim;
});

// Anchor case used across the documented investigator journey.
mockClaims[0] = {
  ...mockClaims[0]!,
  claim_id: "CLM001",
  provider_id: "PRV55912",
  bene_id: "BENE11001",
  claim_type: "Inpatient",
  reimbursement: 26_000,
  risk_score: 96,
  risk_level: "Critical",
  status: "New",
  claim_start_date: "2024-03-04",
  claim_end_date: "2024-03-11",
};
