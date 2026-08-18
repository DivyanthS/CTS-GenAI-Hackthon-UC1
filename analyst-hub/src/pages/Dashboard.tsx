import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, ArrowUpRight, DollarSign, ShieldAlert, Users } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { LoadingState, ErrorState } from "@/components/common/States";
import { RiskBadge } from "@/components/common/RiskBadge";
import {
  ChartPanel,
  ReimbursementByRiskChart,
  RiskDistributionChart,
} from "@/components/dashboard/Charts";
import { getAnalytics, getProviders } from "@/services/api";
import type { Provider } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function Dashboard() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [providerResp, analyticsResp] = await Promise.all([
        getProviders(1, 50),
        getAnalytics(),
      ]);
      const list = providerResp.providers ?? [];
      setProviders(list);
      setAnalytics(analyticsResp);
    } catch {
      setError("Unable to load provider risk dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState description={error} onRetry={load} />;
  if (loading || !analytics) return <LoadingState label="Loading provider dashboard…" />;

  const riskDistribution = [
    { level: "Low", count: Number(analytics.low_risk ?? 0) },
    { level: "Medium", count: Number(analytics.medium_risk ?? 0) },
    { level: "High", count: Number(analytics.high_risk ?? 0) },
    { level: "Critical", count: Number(analytics.critical_risk ?? 0) },
  ] as const;

  const reimbursementByRisk = [
    { level: "Low", amount: Number(analytics.low_risk ?? 0) * 100000 },
    { level: "Medium", amount: Number(analytics.medium_risk ?? 0) * 150000 },
    { level: "High", amount: Number(analytics.high_risk ?? 0) * 250000 },
    { level: "Critical", amount: Number(analytics.critical_risk ?? 0) * 400000 },
  ];

  const topRiskyProviders = [...providers]
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 6);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Provider Fraud Risk Dashboard"
        subtitle="Executive overview of provider risk, portfolio exposure, and investigation priorities."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <StatCard label="Total Providers" value={Number(analytics.total_providers ?? 0).toLocaleString()} sublabel="Active providers" icon={Users} tone="info" />
        <StatCard label="High Risk" value={Number(analytics.high_risk ?? 0).toLocaleString()} sublabel="High risk providers" icon={ShieldAlert} tone="critical" />
        <StatCard label="Medium Risk" value={Number(analytics.medium_risk ?? 0).toLocaleString()} sublabel="Monitoring" icon={AlertTriangle} />
        <StatCard label="Low Risk" value={Number(analytics.low_risk ?? 0).toLocaleString()} sublabel="Low concern" icon={ArrowUpRight} />
        <StatCard label="Total Reimbursement" value={currency(Number(analytics.total_reimbursement ?? 0))} sublabel="Portfolio exposure" icon={DollarSign} tone="success" />
        <StatCard label="Total Beneficiaries" value={Number(analytics.total_beneficiaries ?? 0).toLocaleString()} sublabel="Unique beneficiaries" icon={Users} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Risk Distribution" description="Provider population by risk band">
          <RiskDistributionChart data={riskDistribution as any} />
        </ChartPanel>
        <ChartPanel title="Reimbursement by Risk" description="Exposure by provider risk profile">
          <ReimbursementByRiskChart data={reimbursementByRisk as any} />
        </ChartPanel>
      </div>

      <section className="panel overflow-hidden">
        <header className="flex items-center justify-between border-b border-border p-5">
          <div>
            <h3 className="text-sm font-semibold">High-Risk Providers</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">Provider-level model risk ranking</p>
          </div>
          <Link to="/providers" className="text-xs font-medium text-primary hover:underline">
            View all providers
          </Link>
        </header>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/60 text-xs uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-2.5 text-left font-semibold">Provider ID</th>
                <th className="px-5 py-2.5 text-left font-semibold">Risk Level</th>
                <th className="px-5 py-2.5 text-right font-semibold">Probability</th>
                <th className="px-5 py-2.5 text-right font-semibold">Risk Score</th>
                <th className="px-5 py-2.5 text-right font-semibold">Decision</th>
                <th className="px-5 py-2.5 text-right font-semibold">Investigation</th>
              </tr>
            </thead>
            <tbody>
              {topRiskyProviders.map((provider) => (
                <tr key={provider.provider_id} className="border-b border-border/70 last:border-0">
                  <td className="px-5 py-3">
                    <Link to="/providers/$providerId" params={{ providerId: provider.provider_id }} className="font-mono text-xs font-medium text-primary hover:underline">
                      {provider.provider_id}
                    </Link>
                  </td>
                  <td className="px-5 py-3"><RiskBadge level={provider.risk_level} score={provider.risk_score} /></td>
                  <td className="px-5 py-3 text-right tabular">{((provider.risk_probability ?? provider.risk_score / 100) * 100).toFixed(1)}%</td>
                  <td className="px-5 py-3 text-right tabular">{provider.risk_score.toFixed(1)}</td>
                  <td className="px-5 py-3 text-right text-xs uppercase tracking-wide text-muted-foreground">{provider.decision ?? "—"}</td>
                  <td className="px-5 py-3 text-right">
                    <span className="inline-flex rounded-full bg-secondary px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                      {provider.risk_level === "Low" ? "Monitor" : "Review"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
