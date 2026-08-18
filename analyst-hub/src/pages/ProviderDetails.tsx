import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft, Download, FileText, ShieldCheck, TrendingUp } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatCard } from "@/components/common/StatCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { api, getProvider, getProviders, predictProvider } from "@/services/api";
import type { Provider, RiskFactor } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
const count = (v: number) => v.toLocaleString("en-US");

export function ProviderDetails() {
  const { providerId } = useParams({ from: "/_shell/providers/$providerId" });
  const [provider, setProvider] = useState<Provider | null>(null);
  const [peers, setPeers] = useState<Provider[]>([]);
  const [providerPrediction, setProviderPrediction] = useState<{ fraud_probability: number; threshold?: number; decision?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<"NEW" | "UNDER REVIEW" | "ESCALATED" | "RESOLVED">("NEW");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const p = await getProvider(providerId);
      setProvider(p);

      try {
        const rawResp = await api.get(`/providers/${encodeURIComponent(providerId)}`).catch(() => null);
        const backendProvider = rawResp?.data?.provider;
        if (backendProvider && typeof backendProvider.fraud_probability === "number") {
          setProviderPrediction({
            fraud_probability: Number(backendProvider.fraud_probability),
            ...(typeof backendProvider.threshold === "number" ? { threshold: backendProvider.threshold } : {}),
            ...(typeof backendProvider.decision === "string" ? { decision: backendProvider.decision } : {}),
          });
        } else {
          const pred = await predictProvider(providerId).catch(() => null);
          setProviderPrediction(pred ?? null);
        }
      } catch {
        setProviderPrediction(null);
      }

      const pageSize = 100;
      const first = await getProviders(1, pageSize);
      const providerPool = [...(first.providers ?? [])];
      const totalPages = first.total_pages ?? 1;

      for (let page = 2; page <= totalPages; page += 1) {
        const resp = await getProviders(page, pageSize).catch(() => null);
        if (!resp) break;
        providerPool.push(...(resp.providers ?? []));
      }

      setPeers(providerPool.filter((x) => x.provider_id !== p.provider_id));
    } catch {
      setError("Unable to load provider profile.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [providerId]);

  if (loading) return <LoadingState label="Loading provider profile…" />;
  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!provider) return <EmptyState title="Provider not found" description={`No provider with ID ${providerId}.`} />;

  const avg = (fn: (p: Provider) => number) =>
    peers.length ? Math.round(peers.reduce((s, p) => s + fn(p), 0) / peers.length) : 0;

  const riskProbability = Number(provider.risk_probability ?? provider.risk_score / 100);
  const riskLevel = provider.risk_level ?? (riskProbability >= 0.75 ? "Critical" : riskProbability >= 0.5 ? "High" : riskProbability >= 0.23 ? "Medium" : "Low");
  const factors = provider.risk_factors ?? [];

  const downloadPdf = async () => {
    try {
      const response = await api.get(`/reports/${encodeURIComponent(provider.analysis_run_id ?? "latest")}/pdf`, { responseType: "blob" });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = `Provider_${provider.provider_id}_Risk_Report.pdf`;
      link.click();
      URL.revokeObjectURL(href);
    } catch {
      setError("Unable to download the provider PDF report.");
    }
  };

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/providers"><ArrowLeft className="size-4" /> Back to providers</Link>
      </Button>

      <PageHeader
        title={`Provider ${provider.provider_id}`}
        subtitle="Billing profile, model score, and peer performance context."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <RiskBadge level={riskLevel} score={provider.risk_score} />
            <Button variant="outline" size="sm" onClick={() => window.open(`/reports/${provider.analysis_run_id ?? "latest"}`)}>
              <FileText className="size-4" /> View Report
            </Button>
            <Button variant="default" size="sm" onClick={downloadPdf}>
              <Download className="size-4" /> Download PDF
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Claims" value={count(provider.claim_count)} sublabel="Submitted claims" />
        <StatCard label="Unique Beneficiaries" value={count(provider.beneficiary_count)} sublabel="Active patients" tone="info" />
        <StatCard label="Total Reimbursement" value={currency(provider.total_reimbursement)} sublabel="Portfolio payment" />
        <StatCard label="Avg / Claim" value={currency(provider.average_reimbursement)} sublabel="Per-claim average" tone="critical" />
      </div>

      <section className="grid gap-4 lg:grid-cols-[1.4fr_0.6fr]">
        <div className="panel p-6">
          <h2 className="text-sm font-semibold">Risk Assessment</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Risk Probability</div><div className="mt-2 text-xl font-semibold tabular">{(riskProbability * 100).toFixed(1)}%</div></div>
            <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Risk Score</div><div className="mt-2 text-xl font-semibold tabular">{provider.risk_score.toFixed(1)}</div></div>
            <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Risk Level</div><div className="mt-2"><RiskBadge level={riskLevel} score={provider.risk_score} /></div></div>
            <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Decision</div><div className="mt-2 text-sm font-medium text-foreground">{provider.decision ?? "Not available"}</div></div>
          </div>
        </div>

        <div className="panel p-6">
          <h2 className="text-sm font-semibold">Investigation Required?</h2>
          <div className="mt-4 space-y-3">
            <Button className="w-full justify-center" variant="destructive" onClick={() => setStatus("NEW")}>YES — SEND TO INVESTIGATION</Button>
            <Button className="w-full justify-center" variant="outline" onClick={() => setStatus("RESOLVED")}>NO — MONITOR</Button>
            <div className="rounded-md border border-dashed border-border bg-secondary/30 p-3 text-xs text-muted-foreground">
              <div className="font-medium text-foreground">Model decision</div>
              <div className="mt-1">{provider.decision ?? "Not available"}</div>
              <div className="mt-3 font-medium text-foreground">Human investigation status</div>
              <div className="mt-1">{status}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Provider Summary</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
          <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Claims</div><div className="mt-2 text-lg font-semibold tabular">{count(provider.claim_count)}</div></div>
          <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Beneficiaries</div><div className="mt-2 text-lg font-semibold tabular">{count(provider.beneficiary_count)}</div></div>
          <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Reimb.</div><div className="mt-2 text-lg font-semibold tabular">{currency(provider.total_reimbursement)}</div></div>
          <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Avg Reimb.</div><div className="mt-2 text-lg font-semibold tabular">{currency(provider.average_reimbursement)}</div></div>
          <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Max Reimb.</div><div className="mt-2 text-lg font-semibold tabular">{currency(provider.max_reimbursement ?? 0)}</div></div>
          <div className="rounded-md border border-border bg-secondary/40 p-3"><div className="text-[11px] uppercase tracking-wider text-muted-foreground">Claims / Beneficiary</div><div className="mt-2 text-lg font-semibold tabular">{Number(provider.claims_per_beneficiary ?? provider.claim_count / Math.max(provider.beneficiary_count, 1)).toFixed(2)}</div></div>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="panel p-6">
          <h2 className="text-sm font-semibold">Risk Factors</h2>
          <div className="mt-5 space-y-3">
            {factors.length === 0 ? (
              <EmptyState title="No risk factors" description="No model risk factors are available for this provider yet." />
            ) : (
              factors.map((factor: RiskFactor, index: number) => (
                <div key={`${factor.name}-${index}`} className="rounded-md border border-border bg-secondary/30 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{factor.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{factor.impact ?? "Impact not specified"}</p>
                    </div>
                    <span className="rounded-full bg-secondary px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">{factor.severity ?? "Medium"}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                    <div><span className="block text-[10px] uppercase tracking-wider">Observed</span><span className="mt-1 block font-medium text-foreground">{factor.provider_value ?? "—"}</span></div>
                    <div><span className="block text-[10px] uppercase tracking-wider">Benchmark</span><span className="mt-1 block font-medium text-foreground">{factor.benchmark ?? "—"}</span></div>
                    <div><span className="block text-[10px] uppercase tracking-wider">Δ %</span><span className="mt-1 block font-medium text-foreground">{factor.difference_percent ?? "—"}</span></div>
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">{factor.explanation ?? "No explanation available."}</p>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel p-6">
          <h2 className="text-sm font-semibold">Provider Characteristics</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Average Patient Age</div><div className="mt-2 text-lg font-semibold tabular">{provider.average_patient_age ?? "—"}</div></div>
            <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Avg Chronic Conditions</div><div className="mt-2 text-lg font-semibold tabular">{provider.average_chronic_condition_count ?? "—"}</div></div>
            <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Inpatient Share</div><div className="mt-2 text-lg font-semibold tabular">{provider.inpatient_share != null ? `${(provider.inpatient_share * 100).toFixed(1)}%` : "—"}</div></div>
            <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Part A Coverage</div><div className="mt-2 text-lg font-semibold tabular">{provider.average_part_a_coverage != null ? `${(provider.average_part_a_coverage * 100).toFixed(1)}%` : "—"}</div></div>
            <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Part B Coverage</div><div className="mt-2 text-lg font-semibold tabular">{provider.average_part_b_coverage != null ? `${(provider.average_part_b_coverage * 100).toFixed(1)}%` : "—"}</div></div>
            <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Claims / Beneficiary</div><div className="mt-2 text-lg font-semibold tabular">{Number(provider.claims_per_beneficiary ?? provider.claim_count / Math.max(provider.beneficiary_count, 1)).toFixed(2)}</div></div>
          </div>
          <div className="mt-5">
            <Button variant="outline" className="w-full justify-center"><TrendingUp className="size-4" /> View All Provider Features</Button>
          </div>
        </section>
      </div>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Peer Comparison</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Claims</div><div className="mt-2 text-lg font-semibold tabular">{provider.claim_count}</div><div className="mt-1 text-[11px] text-muted-foreground">Peer avg: {avg((p) => p.claim_count)}</div></div>
          <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Beneficiaries</div><div className="mt-2 text-lg font-semibold tabular">{provider.beneficiary_count}</div><div className="mt-1 text-[11px] text-muted-foreground">Peer avg: {avg((p) => p.beneficiary_count)}</div></div>
          <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Avg Reimb.</div><div className="mt-2 text-lg font-semibold tabular">{currency(provider.average_reimbursement)}</div><div className="mt-1 text-[11px] text-muted-foreground">Peer avg: {currency(avg((p) => p.average_reimbursement))}</div></div>
          <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Inpatient</div><div className="mt-2 text-lg font-semibold tabular">{provider.inpatient_claims}</div><div className="mt-1 text-[11px] text-muted-foreground">Peer avg: {avg((p) => p.inpatient_claims)}</div></div>
          <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">Outpatient</div><div className="mt-2 text-lg font-semibold tabular">{provider.outpatient_claims}</div><div className="mt-1 text-[11px] text-muted-foreground">Peer avg: {avg((p) => p.outpatient_claims)}</div></div>
        </div>
      </section>
    </div>
  );
}
