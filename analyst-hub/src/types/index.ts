export type RiskLevel = "Critical" | "High" | "Medium" | "Low";
export type ClaimType = "Inpatient" | "Outpatient";
export type CaseStatus = "New" | "Under Review" | "Escalated" | "Resolved";
export type Prediction = "Potential Fraud" | "Elevated Risk" | "No Elevated Risk";

export interface Evidence {
  factor: string;
  provider_value: number;
  peer_value: number;
  difference: string;
  unit: "currency" | "count" | "percent";
  note?: string;
}

export interface Explanation {
  summary: string;
  reasons: string[];
  disclaimer: string;
  generated_at?: string;
  model?: string;
}

export interface RiskResult {
  claim_id: string;
  provider_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  prediction: Prediction;
  top_risk_factors: string[];
  evidence: Evidence[];
  explanation: Explanation;
}

export interface Claim {
  claim_id: string;
  provider_id: string;
  bene_id: string;
  claim_type: ClaimType;
  reimbursement: number;
  claim_start_date: string;
  claim_end_date: string;
  /** Absent because the current model scores providers, not individual claims. */
  risk_score?: number;
  risk_level?: RiskLevel;
  status?: CaseStatus;
  attending_physician?: string;
  operating_physician?: string;
  diagnosis_codes?: string[];
  procedure_codes?: string[];
}

export interface Provider {
  provider_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  claim_count: number;
  beneficiary_count: number;
  total_reimbursement: number;
  average_reimbursement: number;
  inpatient_claims: number;
  outpatient_claims: number;
  status: CaseStatus;
}

export interface Investigation {
  case_id: string;
  claim_id: string;
  provider_id: string;
  risk_score: number;
  priority: RiskLevel;
  status: CaseStatus;
  created_at: string;
  assigned_to: string;
}

export interface DashboardSummary {
  total_claims: number;
  providers: number;
  beneficiaries: number;
  high_risk_cases: number;
  risk_distribution: { level: RiskLevel; count: number }[];
  claim_type_distribution: { type: ClaimType; count: number }[];
  reimbursement_by_risk: { level: RiskLevel; amount: number }[];
  top_risky_providers: Provider[];
  recent_cases: Investigation[];
}

export interface DatasetInfo {
  file_name: string;
  file_size: string;
  rows: number;
  columns: number;
  providers: number;
  beneficiaries: number;
  status: "uploaded" | "validated" | "failed";
}

export interface ValidationCheck {
  name: string;
  status: "pass" | "warn" | "fail";
  detail: string;
}

export interface SchemaField {
  field: string;
  type: string;
  required: boolean;
  status: "pass" | "warn" | "fail";
  note: string;
}
