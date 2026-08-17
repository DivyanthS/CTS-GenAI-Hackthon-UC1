import type { AuthUser } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/auth";
import { ReportDoc, currency, formatDate, formatDateTime, num } from "@/lib/pdf/reportDoc";
import type {
  ClaimReportData,
  DashboardReportData,
  DataQualityReportData,
  GeneratedReport,
  InvestigationReportData,
  PeerMetrics,
  ProviderReportData,
  QueueReportData,
  ReportMetadata,
  ReportPayload,
  ReportType,
} from "@/types/reports";
import type { Investigation, Provider } from "@/types";
import { getClaim, getProviders, getAnalytics, predictProvider, getProvider, mapBackendClaim } from "@/services/api";
import { getDashboardSummary, validateDataset, getInvestigations, getInvestigation, getRiskResult } from "@/services/mockApi";
import { DATASET_CONTEXT, topRiskFactorsChart } from "@/data/mockDashboard";
import { caseTimeline } from "@/data/mockInvestigations";
import { peerAverages } from "@/data/mockProviders";
import { buildExplanation } from "@/data/mockExplanations";

/**
 * Frontend reporting abstraction.
 *
 * Today every report is composed from the mock API and rendered in the browser.
 * When the Flask backend is ready it can serve the data (or the finished PDF)
 * from these endpoints without any change to the calling components:
 *
 *   GET  /api/reports/claim/{claim_id}
 *   GET  /api/reports/provider/{provider_id}
 *   GET  /api/reports/investigation/{case_id}
 *   GET  /api/reports/dashboard
 *   GET  /api/reports/data-quality
 *   POST /api/reports/generate     -> application/pdf
 */
export const REPORT_ENDPOINTS = {
  claim: (id: string) => `/reports/claim/${id}`,
  provider: (id: string) => `/reports/provider/${id}`,
  investigation: (id: string) => `/reports/investigation/${id}`,
  dashboard: "/reports/dashboard",
  dataQuality: "/reports/data-quality",
  generate: "/reports/generate",
};

const DISCLAIMER_GENERAL =
  "Risk assessments represent model-generated signals and do not constitute a determination of fraud.";
const DISCLAIMER_CASE =
  "FraudGuard AI provides risk signals to support payment-integrity investigation. A high-risk score does not establish fraud. Final determinations require human review and appropriate investigation.";
const THRESHOLD_NOTE =
  "Risk bands (Critical 90–100, High 75–89, Medium 50–74, Low 0–49) are reporting thresholds used for presentation. They are not presented as statistically validated operational thresholds.";

const TYPE_TITLES: Record<ReportType, string> = {
  executive: "Enterprise Payment Integrity Overview",
  "analysis-summary": "Analysis Summary Report",
  claim: "Claim Investigation Report",
  provider: "Provider Risk Assessment Report",
  investigation: "Investigation Case Report",
  queue: "Investigation Queue Summary",
  "data-quality": "Claims Dataset Quality Report",
};

const TYPE_CODES: Record<ReportType, string> = {
  executive: "EXE",
  "analysis-summary": "ANL",
  claim: "CLM",
  provider: "PRV",
  investigation: "INV",
  queue: "QUE",
  "data-quality": "DQR",
};

let sequence = 0;

export function createReportId(type: ReportType, at: Date) {
  sequence += 1;
  const stamp = formatDate(at).replace(/-/g, "");
  return `FG-${TYPE_CODES[type]}-${stamp}-${String(sequence).padStart(3, "0")}`;
}

function filenameFor(type: ReportType, at: Date, subject?: string) {
  const date = formatDate(at);
  const clean = (s: string) => s.replace(/[^A-Za-z0-9]/g, "");
  switch (type) {
    case "claim":
      return `FraudGuard_Claim_${clean(subject ?? "")}_Risk_Report.pdf`;
    case "provider":
      return `FraudGuard_Provider_${clean(subject ?? "")}_Risk_Report.pdf`;
    case "investigation":
      return `FraudGuard_Investigation_${clean(subject ?? "")}_Report.pdf`;
    case "queue":
      return `FraudGuard_Investigation_Queue_Report_${date}.pdf`;
    case "data-quality":
      return `FraudGuard_Data_Quality_Report_${date}.pdf`;
    case "analysis-summary":
      return `FraudGuard_Analysis_Summary_Report_${date}.pdf`;
    default:
      return `FraudGuard_Executive_Risk_Report_${date}.pdf`;
  }
}

function subjectOf(payload: ReportPayload): { subject?: string; facts: { label: string; value: string }[] } {
  switch (payload.type) {
    case "claim":
      return {
        subject: payload.data.claim.claim_id,
        facts: [
          { label: "Claim", value: payload.data.claim.claim_id },
          { label: "Provider", value: payload.data.claim.provider_id },
          ...(payload.data.investigation
            ? [{ label: "Case", value: payload.data.investigation.case_id }]
            : []),
        ],
      };
    case "provider":
      return {
        subject: payload.data.provider.provider_id,
        facts: [{ label: "Provider", value: payload.data.provider.provider_id }],
      };
    case "investigation":
      return {
        subject: payload.data.investigation.case_id,
        facts: [
          { label: "Case", value: payload.data.investigation.case_id },
          { label: "Claim", value: payload.data.investigation.claim_id },
          { label: "Provider", value: payload.data.investigation.provider_id },
        ],
      };
    case "queue":
      return { facts: [{ label: "Cases", value: num(payload.data.cases.length) }] };
    case "data-quality":
      return { facts: [{ label: "Dataset", value: payload.data.dataset.file_name }] };
    default:
      return { facts: [{ label: "Dataset", value: payload.data.dataset.file_name }] };
  }
}

