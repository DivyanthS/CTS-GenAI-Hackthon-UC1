import type { CaseStatus, Provider, RiskLevel } from "@/types";

const levelFor = (score: number): RiskLevel =>
  score >= 90 ? "Critical" : score >= 75 ? "High" : score >= 50 ? "Medium" : "Low";

const seeds: [string, number, number, number, number][] = [
  ["PRV55912", 96, 1284, 846, 12_400_000],
  ["PRV51459", 94, 1102, 731, 9_850_000],
  ["PRV53758", 92, 968, 690, 8_120_000],
  ["PRV52019", 91, 903, 612, 7_640_000],
  ["PRV56104", 89, 874, 588, 6_980_000],
  ["PRV54121", 87, 812, 559, 6_120_000],
  ["PRV50845", 84, 764, 501, 5_460_000],
  ["PRV57733", 81, 688, 470, 4_910_000],
  ["PRV52288", 78, 640, 442, 4_380_000],
  ["PRV53390", 76, 601, 418, 3_970_000],
  ["PRV51127", 68, 545, 389, 3_280_000],
  ["PRV55480", 64, 498, 351, 2_910_000],
  ["PRV56621", 61, 452, 322, 2_540_000],
  ["PRV50098", 57, 411, 298, 2_190_000],
  ["PRV54876", 53, 377, 271, 1_930_000],
  ["PRV52745", 44, 322, 240, 1_540_000],
  ["PRV51902", 38, 288, 214, 1_270_000],
  ["PRV53014", 31, 241, 183, 980_000],
  ["PRV57190", 24, 196, 152, 720_000],
  ["PRV55633", 17, 148, 119, 490_000],
];

export const mockProviders: Provider[] = seeds.map(
  ([id, score, claims, benes, total], i) => ({
    provider_id: id,
    risk_score: score,
    risk_level: levelFor(score),
    claim_count: claims,
    beneficiary_count: benes,
    total_reimbursement: total,
    average_reimbursement: Math.round(total / claims),
    inpatient_claims: Math.round(claims * (0.08 + (i % 5) * 0.02)),
    outpatient_claims: claims - Math.round(claims * (0.08 + (i % 5) * 0.02)),
    status: (["New", "Under Review", "Escalated", "Resolved"] as CaseStatus[])[
      i % 4
    ] as CaseStatus,
  }),
);

export const peerAverages = {
  claim_count: 642,
  average_reimbursement: 5210,
  total_reimbursement: 4_800_000,
  beneficiary_count: 495,
};

export const providerVolumeSeries = [
  { month: "Jan", claims: 78, reimbursement: 720_000 },
  { month: "Feb", claims: 84, reimbursement: 790_000 },
  { month: "Mar", claims: 96, reimbursement: 910_000 },
  { month: "Apr", claims: 103, reimbursement: 985_000 },
  { month: "May", claims: 118, reimbursement: 1_120_000 },
  { month: "Jun", claims: 127, reimbursement: 1_240_000 },
  { month: "Jul", claims: 132, reimbursement: 1_310_000 },
  { month: "Aug", claims: 121, reimbursement: 1_180_000 },
  { month: "Sep", claims: 114, reimbursement: 1_090_000 },
  { month: "Oct", claims: 108, reimbursement: 1_020_000 },
  { month: "Nov", claims: 102, reimbursement: 960_000 },
  { month: "Dec", claims: 101, reimbursement: 945_000 },
];

export const providerRiskFactors = [
  { factor: "Claim volume vs peers", weight: 32 },
  { factor: "Average reimbursement", weight: 26 },
  { factor: "Physician concentration", weight: 17 },
  { factor: "Diagnosis code repetition", weight: 14 },
  { factor: "Short claim duration", weight: 11 },
];
