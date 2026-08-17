import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatCard } from "@/components/common/StatCard";
import { PeerComparison } from "@/components/explanation/PeerComparison";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/common/DataTable";
import { api, getProvider, getProviders, predictProvider } from "@/services/api";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectProviderReportData } from "@/services/reportService";
import type { Claim, Provider } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
const count = (v: number) => v.toLocaleString("en-US");

export function ProviderDetails() {
  const { providerId } = useParams({ from: "/_shell/providers/$providerId" });
  const [provider, setProvider] = useState<Provider | null>(null);
  const [peers, setPeers] = useState<Provider[]>([]);
  const [providerPrediction, setProviderPrediction] = useState<{ fraud_probability: number; threshold?: number; decision?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [relatedClaims, setRelatedClaims] = useState<Claim[]>([]);
  const [claimsMeta, setClaimsMeta] = useState<{ total: number; page_size: number; total_pages: number } | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch provider record
      const p = await getProvider(providerId);
      setProvider(p ?? null);

      // Determine whether the provider GET already includes prediction fields.
      try {
        // Fetch raw backend provider record to check for fraud_probability without relying on mapProvider internals
        const rawResp = await api.get(`/providers/${encodeURIComponent(providerId)}`).catch(() => null);
        const backendProvider = rawResp?.data?.provider;

        if (backendProvider && typeof backendProvider.fraud_probability === "number") {
          // Use the backend-provided prediction from the provider GET
          setProviderPrediction({
            fraud_probability: Number(backendProvider.fraud_probability),
            ...(typeof backendProvider.threshold === "number" ? { threshold: backendProvider.threshold } : {}),
            ...(typeof backendProvider.decision === "string" ? { decision: backendProvider.decision } : {}),
          });
        } else {
          // Fall back to calling POST /predict as authoritative if GET does not include it
          try {
            const pred = await predictProvider(providerId).catch(() => null);
            setProviderPrediction(pred ?? null);
          } catch (err) {
            setProviderPrediction(null);
          }
        }
      } catch (err) {
        setProviderPrediction(null);
      }

      // Fetch providers for peer comparisons. Use a large page_size to reduce the number of requests
      const pageSize = 100;
      const first = await getProviders(1, pageSize);
      const providersAccum: Provider[] = first.providers ?? [];
      const totalPages = first.total_pages ?? 1;

      // If multiple pages, fetch remaining pages sequentially to keep network usage reasonable
      for (let page = 2; page <= totalPages; page++) {
        try {
          const resp = await getProviders(page, pageSize);
          providersAccum.push(...(resp.providers ?? []));
        } catch (err) {
          // If further pages fail, stop and continue with what we have
          break;
        }
      }

      // Exclude the selected provider from peer averages
      const peersList = providersAccum.filter((x) => x.provider_id !== p?.provider_id);
      setPeers(peersList);

      // Fetch related claims for this provider (first page). Use page_size=50 to cover most providers without fetching everything.
      try {
        const claimsResp = await (await import("@/services/api")).getClaims(1, 50, providerId);
        setRelatedClaims(claimsResp.claims ?? []);
        setClaimsMeta({ total: claimsResp.total, page_size: claimsResp.page_size, total_pages: claimsResp.total_pages });
      } catch (err) {
        // Non-fatal: show no related claims
        setRelatedClaims([]);
        setClaimsMeta(null);
      }
    } catch (err) {
      console.error(err);
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
  if (!provider)
    return <EmptyState title="Provider not found" description={`No provider with ID ${providerId}.`} />;

  const avg = (fn: (p: Provider) => number) =>
    peers.length ? Math.round(peers.reduce((s, p) => s + fn(p), 0) / peers.length) : 0;

  const claimColumns: Column<Claim>[] = [
    { key: "claim_id", header: "Claim ID", render: (row: import("@/types").Claim) => (
      <Link to="/claims/$claimId" params={{ claimId: row.claim_id }} className="font-medium text-primary">{row.claim_id}</Link>
    ) },
    { key: "type", header: "Type", render: (row: import("@/types").Claim) => row.claim_type },
    { key: "reimb", header: "Reimbursement", align: "right", render: (row: import("@/types").Claim) => currency(row.reimbursement) },
    { key: "start", header: "Start", render: (row: import("@/types").Claim) => row.claim_start_date },
    { key: "end", header: "End", render: (row: import("@/types").Claim) => row.claim_end_date },
    { key: "bene", header: "Beneficiary", render: (row: import("@/types").Claim) => row.bene_id || "—" },
    // Show risk only if backend provided a non-zero risk_score
    { key: "risk", header: "Claim risk", render: () => "Not available", className: "w-28" },
  ];

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/providers">
          <ArrowLeft className="size-4" /> Back to providers
        </Link>
      </Button>

      <PageHeader
        title={`Provider ${provider.provider_id}`}
        subtitle="Billing profile and peer-cohort comparison."
        actions={
          <div className="flex items-center gap-2">
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
                  score={Number(((providerPrediction.fraud_probability ?? 0) * 100).toFixed(2))}
                />
                <div className="text-sm">
                  <div className="font-medium">Decision: {providerPrediction.decision ?? "—"}</div>
                  <div className="text-muted-foreground text-xs">Threshold: {providerPrediction.threshold ?? "Not available"}</div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Provider risk prediction unavailable</div>
            )}

            <ReportButton
              type="provider"
              label="Download Provider Report"
              mode="download"
              build={async () => {
                const data = await collectProviderReportData(provider.provider_id);
                return data ? { type: "provider", data } : null;
              }}
            />
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Claims" value={count(provider.claim_count)} sublabel="Total submitted" />
        <StatCard label="Beneficiaries" value={count(provider.beneficiary_count)} sublabel="Unique patients" tone="info" />
        <StatCard label="Total Reimbursement" value={currency(provider.total_reimbursement)} sublabel="Paid to date" />
        <StatCard label="Avg / Claim" value={currency(provider.average_reimbursement)} sublabel="Per claim average" tone="critical" />
      </div>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Peer comparison</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Provider metrics versus the average of the scored provider cohort.
        </p>
        <div className="mt-5">
          <PeerComparison
            metrics={[
              { metric: "Claims submitted", provider: provider.claim_count, peer: avg((p) => p.claim_count), format: count },
              { metric: "Unique beneficiaries", provider: provider.beneficiary_count, peer: avg((p) => p.beneficiary_count), format: count },
              { metric: "Average reimbursement", provider: provider.average_reimbursement, peer: avg((p) => p.average_reimbursement), format: currency },
              { metric: "Inpatient claims", provider: provider.inpatient_claims, peer: avg((p) => p.inpatient_claims), format: count },
              { metric: "Outpatient claims", provider: provider.outpatient_claims, peer: avg((p) => p.outpatient_claims), format: count },
            ]}
          />
        </div>
      </section>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Related claims</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">Showing recent claims for this provider. Click a claim to view details.</p>

        <div className="mt-4">
          {relatedClaims.length === 0 ? (
            <EmptyState title="No claims found" description={claimsMeta ? `Provider has no claims.` : `No related claims available.`} />
          ) : (
            <div>
              <div className="mb-3 text-xs text-muted-foreground">Showing {relatedClaims.length}{claimsMeta ? ` of ${claimsMeta.total}` : ""} claims</div>

              <DataTable
                data={relatedClaims}
                columns={claimColumns}
                rowKey={(r) => r.claim_id}
                pageSize={10}
                searchable={(r) => `${r.claim_id} ${r.bene_id} ${r.claim_type}`}
                emptyTitle="No related claims"
              />

              {claimsMeta && claimsMeta.total_pages > 1 && (
                <div className="mt-3 text-xs">
                  Showing first page of claims. To view all claims, visit the <Link to="/claims">Claims list</Link> and filter by provider.
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
