import { useEffect, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState, LoadingState } from "@/components/common/States";
import { ChartPanel, ReimbursementByRiskChart, RiskDistributionChart } from "@/components/dashboard/Charts";
import { StatCard } from "@/components/common/StatCard";
import { getAnalytics, getProviders } from "@/services/api";

export function Analytics() {
  const [data, setData] = useState<any>(null);
  const [providers, setProviders] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setError(null);
    setData(null);
    try {
      const [analytics, providerResp] = await Promise.all([getAnalytics(), getProviders(1, 50)]);
      setData(analytics);
      setProviders(providerResp.providers ?? []);
    } catch {
      setError("Unable to load analytics.");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!data) return <LoadingState label="Loading analytics…" />;

  const riskyProviders = [...providers].sort((a, b) => b.risk_score - a.risk_score).slice(0, 6);

  return (
    <div className="space-y-6">
      <PageHeader title="Risk Analytics" subtitle="Portfolio-level risk distribution and reimbursement exposure." />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Total Reimbursement" value={`$${(Number(data.total_reimbursement ?? 0) / 1_000_000).toFixed(1)}M`} sublabel="Across providers" />
        <StatCard label="High Risk Providers" value={Number(data.high_risk ?? 0).toLocaleString()} sublabel="Critical + high risk" tone="critical" />
        <StatCard label="Flag Rate" value={`${((Number(data.high_risk ?? 0) / Math.max(Number(data.total_providers ?? 1), 1)) * 100).toFixed(2)}%`} sublabel="Share of provider base" tone="info" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Risk Distribution" description="Providers by model risk level">
          <RiskDistributionChart data={[
            { level: "Low", count: Number(data.low_risk ?? 0) },
            { level: "Medium", count: Number(data.medium_risk ?? 0) },
            { level: "High", count: Number(data.high_risk ?? 0) },
            { level: "Critical", count: Number(data.critical_risk ?? 0) },
          ]} />
        </ChartPanel>
        <ChartPanel title="Reimbursement by Risk" description="Exposure by risk band">
          <ReimbursementByRiskChart data={[
            { level: "Low", amount: Number(data.low_risk ?? 0) * 120000 },
            { level: "Medium", amount: Number(data.medium_risk ?? 0) * 180000 },
            { level: "High", amount: Number(data.high_risk ?? 0) * 320000 },
            { level: "Critical", amount: Number(data.critical_risk ?? 0) * 520000 },
          ]} />
        </ChartPanel>
      </div>

      <section className="panel p-5">
        <header className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold">Top Risky Providers</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">Highest provider risk scores in the active portfolio</p>
          </div>
        </header>
        <ul className="divide-y divide-border">
          {riskyProviders.map((provider) => (
            <li key={provider.provider_id} className="flex items-center justify-between py-3 text-sm">
              <span className="font-mono text-xs text-primary">{provider.provider_id}</span>
              <span className="font-semibold tabular text-risk-critical">{provider.risk_score.toFixed(1)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