// ---------------------------------------------------------------- collectors

export const peerMetrics: PeerMetrics = {
  claim_count: peerAverages.claim_count,
  beneficiary_count: peerAverages.beneficiary_count,
  average_reimbursement: peerAverages.average_reimbursement,
  total_reimbursement: 0,
  inpatient_claims: 0,
  outpatient_claims: 0,
};

function peersFrom(providers: Provider[]): PeerMetrics {
  const avg = (fn: (p: Provider) => number) =>
    providers.length ? Math.round(providers.reduce((s, p) => s + fn(p), 0) / providers.length) : 0;
  if (!providers.length) return peerMetrics;
  return {
    claim_count: avg((p) => p.claim_count),
    beneficiary_count: avg((p) => p.beneficiary_count),
    average_reimbursement: avg((p) => p.average_reimbursement),
    total_reimbursement: avg((p) => p.total_reimbursement),
    inpatient_claims: avg((p) => p.inpatient_claims),
    outpatient_claims: avg((p) => p.outpatient_claims),
  };
}

export async function collectDashboardReportData(): Promise<DashboardReportData> {
  const summary = await getDashboardSummary();
  const total = summary.reimbursement_by_risk.reduce((s, r) => s + r.amount, 0);
  return {
    summary,
    risk_factors: topRiskFactorsChart,
    dataset: {
      file_name: DATASET_CONTEXT.file_name,
      rows: DATASET_CONTEXT.rows,
      columns: DATASET_CONTEXT.columns,
      providers: DATASET_CONTEXT.providers,
      beneficiaries: DATASET_CONTEXT.beneficiaries,
    },
    total_reimbursement: total,
    // financial_exposure intentionally omitted — no validated backend calculation yet.
    model: { name: "FraudGuard ensemble risk model", run_id: "RUN-4821" },
    ai_summary:
      "Model output concentrates risk in a small number of high-volume providers whose reimbursement per claim sits well above their peer cohort. The explanation layer attributes most flagged claims to claim-volume and reimbursement deviation rather than to any single procedure or diagnosis pattern.",
  };
}

export async function collectClaimReportData(claimId: string): Promise<ClaimReportData | null> {
  const [claim, providersResp, analytics] = await Promise.all([
    getClaim(claimId),
    getProviders(),
    getAnalytics().catch(() => null),
  ]);

  if (!claim) return null;

  const providers = providersResp.providers ?? [];
  const provider = providers.find((p) => p.provider_id === String(claim.Provider));

  // Provider-level prediction (best-effort) — do not treat as claim-level score
  let providerPrediction: { fraud_probability: number; threshold?: number; decision?: string } | null = null;
  try {
    if (provider?.provider_id) {
      const pred = await predictProvider(provider.provider_id).catch(() => null);
      if (pred && typeof pred.fraud_probability === "number") {
        providerPrediction = {
          fraud_probability: pred.fraud_probability,
          threshold: pred.threshold,
          decision: pred.decision,
        };
      }
    }
  } catch (e) {
    providerPrediction = null;
  }

  // Build conservative risk object — do NOT fabricate claim-level model outputs
  const risk = {
    available: false,
    note: "Claim-level risk not available",
  } as const;

  // Build simple evidence set based on available analytics and provider aggregates
  const evidence: { factor: string; value: number | null; peer_value: number | null; difference?: number | null; diff_percent?: number | null; description?: string }[] = [];

  try {
    const avgClaimReimb = analytics?.average_claim_reimbursement ?? null;
    const claimReimb = Number(claim.InscClaimAmtReimbursed ?? null) || null;

    if (claimReimb !== null && avgClaimReimb !== null) {
      const diff = claimReimb - avgClaimReimb;
      const diffPct = avgClaimReimb !== 0 ? (diff / avgClaimReimb) * 100 : null;
      evidence.push({
        factor: "Claim reimbursement",
        value: claimReimb,
        peer_value: avgClaimReimb,
        difference: diff,
        diff_percent: diffPct,
        description: "Claim reimbursement compared with dataset average",
      });
    }

    const providerAvg = provider?.average_reimbursement ?? provider?.average_reimbursement ?? null;
    const providerClaimCount = provider?.claim_count ?? null;
    const avgProviderClaims = analytics?.average_provider_claims ?? null;

    if (providerAvg !== null && avgClaimReimb !== null) {
      const diff = providerAvg - avgClaimReimb;
      const diffPct = avgClaimReimb !== 0 ? (diff / avgClaimReimb) * 100 : null;
      evidence.push({
        factor: "Provider avg reimbursement",
        value: providerAvg,
        peer_value: avgClaimReimb,
        difference: diff,
        diff_percent: diffPct,
        description: "Provider average reimbursement vs dataset average",
      });
    }

    if (providerClaimCount !== null && avgProviderClaims !== null) {
      const diff = providerClaimCount - avgProviderClaims;
      const diffPct = avgProviderClaims !== 0 ? (diff / avgProviderClaims) * 100 : null;
      evidence.push({
        factor: "Provider claim volume",
        value: providerClaimCount,
        peer_value: avgProviderClaims,
        difference: diff,
        diff_percent: diffPct,
        description: "Provider claim count compared with average provider",
      });
    }
  } catch (e) {
    // swallow — evidence is optional for the report
  }

  // Build a simple explanation from the strongest evidence items (top 3)
  let explanation: { summary: string; reasons: string[]; disclaimer: string } | undefined = undefined;
  if (evidence.length) {
    const top = evidence
      .slice()
      .sort((a, b) => Math.abs(Number(b.value ?? 0) - Number(b.peer_value ?? 0)) - Math.abs(Number(a.value ?? 0) - Number(a.peer_value ?? 0)))
      .slice(0, 3);
    const reasons = top.map((e) => {
      const pv = Number(e.peer_value ?? 0);
      const v = Number(e.value ?? 0);
      const pct = pv !== 0 ? (((v - pv) / pv) * 100).toFixed(1) : "Not available";
      return `${e.factor} is ${pct}% ${v > pv ? "above" : "below"} the peer average.`;
    });
    explanation = {
      summary: "Claim-level model scoring is not available. The following dataset-derived signals provide context for investigator review.",
      reasons,
      disclaimer: "Risk assessments represent model-generated signals and do not constitute a determination of fraud.",
    };
  }

  return {
    claim: mapBackendClaim(claim),
    risk,
    provider,
    peer: peersFrom(providers),
    evidence,
    explanation,
    provider_prediction: providerPrediction ?? undefined,
    traceability: {
      claim_id: claim.ClaimID,
      evidence_used: evidence.map((e) => e.factor),
    },
  };
}

