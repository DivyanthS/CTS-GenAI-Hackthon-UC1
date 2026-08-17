import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EvidenceCard } from "@/components/explanation/EvidenceCard";
import { ExplanationCard } from "@/components/explanation/ExplanationCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { getClaim as getBackendClaim, BackendClaim, api } from "@/services/api";
import { getProvider, getAnalytics, predictProvider } from "@/services/api";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectClaimReportData } from "@/services/reportService";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function ClaimDetails() {
  const { claimId } = useParams({ from: "/_shell/claims/$claimId" });
  const [claim, setClaim] = useState<BackendClaim | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [provider, setProvider] = useState<any | null>(null);
  const [providerRaw, setProviderRaw] = useState<any | null>(null);
  const [providerPrediction, setProviderPrediction] = useState<{ fraud_probability: number; threshold?: number; decision?: string } | null>(null);
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [evidence, setEvidence] = useState<import("@/types").Evidence[]>([]);
  const [explanation, setExplanation] = useState<import("@/types").Explanation | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);

    Promise.all([
      getBackendClaim(claimId),
    ])
      .then(async ([c]) => {
        if (!c) {
          setClaim(null);
          setLoading(false);
          return;
        }

        setClaim(c);

        try {
          // Prefer the backend explanation/evidence endpoint for authoritative, dataset-grounded evidence.
          const [explanationRes, prov] = await Promise.all([
            import("@/services/api").then((m) => m.getClaimExplanation(String(c.ClaimID))).catch(() => null),
            // Keep provider summary for context (may be null)
            import("@/services/api").then((m) => m.getProvider(String(c.Provider))).catch(() => null),
          ]);

          setProvider(prov ?? null);

          if (explanationRes) {
            // Provider-level risk is returned under `risk` with scope="provider".
            const risk = explanationRes.risk;
            setProviderPrediction(
              risk && typeof risk.fraud_probability === "number"
                ? {
                    fraud_probability: risk.fraud_probability,
                    ...(typeof risk.threshold === "number" ? { threshold: risk.threshold } : {}),
                    ...(typeof risk.decision === "string" ? { decision: risk.decision } : {}),
                  }
                : null,
            );

            // Map backend factors into the frontend Evidence[] shape
            const ev: import("@/types").Evidence[] = (explanationRes.factors ?? []).map((f: any) => {
              // prefer provider_value then claim_value when present
              const providerValue = f.provider_value ?? f.claim_value ?? null;
              const peerValue = f.peer_value ?? null;

              // Format the difference string as an integer percent if available
              const diffPct = typeof f.difference_percent === "number" ? f.difference_percent : null;

              const diffStr = diffPct != null ? `${diffPct >= 0 ? "+" : ""}${Math.round(diffPct)}` : "";

              // Heuristic unit mapping (backend returns numeric evidence; frontend formats)
              const unit = (f.name || "").toLowerCase().includes("reimb") || (f.name || "").toLowerCase().includes("reimbursement") ? "currency" : "count";

              return {
                factor: f.name,
                provider_value: providerValue,
                peer_value: peerValue,
                difference: diffStr,
                unit: unit as import("@/types").Evidence["unit"],
                note: f.note ?? undefined,
              };
            });

            setEvidence(ev.slice(0, 6));

            setExplanation({
              summary: explanationRes.summary ?? "",
              reasons: explanationRes.review_focus ?? [],
              disclaimer: explanationRes.disclaimer ?? "",
              generated_at: new Date().toISOString(),
            });

            // Also set raw provider features if available via providers endpoint
            try {
              const raw = await api.get(`/providers/${encodeURIComponent(String(c.Provider))}`).then((r) => r.data?.provider ?? null).catch(() => null);
              setProviderRaw(raw ?? null);
            } catch (err) {
              setProviderRaw(null);
            }
          } else {
            // Fallback: if backend explanation unavailable, leave evidence/explanation empty.
            setEvidence([]);
            setExplanation(null);

            try {
              const raw = await api.get(`/providers/${encodeURIComponent(String(c.Provider))}`).then((r) => r.data?.provider ?? null).catch(() => null);
              setProviderRaw(raw ?? null);
            } catch (err) {
              setProviderRaw(null);
            }
          }
        } catch (err) {
          // Non-fatal: evidence/explanation remain empty.
          console.error(err);
          setEvidence([]);
          setExplanation(null);
        }
      })
      .catch(() => setError("Unable to load claim details."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [claimId]);

  if (loading) return <LoadingState label="Loading claim details…" />;
  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!claim)
    return (
      <EmptyState
        title="Claim not found"
        description={`No claim exists with ID ${claimId}.`}
      />
    );

  // Helper: collect diagnosis and procedure codes from known fields
  const diagnosisCodesRaw: string[] = [];
  const procedureCodesRaw: string[] = [];

  // Admission diagnosis
  if ((claim as any).ClmAdmitDiagnosisCode) {
    diagnosisCodesRaw.push(String((claim as any).ClmAdmitDiagnosisCode));
  }

  // ClmDiagnosisCode_1 .. ClmDiagnosisCode_10
  for (let i = 1; i <= 10; i++) {
    const key = `ClmDiagnosisCode_${i}`;
    const val = (claim as any)[key];
    if (val && String(val).toUpperCase() !== "UNKNOWN") {
      diagnosisCodesRaw.push(String(val));
    }
  }

  // ClmProcedureCode_1 .. ClmProcedureCode_6
  for (let i = 1; i <= 6; i++) {
    const key = `ClmProcedureCode_${i}`;
    const val = (claim as any)[key];
    if (val && String(val).toUpperCase() !== "UNKNOWN") {
      procedureCodesRaw.push(String(val));
    }
  }

  // Clean: trim, remove empty values and duplicates
  const diagnosisCodes = Array.from(new Set(diagnosisCodesRaw
    .map((s) => String(s).trim())
    .filter((s) => s && s !== "null" && s !== "undefined")));

  const procedureCodes = Array.from(new Set(procedureCodesRaw
    .map((s) => String(s).trim())
    .filter((s) => s && s !== "null" && s !== "undefined")));

  // Service duration in days (if valid dates)
  let serviceDurationDisplay = "—";
  try {
    const start = claim.ClaimStartDt ? new Date(String(claim.ClaimStartDt)) : null;
    const end = claim.ClaimEndDt ? new Date(String(claim.ClaimEndDt)) : null;
    if (start && !isNaN(start.getTime()) && end && !isNaN(end.getTime())) {
      const msPerDay = 1000 * 60 * 60 * 24;
      const days = Math.round((end.getTime() - start.getTime()) / msPerDay);
      serviceDurationDisplay = `${String(claim.ClaimStartDt ?? "—")} → ${String(claim.ClaimEndDt ?? "—")} (${days} days)`;
    } else {
      serviceDurationDisplay = `${String(claim.ClaimStartDt ?? "—")} → ${String(claim.ClaimEndDt ?? "—")}`;
    }
  } catch (err) {
    serviceDurationDisplay = `${String(claim.ClaimStartDt ?? "—")} → ${String(claim.ClaimEndDt ?? "—")}`;
  }

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/claims">
          <ArrowLeft className="size-4" /> Back to claims
        </Link>
      </Button>

      <PageHeader
        title={`Claim ${claim.ClaimID}`}
        subtitle={`Provider ${claim.Provider} · Beneficiary ${claim.BeneID ?? "—"}`}
        actions={
          <div className="flex items-center gap-2">
            {/* Claim-level risk is not available from the backend; do not fabricate. */}
            <div className="text-xs text-muted-foreground">Claim-level risk: <span className="font-medium text-foreground">Not available</span></div>

            <ReportButton
              type="claim"
              label="Download Claim Report"
              mode="download"
              build={async () => {
                const data = await collectClaimReportData(claim.ClaimID);
                return data ? { type: "claim", data } : null;
              }}
            />
          </div>
        }
      />

      <section className="panel p-6">
        <dl className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Claim type", claim.ClaimType ?? "—"],
            ["Reimbursement", claim.InscClaimAmtReimbursed != null ? currency(Number(claim.InscClaimAmtReimbursed)) : "—"],
            ["Service period", serviceDurationDisplay],
            ["Service duration", serviceDurationDisplay.includes("(") ? serviceDurationDisplay.split("(").at(1)?.replace(")", "") ?? "—" : "—"],
            ["Attending physician", claim.AttendingPhysician ?? "—"],
            ["Operating physician", claim.OperatingPhysician ?? "—"],
            ["Other physician", claim.OtherPhysician ?? "—"],
            ["Diagnosis codes", diagnosisCodes.length ? diagnosisCodes.join(", ") : "—"],
            ["Procedure codes", procedureCodes.length ? procedureCodes.join(", ") : "—"],
            ["Deductible paid", (claim as any).DeductibleAmtPaid != null ? currency(Number((claim as any).DeductibleAmtPaid)) : "—"],
          ].map(([label, value]) => (            <div key={String(label)}>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">{label}</dt>
              <dd className="mt-1 text-sm font-medium text-foreground">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <div>
       <h2 className="text-sm font-semibold text-foreground">Provider-level risk</h2>
       <div className="mt-3">
         {providerPrediction ? (
           <div className="flex items-center gap-3">
             <RiskBadge
               level={
                 providerPrediction.fraud_probability >= 0.75
                   ? "Critical"
                   : providerPrediction.fraud_probability >= 0.5
                   ? "High"
                   : providerPrediction.fraud_probability >= 0.23
                   ? "Medium"
                   : "Low"
               }
               score={Math.round(providerPrediction.fraud_probability * 100)}
             />

             <div className="text-sm">
               <div className="font-medium">Provider: {provider?.provider_id ?? provider?.provider_id ?? claim.Provider}</div>
               <div className="text-muted-foreground text-xs">Decision: {providerPrediction.decision ?? "—"} · Threshold: {providerPrediction.threshold ?? "Not available"}</div>
               <div className="text-xs text-muted-foreground mt-1">This score represents the selected provider's model risk. It is not an individual claim-level fraud probability.</div>
             </div>
           </div>
         ) : (
           <div className="text-sm text-muted-foreground">Provider risk information unavailable.</div>
         )}
       </div>
      </div>
       
      <div className="mt-4">
        <h2 className="text-sm font-semibold text-foreground">Provider context</h2>
        <div className="mt-3 panel p-4">
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Provider ID", provider?.provider_id ?? claim.Provider],
              ["Total claims", providerRaw?.TotalClaims ?? provider?.claim_count ?? "—"],
              ["Unique beneficiaries", providerRaw?.UniqueBeneficiaries ?? provider?.beneficiary_count ?? "—"],
              ["Total reimbursement", providerRaw?.TotalReimbursement != null ? currency(Number(providerRaw?.TotalReimbursement ?? provider?.total_reimbursement ?? 0)) : "—"],
              ["Average reimbursement", providerRaw?.AverageReimbursement != null ? currency(Number(providerRaw?.AverageReimbursement ?? provider?.average_reimbursement ?? 0)) : "—"],
              ["Maximum reimbursement", providerRaw?.MaxReimbursement != null ? currency(Number(providerRaw?.MaxReimbursement)) : "—"],
              ["Std. reimbursement", providerRaw?.StdReimbursement != null ? currency(Number(providerRaw?.StdReimbursement)) : "—"],
              ["Claims / beneficiary", providerRaw?.ClaimsPerBeneficiary != null ? Number(providerRaw?.ClaimsPerBeneficiary) : (provider?.claim_count && provider?.beneficiary_count ? Math.round(provider.claim_count / Math.max(1, provider.beneficiary_count)) : "—")],
              ["Inpatient share", providerRaw?.InpatientShare != null ? `${Math.round(Number(providerRaw?.InpatientShare) * 100)}%` : "—"],
              ["Unique attending physicians", providerRaw?.UniqueAttendingPhysicians != null ? Number(providerRaw?.UniqueAttendingPhysicians) : "—"],
              ["Unique operating physicians", providerRaw?.UniqueOperatingPhysicians != null ? Number(providerRaw?.UniqueOperatingPhysicians) : "—"],
              ["Unique other physicians", providerRaw?.UniqueOtherPhysicians != null ? Number(providerRaw?.UniqueOtherPhysicians) : "—"],
            ].map(([label, value]) => (
              <div key={String(label)}>
                <dt className="text-xs uppercase tracking-wider text-muted-foreground">{label}</dt>
                <dd className="mt-1 text-sm font-medium text-foreground">{String(value ?? "—")}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
       
      <div>
       <h2 className="text-sm font-semibold text-foreground">Model evidence</h2>
       <div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
         {evidence.map((e) => (
           <EvidenceCard key={e.factor} evidence={e} />
         ))}
       </div>
      </div>

      {explanation && (
       <ExplanationCard explanation={explanation} evidence={evidence.slice(0, 3)} />
      )}

      <section className="panel p-4">
        <h3 className="text-sm font-semibold text-foreground">Claim-level model</h3>
        <p className="mt-2 text-sm text-muted-foreground">Not available</p>
        <p className="mt-1 text-sm text-muted-foreground">The current fraud model scores providers rather than individual claims. Claim-level risk is therefore not reported for this claim.</p>
      </section>

      {/* Dataset label: show only if the backend actually includes it */}
      {typeof (claim as any).PotentialFraud !== "undefined" && (
        <section className="panel p-4">
          <h3 className="text-sm font-semibold text-foreground">Claim dataset information</h3>
          <dl className="mt-2 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">Dataset fraud label</dt>
              <dd className="mt-1 text-sm font-medium text-foreground">{String((claim as any).PotentialFraud ?? "—")}</dd>
            </div>
          </dl>
          <p className="mt-2 text-sm text-muted-foreground">This value is sourced directly from the combined claim dataset and represents the dataset's existing label (if any). It is not a model prediction.</p>
        </section>
      )}

      <section className="panel p-6">
        <h2 className="text-sm font-semibold text-foreground">Disclaimer</h2>
        <p className="mt-2 text-sm text-muted-foreground">Risk assessments represent model-generated signals and do not constitute a determination of fraud. Claim-level model scoring is not currently provided by the backend; the above evidence items are dataset-derived analytical signals for investigator review.</p>
      </section>
    </div>
  );
}
