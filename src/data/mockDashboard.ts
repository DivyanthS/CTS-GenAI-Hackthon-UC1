import type { DashboardSummary, SchemaField, ValidationCheck } from "@/types";
import { mockProviders } from "./mockProviders";
import { mockInvestigations } from "./mockInvestigations";

export const DATASET_CONTEXT = {
  file_name: "All_Datasets_Combined.csv",
  rows: 558_211,
  columns: 117,
  providers: 5_410,
  beneficiaries: 138_556,
  inpatient: 40_474,
  outpatient: 517_737,
};

export const mockDashboard: DashboardSummary = {
  total_claims: DATASET_CONTEXT.rows,
  providers: DATASET_CONTEXT.providers,
  beneficiaries: DATASET_CONTEXT.beneficiaries,
  high_risk_cases: 1_842,
  risk_distribution: [
    { level: "Critical", count: 486 },
    { level: "High", count: 1_356 },
    { level: "Medium", count: 12_704 },
    { level: "Low", count: 543_665 },
  ],
  claim_type_distribution: [
    { type: "Inpatient", count: DATASET_CONTEXT.inpatient },
    { type: "Outpatient", count: DATASET_CONTEXT.outpatient },
  ],
  reimbursement_by_risk: [
    { level: "Critical", amount: 48_200_000 },
    { level: "High", amount: 96_500_000 },
    { level: "Medium", amount: 212_400_000 },
    { level: "Low", amount: 684_900_000 },
  ],
  top_risky_providers: mockProviders.slice(0, 6),
  recent_cases: mockInvestigations.slice(0, 6),
};

export const validationChecks: ValidationCheck[] = [
  { name: "File format", status: "pass", detail: "CSV parsed with 117 delimited columns" },
  { name: "Required fields", status: "pass", detail: "All 12 required fields present" },
  { name: "Claim IDs", status: "pass", detail: "558,211 non-null ClaimID values" },
  { name: "Provider IDs", status: "pass", detail: "5,410 unique Provider values" },
  { name: "Beneficiary IDs", status: "pass", detail: "138,556 unique BeneID values" },
  { name: "Duplicate Claim IDs", status: "pass", detail: "0 duplicates detected" },
  { name: "Data types", status: "warn", detail: "3 date columns coerced from string" },
  { name: "Missing values", status: "warn", detail: "OperatingPhysician null in 61.4% of rows" },
];

export const schemaFields: SchemaField[] = [
  { field: "ClaimID", type: "string", required: true, status: "pass", note: "Primary key" },
  { field: "Provider", type: "string", required: true, status: "pass", note: "5,410 unique" },
  { field: "BeneID", type: "string", required: true, status: "pass", note: "138,556 unique" },
  { field: "ClaimType", type: "categorical", required: true, status: "pass", note: "Inpatient / Outpatient" },
  { field: "ClaimStartDt", type: "date", required: true, status: "warn", note: "Coerced from string" },
  { field: "ClaimEndDt", type: "date", required: true, status: "warn", note: "Coerced from string" },
  { field: "InscClaimAmtReimbursed", type: "numeric", required: true, status: "pass", note: "No negatives" },
  { field: "AttendingPhysician", type: "string", required: true, status: "pass", note: "1.2% null" },
  { field: "OperatingPhysician", type: "string", required: false, status: "warn", note: "61.4% null" },
  { field: "PotentialFraud", type: "boolean", required: false, status: "pass", note: "Provider-level label" },
];

export const analysisStages = [
  "Dataset loaded",
  "Features prepared",
  "Provider patterns calculated",
  "ML model executed",
  "Risk scores generated",
  "Evidence generated",
  "LLM explanations generated",
];

export const topRiskFactorsChart = [
  { factor: "Claim volume vs peers", weight: 32 },
  { factor: "Avg reimbursement", weight: 26 },
  { factor: "Physician concentration", weight: 17 },
  { factor: "Diagnosis repetition", weight: 14 },
  { factor: "Short claim duration", weight: 11 },
];

export const peerDeviationScatter = mockProviders.map((p) => ({
  provider: p.provider_id,
  volumeDeviation: Math.round(((p.claim_count - 642) / 642) * 100),
  reimbursementDeviation: Math.round(((p.average_reimbursement - 5210) / 5210) * 100),
  risk: p.risk_score,
}));
