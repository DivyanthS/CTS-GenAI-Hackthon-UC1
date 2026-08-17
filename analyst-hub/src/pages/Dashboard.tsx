import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, FileStack, Users, UserRound } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { LoadingState, ErrorState } from "@/components/common/States";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import {
  ChartPanel,
  ClaimTypeChart,
  ReimbursementByRiskChart,
  RiskDistributionChart,
} from "@/components/dashboard/Charts";
import { getDashboardSummary } from "@/services/mockApi";
import { ReportTypeSelector } from "@/components/reports/ReportTypeSelector";
import { collectDashboardReportData } from "@/services/reportService";
import type { DashboardSummary } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setData(null);
    getDashboardSummary().then(setData).catch(() => setError("Unable to load dashboard summary."));
  };

  useEffect(load, []);

  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!data) return <LoadingState label="Loading dashboard summary…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Claims Payment Integrity Dashboard"
        subtitle="Monitor suspicious claims, provider behavior and investigation workload."
        actions={
          <ReportTypeSelector
            label="Generate Report"
            options={[
              { type: "executive", build: async () => ({ type: "executive", data: await collectDashboardReportData() }) },
              { type: "analysis-summary", build: async () => ({ type: "analysis-summary", data: await collectDashboardReportData() }) },
            ]}
          />
        }
      />

      <p className="rounded-md border border-dashed border-border bg-card px-4 py-2.5 text-xs text-muted-foreground">
        Prototype values derived from the current combined dataset. Risk scores are model outputs,
        not determinations of fraud.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Claims" value={data.total_claims.toLocaleString()} sublabel="Combined dataset rows" icon={FileStack} />
        <StatCard label="Providers" value={data.providers.toLocaleString()} sublabel="Unique provider IDs" icon={Users} tone="info" />
        <StatCard label="Beneficiaries" value={data.beneficiaries.toLocaleString()} sublabel="Unique beneficiary IDs" icon={UserRound} />
        <StatCard
          label="High Risk Cases"
          value={data.high_risk_cases.toLocaleString()}
          sublabel="Critical + High risk claims"
          icon={AlertTriangle}
          tone="critical"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartPanel title="Risk Distribution" description="Scored claims by model risk level" >
          <RiskDistributionChart data={data.risk_distribution} />
        </ChartPanel>
        <ChartPanel title="Claim Type Distribution" description="Inpatient vs outpatient volume">
          <ClaimTypeChart data={data.claim_type_distribution} />
        </ChartPanel>
        <ChartPanel title="Reimbursement by Risk Level" description="Exposure in reimbursed dollars">
          <ReimbursementByRiskChart data={data.reimbursement_by_risk} />
        </ChartPanel>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="panel overflow-hidden">
          <header className="flex items-center justify-between border-b border-border p-5">
            <div>
              <h3 className="text-sm font-semibold">Top Risky Providers</h3>
              <p className="mt-0.5 text-xs text-muted-foreground">Provider-level model risk</p>
            </div>
            <Link to="/providers" className="text-xs font-medium text-primary hover:underline">
              View all
            </Link>
          </header>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/60 text-xs uppercase tracking-wider text-muted-foreground">
                  <th scope="col" className="px-5 py-2.5 text-left font-semibold">Provider</th>
                  <th scope="col" className="px-5 py-2.5 text-left font-semibold">Risk Score</th>
                  <th scope="col" className="px-5 py-2.5 text-right font-semibold">Claims</th>
                  <th scope="col" className="px-5 py-2.5 text-right font-semibold">Reimbursement</th>
                </tr>
              </thead>
              <tbody>
                {data.top_risky_providers.map((p) => (
                  <tr key={p.provider_id} className="border-b border-border/70 last:border-0">
                    <td className="px-5 py-3">
                      <Link
                        to="/providers/$providerId"
                        params={{ providerId: p.provider_id }}
                        className="font-mono text-xs font-medium text-primary hover:underline"
                      >
                        {p.provider_id}
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <RiskBadge level={p.risk_level} score={p.risk_score} />
                    </td>
                    <td className="px-5 py-3 text-right tabular">{p.claim_count.toLocaleString()}</td>
                    <td className="px-5 py-3 text-right tabular">{currency(p.total_reimbursement)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel overflow-hidden">
          <header className="flex items-center justify-between border-b border-border p-5">
            <div>
              <h3 className="text-sm font-semibold">Recent Investigation Cases</h3>
              <p className="mt-0.5 text-xs text-muted-foreground">Latest triaged cases</p>
            </div>
            <Link to="/investigations" className="text-xs font-medium text-primary hover:underline">
              Open queue
            </Link>
          </header>
          <ul className="divide-y divide-border">
            {data.recent_cases.map((c) => (
              <li key={c.case_id} className="flex items-center justify-between gap-3 px-5 py-3">
                <div className="min-w-0">
                  <Link
                    to="/investigations/$caseId"
                    params={{ caseId: c.case_id }}
                    className="font-mono text-xs font-medium text-primary hover:underline"
                  >
                    {c.case_id}
                  </Link>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {c.claim_id} · {c.provider_id} · {c.assigned_to}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <RiskBadge level={c.priority} score={c.risk_score} />
                  <StatusBadge status={c.status} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
