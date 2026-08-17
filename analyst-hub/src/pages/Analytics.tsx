import { useEffect, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState, LoadingState } from "@/components/common/States";
import {
  ChartPanel,
  ClaimTypeChart,
  ReimbursementByRiskChart,
  RiskDistributionChart,
} from "@/components/dashboard/Charts";
import { StatCard } from "@/components/common/StatCard";
import { getDashboardSummary } from "@/services/mockApi";
import type { DashboardSummary } from "@/types";

export function Analytics() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setData(null);
    getDashboardSummary().then(setData).catch(() => setError("Unable to load analytics."));
  };

  useEffect(load, []);

  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!data) return <LoadingState label="Loading analytics…" />;

  const exposure = data.reimbursement_by_risk.reduce((s, r) => s + r.amount, 0);
  const flagged = data.high_risk_cases;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Risk Analytics"
        subtitle="Portfolio-level risk distribution and reimbursement exposure."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard
          label="Total Reimbursement"
          value={`$${(exposure / 1_000_000).toFixed(1)}M`}
          sublabel="Across scored claims"
        />
        <StatCard
          label="Flagged Exposure"
          value={flagged.toLocaleString()}
          sublabel="Critical + high risk claims"
          tone="critical"
        />
        <StatCard
          label="Flag Rate"
          value={`${((flagged / data.total_claims) * 100).toFixed(2)}%`}
          sublabel="Share of dataset flagged"
          tone="info"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Risk Distribution" description="Claims by model risk level">
          <RiskDistributionChart data={data.risk_distribution} />
        </ChartPanel>
        <ChartPanel title="Reimbursement by Risk" description="Dollars exposed per risk band">
          <ReimbursementByRiskChart data={data.reimbursement_by_risk} />
        </ChartPanel>
        <ChartPanel title="Claim Mix" description="Inpatient vs outpatient volume">
          <ClaimTypeChart data={data.claim_type_distribution} />
        </ChartPanel>
        <ChartPanel title="Top Risky Providers" description="Highest provider risk scores">
          <ul className="divide-y divide-border">
            {data.top_risky_providers.slice(0, 6).map((p) => (
              <li key={p.provider_id} className="flex items-center justify-between py-2.5 text-sm">
                <span className="font-mono text-xs">{p.provider_id}</span>
                <span className="tabular font-semibold text-risk-critical">{p.risk_score}</span>
              </li>
            ))}
          </ul>
        </ChartPanel>
      </div>
    </div>
  );
}