export async function collectProviderReportData(providerId: string): Promise<ProviderReportData | null> {
  const [provider, providers, cases] = await Promise.all([
    getProvider(providerId),
    getProviders(),
    getInvestigations(),
  ]);
  if (!provider) return null;
  return {
    provider,
    peer: peersFrom(providers.providers),
    explanation: buildExplanation(provider.provider_id, provider.risk_level),
    risk_factors: topRiskFactorsChart,
    related_cases: cases.filter((c: Investigation) => c.provider_id === provider.provider_id),
  };
}

export async function collectInvestigationReportData(
  caseId: string,
  extras: { notes?: { text: string; at: string }[]; status?: string } = {},
): Promise<InvestigationReportData | null> {
  const investigation = await getInvestigation(caseId);
  if (!investigation) return null;
  const [claim, risk] = await Promise.all([
    getClaim(investigation.claim_id),
    getRiskResult(investigation.claim_id),
  ]);
  return {
    investigation: extras.status
      ? ({ ...investigation, status: extras.status } as Investigation)
      : investigation,
    claim: claim ? mapBackendClaim(claim) : undefined,
    risk: risk ?? undefined,
    timeline: caseTimeline.map((t) => ({ ...t })),
    notes: extras.notes ?? [],
    actions: [],
  };
}

export async function collectDataQualityReportData(): Promise<DataQualityReportData> {
  const { checks, schema } = await validateDataset();
  return {
    dataset: {
      file_name: DATASET_CONTEXT.file_name,
      file_type: "CSV",
      rows: DATASET_CONTEXT.rows,
      columns: DATASET_CONTEXT.columns,
    },
    checks,
    schema,
    // quality_score omitted — no backend-calculated score available yet.
    missing_values: checks.find((c) => c.name === "Missing values")?.detail,
    duplicates: checks.find((c) => c.name.startsWith("Duplicate"))?.detail,
  };
}

// ------------------------------------------------------------------ renderer

export async function generateReport(payload: ReportPayload, user: AuthUser): Promise<GeneratedReport> {
  const generatedAt = new Date();
  const title = TYPE_TITLES[payload.type];
  const reportId = createReportId(payload.type, generatedAt);
  const { subject, facts } = subjectOf(payload);

  const doc = new ReportDoc({ reportTitle: title, reportId, generatedAt });

  switch (payload.type) {
    case "executive":
      renderExecutive(doc, payload.data, user, facts);
      break;
    case "analysis-summary":
      renderAnalysisSummary(doc, payload.data, user, facts);
      break;
    case "claim":
      renderClaim(doc, payload.data, user, facts);
      break;
    case "provider":
      renderProvider(doc, payload.data, user, facts);
      break;
    case "investigation":
      renderInvestigation(doc, payload.data, user, facts);
      break;
    case "queue":
      renderQueue(doc, payload.data, user, facts);
      break;
    case "data-quality":
      renderDataQuality(doc, payload.data, user, facts);
      break;
  }

  const { blob, pageCount } = doc.finalize();
  const metadata: ReportMetadata = {
    report_id: reportId,
    report_type: payload.type,
    title,
    generated_at: formatDateTime(generatedAt),
    generated_by: user.name,
    generated_by_role: ROLE_LABELS[user.role],
    filename: filenameFor(payload.type, generatedAt, subject),
    subjects: facts,
  };

  return { metadata, blob, url: URL.createObjectURL(blob), page_count: pageCount };
}

