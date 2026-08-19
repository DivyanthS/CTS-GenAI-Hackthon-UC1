
import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import {
  ArrowLeft,
  CheckCircle2,
  Lock,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatCard } from "@/components/common/StatCard";
import { PeerComparison } from "@/components/explanation/PeerComparison";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { getProvider, getProviders } from "@/services/mockApi";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectProviderReportData } from "@/services/reportService";
import type { Provider } from "@/types";

const currency = (v: number) =>
  `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

const count = (v: number) => v.toLocaleString("en-US");

export function ProviderDetails() {
  const { providerId } = useParams({
    from: "/_shell/providers/$providerId",
  });

  const [provider, setProvider] = useState<Provider | null>(null);
  const [peers, setPeers] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Investigation decision
  const [investigationDecision, setInvestigationDecision] = useState<
    "YES" | "NO" | null
  >(null);

  const load = () => {
    setLoading(true);
    setError(null);

    Promise.all([getProvider(providerId), getProviders()])
      .then(([p, all]) => {
        setProvider(p ?? null);
        setPeers(all);
      })
      .catch(() => setError("Unable to load provider profile."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [providerId]);

  if (loading) {
    return <LoadingState label="Loading provider profile…" />;
  }

  if (error) {
    return <ErrorState description={error} onRetry={load} />;
  }

  if (!provider) {
    return (
      <EmptyState
        title="Provider not found"
        description={`No provider with ID ${providerId}.`}
      />
    );
  }

  const avg = (fn: (p: Provider) => number) =>
    peers.length
      ? Math.round(
          peers.reduce((s, p) => s + fn(p), 0) / peers.length,
        )
      : 0;

  // Mock SHAP explanation based on the existing provider/peer metrics.
  const shapExplanation = [
    {
      feature: "Outpatient claims",
      value: 0.31,
      impact: "High impact",
    },
    {
      feature: "Claims submitted",
      value: 0.28,
      impact: "High impact",
    },
    {
      feature: "Unique beneficiaries",
      value: 0.24,
      impact: "High impact",
    },
    {
      feature: "Average reimbursement",
      value: 0.12,
      impact: "Moderate impact",
    },
    {
      feature: "Inpatient claims",
      value: 0.08,
      impact: "Low impact",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/providers">
          <ArrowLeft className="size-4" />
          Back to providers
        </Link>
      </Button>

      {/* Page Header */}
      <PageHeader
        title={`Provider ${provider.provider_id}`}
        subtitle="Billing profile and peer-cohort comparison."
        actions={
          <div className="flex items-center gap-2">
            <RiskBadge
              level={provider.risk_level}
              score={provider.risk_score}
            />

            <ReportButton
              type="provider"
              label="Download Provider Report"
              mode="download"
              build={async () => {
                const data = await collectProviderReportData(
                  provider.provider_id,
                );

                return data
                  ? {
                      type: "provider",
                      data,
                    }
                  : null;
              }}
            />
          </div>
        }
      />

      {/* Provider Statistics */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Claims"
          value={count(provider.claim_count)}
          sublabel="Total submitted"
        />

        <StatCard
          label="Beneficiaries"
          value={count(provider.beneficiary_count)}
          sublabel="Unique patients"
          tone="info"
        />

        <StatCard
          label="Total Reimbursement"
          value={currency(provider.total_reimbursement)}
          sublabel="Paid to date"
        />

        <StatCard
          label="Avg / Claim"
          value={currency(provider.average_reimbursement)}
          sublabel="Per claim average"
          tone="critical"
        />
      </div>

      {/* Peer Comparison */}
      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Peer comparison</h2>

        <p className="mt-0.5 text-xs text-muted-foreground">
          Provider metrics versus the average of the scored provider cohort.
        </p>

        <div className="mt-5">
          <PeerComparison
            metrics={[
              {
                metric: "Claims submitted",
                provider: provider.claim_count,
                peer: avg((p) => p.claim_count),
                format: count,
              },
              {
                metric: "Unique beneficiaries",
                provider: provider.beneficiary_count,
                peer: avg((p) => p.beneficiary_count),
                format: count,
              },
              {
                metric: "Average reimbursement",
                provider: provider.average_reimbursement,
                peer: avg((p) => p.average_reimbursement),
                format: currency,
              },
              {
                metric: "Inpatient claims",
                provider: provider.inpatient_claims,
                peer: avg((p) => p.inpatient_claims),
                format: count,
              },
              {
                metric: "Outpatient claims",
                provider: provider.outpatient_claims,
                peer: avg((p) => p.outpatient_claims),
                format: count,
              },
            ]}
          />
        </div>
      </section>

      {/* SHAP Explanation */}
      <section className="panel overflow-hidden">
        <div className="border-b border-border p-5">
          <div className="flex items-center gap-2">
            <TrendingUp className="size-4 text-risk-critical" />

            <h2 className="text-sm font-semibold">
              SHAP Explanation
            </h2>
          </div>

          <p className="mt-1 text-xs text-muted-foreground">
            Key factors influencing this provider's risk score.
          </p>
        </div>

        <div className="space-y-4 p-5">
          {shapExplanation.map((item) => {
            const width = (item.value / 0.31) * 100;

            return (
              <div key={item.feature}>
                <div className="mb-1.5 flex items-center justify-between gap-4">
                  <span className="text-sm font-medium">
                    {item.feature}
                  </span>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold tabular text-risk-critical">
                      +{item.value.toFixed(2)}
                    </span>

                    <span className="text-xs text-muted-foreground">
                      {item.impact}
                    </span>
                  </div>
                </div>

                <div className="h-2 rounded-full bg-secondary">
                  <div
                    className="h-2 rounded-full bg-risk-critical"
                    style={{ width: `${width}%` }}
                    aria-hidden
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Key Explanation */}
        <div className="border-t border-border bg-secondary/30 px-5 py-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Key Explanation
          </p>

          <p className="mt-2 text-base font-medium leading-7 text-foreground">
            This provider's elevated risk is primarily driven by
            significantly higher outpatient claims, total claims submitted,
            and unique beneficiaries compared with the peer average.
          </p>
        </div>
      </section>

      {/* Investigation Decision */}
      <section className="panel p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold">
              Investigation Decision
            </h2>

            <p className="mt-0.5 text-xs text-muted-foreground">
              Decide whether this provider should be sent for investigation.
            </p>
          </div>

          {investigationDecision && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Lock className="size-3.5" />
              Decision Locked
            </div>
          )}
        </div>

        {/* YES / NO buttons */}
        {!investigationDecision ? (
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <Button
              type="button"
              variant="outline"
              className="h-12 justify-start gap-2"
              onClick={() => setInvestigationDecision("YES")}
            >
              <CheckCircle2 className="size-5 text-success" />

              <span>YES — Send for Investigation</span>
            </Button>

            <Button
              type="button"
              variant="outline"
              className="h-12 justify-start gap-2"
              onClick={() => setInvestigationDecision("NO")}
            >
              <XCircle className="size-5 text-muted-foreground" />

              <span>NO — Do Not Investigate</span>
            </Button>
          </div>
        ) : (
          /* Locked decision */
          <div className="mt-5 rounded-lg border border-border bg-secondary/40 p-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                {investigationDecision === "YES" ? (
                  <CheckCircle2 className="size-5 text-success" />
                ) : (
                  <XCircle className="size-5 text-muted-foreground" />
                )}

                <div>
                  <p className="text-sm font-semibold">
                    {investigationDecision === "YES"
                      ? "Sent for Investigation"
                      : "Investigation Not Required"}
                  </p>

                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Status:{" "}
                    {investigationDecision === "YES"
                      ? "Pending Investigation"
                      : "Not Required"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="rounded-md bg-secondary px-2 py-1 text-xs font-medium">
                  {investigationDecision}
                </span>

                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Lock className="size-3.5" />
                  Locked
                </span>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

