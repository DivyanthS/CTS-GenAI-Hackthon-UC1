import type { UserRole } from "@/lib/auth";
import type {
  CaseStatus,
  Claim,
  DashboardSummary,
  Investigation,
  Provider,
  RiskLevel,
  RiskResult,
  SchemaField,
  ValidationCheck,
  Explanation,
} from "@/types";

export type ReportType =
  | "executive"
  | "claim"
  | "provider"
  | "investigation"
  | "queue"
  | "data-quality"
  | "analysis-summary";

export interface ReportDefinition {
  type: ReportType;
  title: string;
  description: string;
  /** UI-level gating only. The backend must enforce authorization later. */
  roles: UserRole[];
}

export const REPORT_DEFINITIONS: ReportDefinition[] = [
  {
    type: "executive",
    title: "Enterprise Payment Integrity Overview",
    description: "Portfolio-level risk, workload and top exposure areas for management.",
    roles: ["ADMIN", "EXECUTIVE"],
  },
  {
    type: "analysis-summary",
    title: "Analysis Summary Report",
    description: "Concise management summary of the latest scoring run.",
    roles: ["ADMIN", "EXECUTIVE", "FRAUD_ANALYST"],
  },
  {
    type: "claim",
    title: "Claim Investigation Report",
    description: "Full claim dossier: model evidence, peer deviation and AI explanation.",
    roles: ["ADMIN", "FRAUD_ANALYST", "INVESTIGATOR"],
  },
  {
    type: "provider",
    title: "Provider Risk Assessment Report",
    description: "Provider billing profile, peer comparison and risk drivers.",
    roles: ["ADMIN", "FRAUD_ANALYST", "PROVIDER_REVIEWER"],
  },
  {
    type: "investigation",
    title: "Investigation Case Report",
    description: "Case dossier with audit-style timeline and human decision record.",
    roles: ["ADMIN", "INVESTIGATOR"],
  },
  {
    type: "queue",
    title: "Investigation Queue Summary",
    description: "Filtered queue snapshot with workload distribution.",
    roles: ["ADMIN", "FRAUD_ANALYST", "INVESTIGATOR"],
  },
  {
    type: "data-quality",
    title: "Claims Dataset Quality Report",
    description: "Validation results, schema conformance and recommended actions.",
    roles: ["ADMIN", "FRAUD_ANALYST"],
  },
];

export function reportsForRole(role: UserRole): ReportDefinition[] {
  return REPORT_DEFINITIONS.filter((r) => r.roles.includes(role));
}

export function canAccessReport(role: UserRole, type: ReportType): boolean {
  return REPORT_DEFINITIONS.some((r) => r.type === type && r.roles.includes(role));
}

export interface ReportMetadata {
  report_id: string;
  report_type: ReportType;
  title: string;
  generated_at: string;
  generated_by: string;
  generated_by_role: string;
  filename: string;
  subjects: { label: string; value: string }[];
}

export interface GeneratedReport {
  metadata: ReportMetadata;
  blob: Blob;
  url: string;
  page_count: number;
}

/** Optional traceability identifiers — omitted when the backend has not supplied them. */
export interface Traceability {
  explanation_id?: string | undefined;
  claim_id?: string | undefined;
  model_run_id?: string | undefined;
  generated_at?: string | undefined;
  evidence_used?: string[] | undefined;
}

export interface ClaimReportData {
  claim: Claim;
  // Claim-level RiskResult is not always available; when absent the frontend will
  // explicitly mark claim-level risk as unavailable. Avoid fabricating claim-level scores.
  risk: RiskResult | { available: false; note: string };
  provider?: Provider | undefined;
  // Optional provider-level prediction supplied for traceability in reports
  provider_prediction?: { fraud_probability: number; threshold?: number; decision?: string } | undefined;
  peer?: PeerMetrics | undefined;
  investigation?: Investigation | undefined;
  notes?: { text: string; at: string }[] | undefined;
  decision?: InvestigationDecision | undefined;
  traceability?: Traceability | undefined;
  // Optional explanation assembled by the frontend when claim-level model explanation is not available
  explanation?: Explanation | undefined;
  evidence?: {
    factor: string;
    value: number | null;
    peer_value: number | null;
    difference?: number | null;
    diff_percent?: number | null;
    description?: string;
  }[] | undefined;
}

export interface PeerMetrics {
  claim_count: number;
  beneficiary_count: number;
  average_reimbursement: number;
  total_reimbursement: number;
  inpatient_claims: number;
  outpatient_claims: number;
}

export interface InvestigationDecision {
  decision: string;
  reviewer: string;
  date: string;
  comments?: string | undefined;
}

export interface ProviderReportData {
  provider: Provider;
  peer: PeerMetrics;
  explanation: { summary: string; reasons: string[]; disclaimer: string; model?: string };
  risk_factors: { factor: string; weight: number }[];
  related_cases: Investigation[];
  notes?: string[] | undefined;
}

export interface InvestigationReportData {
  investigation: Investigation;
  claim?: Claim | undefined;
  risk?: RiskResult | undefined;
  timeline: { label: string; detail: string; state: string }[];
  notes?: { text: string; at: string }[] | undefined;
  actions?: string[] | undefined;
  decision?: InvestigationDecision | undefined;
}

export interface QueueFilters {
  risk?: RiskLevel | "All" | undefined;
  claim_type?: string | undefined;
  status?: CaseStatus | "All" | undefined;
  date_range?: string | undefined;
  search?: string | undefined;
}

export interface QueueReportData {
  filters: QueueFilters;
  cases: Investigation[];
}

export interface DashboardReportData {
  summary: DashboardSummary;
  risk_factors: { factor: string; weight: number }[];
  dataset: { file_name: string; rows: number; columns: number; providers: number; beneficiaries: number };
  total_reimbursement: number;
  /** Only present when the backend calculates it. */
  financial_exposure?: number | undefined;
  model?: { name?: string | undefined; version?: string | undefined; run_id?: string | undefined; metrics?: Record<string, number> };
  ai_summary?: string | undefined;
  analyst_notes?: string[] | undefined;
}

export interface DataQualityReportData {
  dataset: {
    file_name: string;
    file_type: string;
    file_size?: string | undefined;
    rows: number;
    columns: number;
  };
  checks: ValidationCheck[];
  schema: SchemaField[];
  /** Undefined when no real calculation exists yet. */
  quality_score?: number | undefined;
  missing_values?: string | undefined;
  duplicates?: string | undefined;
  invalid_values?: string | undefined;
}

export type ReportPayload =
  | { type: "executive"; data: DashboardReportData }
  | { type: "analysis-summary"; data: DashboardReportData }
  | { type: "claim"; data: ClaimReportData }
  | { type: "provider"; data: ProviderReportData }
  | { type: "investigation"; data: InvestigationReportData }
  | { type: "queue"; data: QueueReportData }
  | { type: "data-quality"; data: DataQualityReportData };