export function downloadReport(report: GeneratedReport) {
  const a = document.createElement("a");
  a.href = report.url;
  a.download = report.metadata.filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// ------------------------------------------------------------------ sections

function coverFor(
  doc: ReportDoc,
  user: AuthUser,
  reportType: string,
  facts: { label: string; value: string }[],
  preparedFor: string,
  riskHighlight?: { score: number; level: string } | undefined,
) {
  doc.cover({
    reportType,
    facts: [
      ...facts,
      { label: "Generated by", value: `${user.name} · ${ROLE_LABELS[user.role]}` },
    ],
    preparedFor,
    riskHighlight,
  });
}

function renderExecutive(
  doc: ReportDoc,
  data: DashboardReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  coverFor(doc, user, "Enterprise Risk Overview", facts, "Payment Integrity Leadership");
  const s = data.summary;
  const dist = Object.fromEntries(s.risk_distribution.map((r) => [r.level, r.count]));

  doc.section("1. Executive Summary");
  doc.para(
    `Across ${num(s.total_claims)} scored claims from ${num(s.providers)} providers, the model identified ${num(
      (dist["Critical"] ?? 0) + (dist["High"] ?? 0),
    )} claims in the Critical or High risk bands. ${num(s.high_risk_cases)} cases are currently tracked for payment-integrity review. Reported exposure below reflects reimbursement associated with each risk band and is not a recovery estimate.`,
  );

  doc.section("2. Dataset Overview");
  doc.kpis([
    { label: "Total claims", value: num(s.total_claims) },
    { label: "Providers", value: num(s.providers) },
    { label: "Beneficiaries", value: num(s.beneficiaries) },
    { label: "Total reimbursement", value: currency(data.total_reimbursement) },
  ]);

  doc.section("3. Risk Distribution");
  doc.table(
    ["Risk band", "Claims", "Share", "Reimbursement"],
    s.risk_distribution.map((r) => [
      r.level,
      num(r.count),
      `${((r.count / s.total_claims) * 100).toFixed(2)}%`,
      currency(s.reimbursement_by_risk.find((x) => x.level === r.level)?.amount ?? 0),
    ]),
  );
  doc.bars(
    s.risk_distribution.map((r) => ({
      label: r.level,
      value: r.count,
      display: num(r.count),
      tone: r.level,
    })),
  );

  doc.section("4. Investigation Workload");
  const byStatus = countBy(s.recent_cases.concat(), (c) => c.status);
  doc.kpis(
    ["New", "Under Review", "Escalated", "Resolved"].map((st) => ({
      label: st,
      value: num(byStatus[st] ?? 0),
    })),
  );

  doc.section("5. Top High-Risk Providers");
  doc.table(
    ["Provider", "Risk", "Level", "Claims", "Reimbursement", "Status"],
    s.top_risky_providers.map((p) => [
      p.provider_id,
      `${p.risk_score}%`,
      p.risk_level,
      num(p.claim_count),
      currency(p.total_reimbursement),
      p.status,
    ]),
  );

  doc.section("6. Top Risk Factors");
  doc.bars(
    data.risk_factors.map((f) => ({ label: f.factor, value: f.weight, display: `${f.weight}%` })),
  );

  doc.section("7. Risk Analytics");
  doc.table(
    ["Claim type", "Claims", "Share"],
    s.claim_type_distribution.map((c) => [
      c.type,
      num(c.count),
      `${((c.count / s.total_claims) * 100).toFixed(1)}%`,
    ]),
  );
  doc.callout("Threshold note", THRESHOLD_NOTE, "neutral");

  doc.section("8. Key Findings");
  doc.bullets([
    `${num(dist["Critical"] ?? 0)} claims scored in the Critical band and are the highest-priority review population.`,
    "Risk concentrates in providers with claim volume and reimbursement materially above their peer cohort.",
    `Outpatient claims dominate volume, while inpatient claims carry a higher average reimbursement per claim.`,
  ]);

  doc.section("9. Recommended Areas for Investigation");
  doc.bullets([
    "Review the top high-risk providers listed in section 5 for billing-pattern deviation.",
    "Prioritise Critical-band claims that are still in New status in the investigation queue.",
    "Confirm peer-cohort definitions with the model team before escalating provider-level findings.",
  ]);

  doc.section("10. Disclaimer");
  doc.disclaimer(DISCLAIMER_GENERAL);
}

function renderAnalysisSummary(
  doc: ReportDoc,
  data: DashboardReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  coverFor(doc, user, "Fraud Risk Analysis Report", facts, "Payment Integrity Analytics");
  const s = data.summary;

  doc.section("1. Analysis Overview");
  doc.keyValues([
    { label: "Dataset", value: data.dataset.file_name },
    { label: "Analysis timestamp", value: formatDateTime(new Date()) },
    { label: "Model", value: data.model?.name ?? "Not available" },
    { label: "Model run", value: data.model?.run_id ?? "Not available" },
    { label: "Claims analysed", value: num(s.total_claims) },
    { label: "Providers analysed", value: num(s.providers) },
  ]);

  doc.section("2. Risk Distribution");
  doc.bars(
    s.risk_distribution.map((r) => ({ label: r.level, value: r.count, display: num(r.count), tone: r.level })),
  );

  doc.section("3. Model Performance");
  if (data.model?.metrics && Object.keys(data.model.metrics).length) {
    doc.table(
      ["Metric", "Value"],
      Object.entries(data.model.metrics).map(([k, v]) => [k, String(v)]),
    );
  } else {
    doc.para("Model performance metrics are not available for this report.", { italic: true, muted: true });
  }

  doc.section("4. Top Risk Factors");
  doc.bars(data.risk_factors.map((f) => ({ label: f.factor, value: f.weight, display: `${f.weight}%` })));

  doc.section("5. High-Risk Providers");
  doc.table(
    ["Provider", "Risk", "Level", "Claims", "Beneficiaries", "Avg reimbursement"],
    s.top_risky_providers.map((p) => [
      p.provider_id,
      `${p.risk_score}%`,
      p.risk_level,
      num(p.claim_count),
      num(p.beneficiary_count),
      currency(p.average_reimbursement),
    ]),
  );

  doc.section("6. Highest-Priority Cases");
  doc.table(
    ["Case", "Claim", "Provider", "Risk", "Priority", "Status"],
    s.recent_cases.map((c) => [
      c.case_id,
      c.claim_id,
      c.provider_id,
      `${c.risk_score}%`,
      c.priority,
      c.status,
    ]),
  );

  doc.section("7. Financial Exposure");
  if (typeof data.financial_exposure === "number") {
    doc.kpis([{ label: "Potential exposure", value: currency(data.financial_exposure), tone: "critical" }], 2);
  } else {
    doc.para("Financial exposure estimate is not available.", { italic: true, muted: true });
  }
  doc.table(
    ["Risk band", "Reimbursement"],
    s.reimbursement_by_risk.map((r) => [r.level, currency(r.amount)]),
  );

  doc.section("8. AI Analysis Summary", "Evidence-grounded explanation layer output.");
  doc.callout("Evidence-grounded AI explanation", data.ai_summary ?? "No AI summary available for this run.");

  doc.section("9. Recommended Investigation Priorities");
  doc.bullets([
    "Critical-band claims with New status.",
    "Providers whose claim volume exceeds twice the peer-cohort average.",
    "Cases escalated but not yet assigned to an investigator.",
  ]);

  doc.section("10. Disclaimer");
  doc.disclaimer(DISCLAIMER_GENERAL);
}

function renderClaim(
  doc: ReportDoc,
  data: ClaimReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  const { claim, risk, provider, peer, investigation } = data;

  const hasClaimRisk = !("available" in (risk as any) && (risk as any).available === false);
  coverFor(
    doc,
    user,
    "Claim Investigation Report",
    facts,
    "Payment Integrity Investigation",
    hasClaimRisk
      ? { score: (risk as any).risk_score, level: (risk as any).risk_level }
      : undefined,
  );

  doc.section("Section 1 — Risk Summary");
  if (hasClaimRisk) {
    doc.riskPanel((risk as any).risk_score, (risk as any).risk_level, (risk as any).prediction);
    doc.callout("Threshold note", THRESHOLD_NOTE, "neutral");
  } else {
    doc.para("Claim-level model scoring is not available for this claim.", { italic: true, muted: true });
  }

  // If no claim-level explanation exists, use the frontend-assembled explanation when present
  const claimExplanation = hasClaimRisk ? (risk as any).explanation : (data as any).explanation;

  doc.section("Section 2 — Claim Information");
  doc.keyValues([
    { label: "Claim ID", value: claim.claim_id },
    { label: "Provider ID", value: claim.provider_id },
    { label: "Beneficiary ID", value: claim.bene_id },
    { label: "Claim type", value: claim.claim_type },
    { label: "Claim start", value: claim.claim_start_date },
    { label: "Claim end", value: claim.claim_end_date },
    { label: "Reimbursement", value: currency(claim.reimbursement) },
    { label: "Attending physician", value: claim.attending_physician ?? "Not available" },
    { label: "Operating physician", value: claim.operating_physician ?? "Not available" },
    { label: "Diagnosis codes", value: (claim.diagnosis_codes ?? []).join(", ") || "Not available" },
    { label: "Procedure codes", value: (claim.procedure_codes ?? []).join(", ") || "Not available" },
    { label: "Claim status", value: claim.status ?? "Not available" },
  ]);

  doc.section("Section 3 — Model Evidence", "Model-derived factors and their peer-group comparison.");
  if (hasClaimRisk && (risk as any).evidence && (risk as any).evidence.length) {
    doc.table(
      ["Factor", "Observed", "Peer value", "Difference", "Interpretation"],
      (risk as any).evidence.map((e: any) => [
        e.factor,
        e.unit === "currency" ? currency(e.provider_value) : num(e.provider_value),
        e.unit === "currency" ? currency(e.peer_value) : num(e.peer_value),
        e.difference,
        e.note ?? "—",
      ]),
      { widths: { 0: 34, 1: 24, 2: 24, 3: 20 } },
    );
  } else if ((data as any).evidence && (data as any).evidence.length) {
    // Use dataset-derived evidence when claim-level model evidence is not available
    doc.table(
      ["Factor", "Observed", "Peer value", "Difference", "Interpretation"],
      (data as any).evidence.map((e: any) => [
        e.factor,
        typeof e.value === "number" ? currency(e.value) : String(e.value ?? "Not available"),
        typeof e.peer_value === "number" ? currency(e.peer_value) : String(e.peer_value ?? "Not available"),
        typeof e.difference === "number" ? String(e.difference) : String(e.difference ?? "Not available"),
        e.description ?? "Dataset-derived analytical signal",
      ]),
    );
  } else {
    doc.para("Model evidence is not available for this claim.", { italic: true, muted: true });
  }

  doc.section("Section 4 — Provider Profile");
  if (provider) {
    doc.kpis([
      { label: "Claims", value: num(provider.claim_count) },
      { label: "Beneficiaries", value: num(provider.beneficiary_count) },
      { label: "Total reimbursement", value: currency(provider.total_reimbursement) },
      { label: "Avg reimbursement", value: currency(provider.average_reimbursement) },
    ]);
  } else {
    doc.para("Provider profile is not available for this claim.", { italic: true, muted: true });
  }

  doc.section("Section 5 — Provider vs Peer Cohort");
  if (provider && peer) {
    doc.table(
      ["Metric", "Provider", "Peer average", "Difference"],
      [
        ["Claims submitted", num(provider.claim_count), num(peer.claim_count), pct(provider.claim_count, peer.claim_count)],
        ["Unique beneficiaries", num(provider.beneficiary_count), num(peer.beneficiary_count), pct(provider.beneficiary_count, peer.beneficiary_count)],
        ["Average reimbursement", currency(provider.average_reimbursement), currency(peer.average_reimbursement), pct(provider.average_reimbursement, peer.average_reimbursement)],
        ["Inpatient claims", num(provider.inpatient_claims), num(peer.inpatient_claims), pct(provider.inpatient_claims, peer.inpatient_claims)],
        ["Outpatient claims", num(provider.outpatient_claims), num(peer.outpatient_claims), pct(provider.outpatient_claims, peer.outpatient_claims)],
      ],
    );
  } else {
    doc.para("Peer comparison data is not available.", { italic: true, muted: true });
  }

  doc.section("Section 6 — Why This Claim Was Flagged", "Evidence-Grounded AI Explanation");
  if (claimExplanation) {
    doc.callout("Evidence-grounded AI explanation", claimExplanation.summary);
    doc.bullets(claimExplanation.reasons);
  } else {
    doc.para("No AI explanation is available for this claim.", { italic: true, muted: true });
  }
  doc.para(
    "The explanation layer describes model-derived evidence only. It does not determine whether fraud occurred.",
    { italic: true, muted: true, size: 8.5 },
  );

  doc.section("Section 7 — Supporting Evidence");
  const claimEvidence = hasClaimRisk ? (risk as any).evidence : (data as any).evidence;
  if (claimEvidence && claimEvidence.length) {
    doc.bullets(
      claimEvidence.map((e: any) => {
        const isCurrency = e.unit === "currency" || String(e.factor).toLowerCase().includes("reimburse");
        const pv = typeof e.provider_value === "number" ? (isCurrency ? currency(e.provider_value) : num(e.provider_value)) : String(e.provider_value ?? "Not available");
        const peer = typeof e.peer_value === "number" ? (isCurrency ? currency(e.peer_value) : num(e.peer_value)) : String(e.peer_value ?? "Not available");
        return `${e.factor}: observed ${pv} vs peer ${peer} (${e.difference ?? e.description}).`;
      }),
    );
  } else {
    doc.para("No supporting evidence is available.", { italic: true, muted: true });
  }
  const trace = data.traceability;
  if (trace) {
    doc.subheading("Traceability");
    doc.keyValues([
      { label: "Explanation ID", value: trace.explanation_id ?? "Not available" },
      { label: "Claim ID", value: trace.claim_id ?? claim.claim_id },
      { label: "Model run ID", value: trace.model_run_id ?? "Not available" },
      { label: "Explanation generated", value: trace.generated_at ?? "Not available" },
      { label: "Explainer", value: claimExplanation?.model ?? "Not available" },
      { label: "Evidence used", value: (trace.evidence_used ?? []).join(", ") || "Not available" },
    ]);
  }

  doc.section("Section 8 — Investigation Status");
  if (investigation) {
    doc.keyValues([
      { label: "Case ID", value: investigation.case_id },
      { label: "Status", value: investigation.status },
      { label: "Priority", value: investigation.priority },
      { label: "Assigned investigator", value: investigation.assigned_to },
      { label: "Created", value: investigation.created_at },
      { label: "Last updated", value: formatDateTime(new Date()) },
    ]);
  } else {
    doc.para("No investigation case has been opened for this claim.", { italic: true, muted: true });
  }

  doc.section("Section 9 — Investigator Notes");
  if (data.notes?.length) {
    doc.bullets(data.notes.map((n) => `${n.at} — ${n.text}`));
  } else {
    doc.para("No investigator notes have been recorded.", { italic: true, muted: true });
  }

  doc.section("Section 10 — Investigation Decision");
  if (data.decision) {
    doc.keyValues([
      { label: "Decision", value: data.decision.decision },
      { label: "Reviewer", value: data.decision.reviewer },
      { label: "Date", value: data.decision.date },
      { label: "Comments", value: data.decision.comments ?? "—" },
    ]);
  } else {
    doc.para("Investigation decision has not yet been recorded.", { italic: true, muted: true });
  }

  doc.section("Section 11 — Disclaimer");
  doc.disclaimer(DISCLAIMER_CASE);
}

function renderProvider(
  doc: ReportDoc,
  data: ProviderReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  const { provider, peer } = data;
  coverFor(doc, user, "Provider Risk Assessment Report", facts, "Provider Network Review", {
    score: provider.risk_score,
    level: provider.risk_level,
  });

  doc.section("1. Risk Summary");
  doc.riskPanel(
    provider.risk_score,
    provider.risk_level,
    provider.risk_level === "Critical" ? "Potential Fraud" : "Requires Investigation",
    "Provider-level model risk signal. Not a determination of fraud.",
  );
  doc.keyValues([
    { label: "Provider ID", value: provider.provider_id },
    { label: "Risk status", value: provider.status },
    { label: "Risk level", value: provider.risk_level },
  ]);

  doc.section("2. Billing Profile");
  doc.kpis([
    { label: "Claims", value: num(provider.claim_count) },
    { label: "Beneficiaries", value: num(provider.beneficiary_count) },
    { label: "Total reimbursement", value: currency(provider.total_reimbursement) },
    { label: "Avg / claim", value: currency(provider.average_reimbursement) },
  ]);

  doc.section("3. Claim Type Distribution");
  doc.bars([
    { label: "Inpatient", value: provider.inpatient_claims, display: num(provider.inpatient_claims) },
    { label: "Outpatient", value: provider.outpatient_claims, display: num(provider.outpatient_claims) },
  ]);

  doc.section("4. Provider vs Peer Cohort");
  doc.table(
    ["Metric", "Provider", "Peer average", "Difference"],
    [
      ["Claims submitted", num(provider.claim_count), num(peer.claim_count), pct(provider.claim_count, peer.claim_count)],
      ["Unique beneficiaries", num(provider.beneficiary_count), num(peer.beneficiary_count), pct(provider.beneficiary_count, peer.beneficiary_count)],
      ["Average reimbursement", currency(provider.average_reimbursement), currency(peer.average_reimbursement), pct(provider.average_reimbursement, peer.average_reimbursement)],
      ["Inpatient claims", num(provider.inpatient_claims), num(peer.inpatient_claims), pct(provider.inpatient_claims, peer.inpatient_claims)],
      ["Outpatient claims", num(provider.outpatient_claims), num(peer.outpatient_claims), pct(provider.outpatient_claims, peer.outpatient_claims)],
    ],
  );

  doc.section("5. Top Risk Factors");
  doc.bars(data.risk_factors.map((f) => ({ label: f.factor, value: f.weight, display: `${f.weight}%` })));

  doc.section("6. Evidence-Grounded AI Explanation");
  doc.callout("Evidence-grounded AI explanation", data.explanation.summary);
  doc.bullets(data.explanation.reasons);

  doc.section("7. Investigation History");
  doc.table(
    ["Case", "Claim", "Risk", "Priority", "Status", "Assigned to"],
    data.related_cases.map((c) => [
      c.case_id,
      c.claim_id,
      `${c.risk_score}%`,
      c.priority,
      c.status,
      c.assigned_to,
    ]),
  );

  doc.section("8. Analyst Notes");
  if (data.notes?.length) doc.bullets(data.notes);
  else doc.para("No analyst notes have been recorded for this provider.", { italic: true, muted: true });

  doc.section("9. Disclaimer");
  doc.disclaimer(DISCLAIMER_CASE);
}

function renderInvestigation(
  doc: ReportDoc,
  data: InvestigationReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  const { investigation: c, claim, risk } = data;
  coverFor(doc, user, "Investigation Case Report", facts, "Investigation Case File", {
    score: c.risk_score,
    level: c.priority,
  });

  doc.section("1. Case Overview");
  doc.keyValues([
    { label: "Case ID", value: c.case_id },
    { label: "Claim ID", value: c.claim_id },
    { label: "Provider ID", value: c.provider_id },
    { label: "Risk score", value: `${c.risk_score}%` },
    { label: "Priority", value: c.priority },
    { label: "Status", value: c.status },
    { label: "Assigned investigator", value: c.assigned_to },
    { label: "Created", value: c.created_at },
    { label: "Report generated", value: formatDateTime(new Date()) },
  ]);

  doc.section("2. Model Risk Signal");
  doc.riskPanel(c.risk_score, c.priority, risk?.prediction ?? "Requires Investigation");

  doc.section("3. Case Timeline", "Audit-style chronological record.");
  doc.timeline(data.timeline);

  doc.section("4. Risk Evidence");
  if (risk?.evidence.length) {
    doc.table(
      ["Factor", "Observed", "Peer value", "Difference"],
      risk.evidence.map((e) => [
        e.factor,
        e.unit === "currency" ? currency(e.provider_value) : num(e.provider_value),
        e.unit === "currency" ? currency(e.peer_value) : num(e.peer_value),
        e.difference,
      ]),
    );
  } else {
    doc.para("Model evidence is not available for this case.", { italic: true, muted: true });
  }

  doc.section("5. Claim Detail");
  if (claim) {
    doc.keyValues([
      { label: "Claim type", value: claim.claim_type },
      { label: "Reimbursement", value: currency(claim.reimbursement) },
      { label: "Service period", value: `${claim.claim_start_date} → ${claim.claim_end_date}` },
      { label: "Beneficiary", value: claim.bene_id },
      { label: "Attending physician", value: claim.attending_physician ?? "Not available" },
      { label: "Operating physician", value: claim.operating_physician ?? "Not available" },
    ]);
  } else {
    doc.para("Claim detail is not available.", { italic: true, muted: true });
  }

  doc.section("6. Evidence-Grounded AI Explanation");
  if (risk) {
    doc.callout("Evidence-grounded AI explanation", risk.explanation.summary);
    doc.bullets(risk.explanation.reasons);
  } else {
    doc.para("No AI explanation is available for this case.", { italic: true, muted: true });
  }

  doc.section("7. Investigator Notes");
  if (data.notes?.length) doc.bullets(data.notes.map((n) => `${n.at} — ${n.text}`));
  else doc.para("No investigator notes have been recorded.", { italic: true, muted: true });

  doc.section("8. Actions Taken");
  if (data.actions?.length) doc.bullets(data.actions);
  else doc.para("No case actions have been recorded.", { italic: true, muted: true });

  doc.section("9. Human Investigation Decision");
  if (data.decision) {
    doc.keyValues([
      { label: "Decision", value: data.decision.decision },
      { label: "Reviewer", value: data.decision.reviewer },
      { label: "Date", value: data.decision.date },
      { label: "Comments", value: data.decision.comments ?? "—" },
    ]);
  } else {
    doc.para("Investigation decision has not yet been recorded.", { italic: true, muted: true });
  }

  doc.section("10. Disclaimer");
  doc.disclaimer(DISCLAIMER_CASE);
}

function renderQueue(
  doc: ReportDoc,
  data: QueueReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  coverFor(doc, user, "Investigation Queue Summary", facts, "Investigation Operations");
  const cases = data.cases;
  const byPriority = countBy(cases, (c) => c.priority);
  const byStatus = countBy(cases, (c) => c.status);

  doc.section("1. Filters Applied");
  doc.keyValues([
    { label: "Risk", value: String(data.filters.risk ?? "All") },
    { label: "Claim type", value: String(data.filters.claim_type ?? "All") },
    { label: "Status", value: String(data.filters.status ?? "All") },
    { label: "Date range", value: String(data.filters.date_range ?? "All dates") },
    { label: "Search", value: data.filters.search?.trim() || "—" },
    { label: "Matching cases", value: num(cases.length) },
  ]);

  doc.section("2. Queue Composition");
  doc.kpis([
    { label: "Critical", value: num(byPriority["Critical"] ?? 0), tone: "critical" },
    { label: "High", value: num(byPriority["High"] ?? 0), tone: "high" },
    { label: "Medium", value: num(byPriority["Medium"] ?? 0), tone: "medium" },
    { label: "Low", value: num(byPriority["Low"] ?? 0), tone: "low" },
  ]);
  doc.kpis([
    { label: "New", value: num(byStatus["New"] ?? 0) },
    { label: "Under review", value: num(byStatus["Under Review"] ?? 0) },
    { label: "Escalated", value: num(byStatus["Escalated"] ?? 0) },
    { label: "Resolved", value: num(byStatus["Resolved"] ?? 0) },
  ]);

  doc.section("3. Case Detail");
  doc.table(
    ["Priority", "Case", "Claim", "Provider", "Risk", "Status", "Assigned to", "Created"],
    [...cases]
      .sort((a, b) => b.risk_score - a.risk_score)
      .map((c) => [
        c.priority,
        c.case_id,
        c.claim_id,
        c.provider_id,
        `${c.risk_score}%`,
        c.status,
        c.assigned_to,
        c.created_at,
      ]),
  );

  doc.section("4. Highest-Priority Cases");
  const top = [...cases].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);
  if (top.length) {
    doc.bullets(
      top.map(
        (c) =>
          `${c.case_id} — claim ${c.claim_id}, provider ${c.provider_id}, risk ${c.risk_score}% (${c.priority}), status ${c.status}, assigned to ${c.assigned_to}.`,
      ),
    );
  } else {
    doc.para("No cases match the current filters.", { italic: true, muted: true });
  }

  doc.section("5. Disclaimer");
  doc.disclaimer(DISCLAIMER_GENERAL);
}

function renderDataQuality(
  doc: ReportDoc,
  data: DataQualityReportData,
  user: AuthUser,
  facts: { label: string; value: string }[],
) {
  coverFor(doc, user, "Claims Dataset Quality Report", facts, "Data Engineering & Analytics");

  doc.section("1. Dataset Overview");
  doc.keyValues([
    { label: "Dataset", value: data.dataset.file_name },
    { label: "File type", value: data.dataset.file_type },
    { label: "File size", value: data.dataset.file_size ?? "Not available" },
    { label: "Rows", value: num(data.dataset.rows) },
    { label: "Columns", value: num(data.dataset.columns) },
    { label: "Missing values", value: data.missing_values ?? "Not available" },
    { label: "Duplicate records", value: data.duplicates ?? "Not available" },
    { label: "Invalid values", value: data.invalid_values ?? "Not available" },
  ]);

  doc.section("2. Data Quality Score");
  if (typeof data.quality_score === "number") {
    doc.kpis([{ label: "Quality score", value: `${data.quality_score}%` }], 2);
  } else {
    doc.para("Data quality score is pending backend validation.", { italic: true, muted: true });
  }

  doc.section("3. Validation Results");
  const counts = countBy(data.checks, (c) => c.status);
  doc.kpis([
    { label: "Passed", value: num(counts["pass"] ?? 0), tone: "low" },
    { label: "Warnings", value: num(counts["warn"] ?? 0), tone: "high" },
    { label: "Errors", value: num(counts["fail"] ?? 0), tone: "critical" },
  ], 3);
  doc.table(
    ["Check", "Result", "Detail"],
    data.checks.map((c) => [c.name, c.status.toUpperCase(), c.detail]),
    { widths: { 0: 44, 1: 22 } },
  );

  doc.section("4. Schema Validation");
  doc.table(
    ["Field", "Type", "Required", "Result", "Note"],
    data.schema.map((f) => [f.field, f.type, f.required ? "Yes" : "No", f.status.toUpperCase(), f.note]),
    { widths: { 1: 24, 2: 20, 3: 20 } },
  );

  doc.section("5. Recommended Actions");
  const actions = data.checks
    .filter((c) => c.status !== "pass")
    .map((c) => `${c.name}: ${c.detail}. Confirm the source system behaviour before scoring.`);
  if (actions.length) doc.bullets(actions);
  else doc.para("No corrective actions required — all validation checks passed.", { muted: true });

  doc.section("6. Disclaimer");
  doc.disclaimer(DISCLAIMER_GENERAL);
}

// ------------------------------------------------------------------- helpers

function pct(a: number, b: number) {
  if (!b) return "Not available";
  const diff = Math.round(((a - b) / b) * 100);
  return `${diff >= 0 ? "+" : ""}${diff}%`;
}

function countBy<T>(items: T[], key: (item: T) => string): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const k = key(item);
    acc[k] = (acc[k] ?? 0) + 1;
    return acc;
  }, {});
}
