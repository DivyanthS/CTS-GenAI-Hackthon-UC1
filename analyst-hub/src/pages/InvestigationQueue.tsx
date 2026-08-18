import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/common/DataTable";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { getProviders } from "@/services/api";
import type { CaseStatus, RiskLevel } from "@/types";

type InvestigationRow = {
  provider_id: string;
  risk_level: RiskLevel;
  risk_probability: number;
  risk_score: number;
  model_decision: string;
  investigation_status: CaseStatus;
  date_added: string;
  model_version?: string;
};

const STATUSES: (CaseStatus | "All")[] = ["All", "New", "Under Review", "Escalated", "Resolved"];

export function InvestigationQueue() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<InvestigationRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<CaseStatus | "All">("All");

  useEffect(() => {
    const load = async () => {
      try {
        const providerResp = await getProviders(1, 100);
        const saved = JSON.parse(sessionStorage.getItem("investigation-queue") ?? "[]") as Array<{
          provider_id: string;
          investigation_status: CaseStatus;
          date_added: string;
        }>;
        const savedMap = new Map(saved.map((item) => [item.provider_id, item]));

        const nextRows = (providerResp.providers ?? []).map((provider) => {
          const savedItem = savedMap.get(provider.provider_id);
          return {
            provider_id: provider.provider_id,
            risk_level: provider.risk_level,
            risk_probability: Number(provider.risk_probability ?? provider.risk_score / 100),
            risk_score: provider.risk_score,
            model_decision: provider.decision ?? "Not available",
            investigation_status: savedItem?.investigation_status ?? (provider.risk_level === "Low" ? "Resolved" : "New"),
            date_added: savedItem?.date_added ?? new Date().toISOString(),
            model_version: provider.model_version,
          } satisfies InvestigationRow;
        });

        setRows(nextRows.sort((a, b) => b.risk_score - a.risk_score));
      } catch {
        setError("Unable to load the investigation queue.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const filtered = status === "All" ? rows : rows.filter((row) => row.investigation_status === status);

  const columns: Column<InvestigationRow>[] = [
    {
      key: "provider_id",
      header: "Provider ID",
      sortValue: (r) => r.provider_id,
      render: (r) => <span className="font-mono text-xs font-medium text-primary">{r.provider_id}</span>,
    },
    {
      key: "risk_level",
      header: "Risk Level",
      sortValue: (r) => r.risk_score,
      render: (r) => <RiskBadge level={r.risk_level} score={r.risk_score} />,
    },
    {
      key: "risk_probability",
      header: "Probability",
      align: "right",
      sortValue: (r) => r.risk_probability,
      render: (r) => `${(r.risk_probability * 100).toFixed(1)}%`,
    },
    {
      key: "risk_score",
      header: "Risk Score",
      align: "right",
      sortValue: (r) => r.risk_score,
      render: (r) => r.risk_score.toFixed(1),
    },
    {
      key: "model_decision",
      header: "Model Decision",
      sortValue: (r) => r.model_decision,
      render: (r) => <span className="text-xs uppercase tracking-wide text-muted-foreground">{r.model_decision}</span>,
    },
    {
      key: "investigation_status",
      header: "Investigation Status",
      sortValue: (r) => r.investigation_status,
      render: (r) => <StatusBadge status={r.investigation_status} />,
    },
    {
      key: "date_added",
      header: "Date Added",
      sortValue: (r) => r.date_added,
      render: (r) => <span className="text-xs text-muted-foreground">{new Date(r.date_added).toLocaleDateString()}</span>,
    },
    {
      key: "action",
      header: "Action",
      render: (r) => <span className="text-xs font-medium text-primary">Review</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Investigation Queue"
        subtitle="High-risk providers prioritized for human investigation. Model decisions remain separate from human review state."
      />
      <DataTable
        data={filtered}
        columns={columns}
        rowKey={(r) => r.provider_id}
        searchable={(r) => `${r.provider_id} ${r.model_decision} ${r.risk_level}`}
        searchPlaceholder="Search provider or model decision…"
        loading={loading}
        error={error}
        emptyTitle="No providers in this queue view"
        onRowClick={(row) => navigate({ to: "/providers/$providerId", params: { providerId: row.provider_id } })}
        toolbar={STATUSES.map((s) => (
          <Button key={s} size="sm" variant={status === s ? "default" : "outline"} onClick={() => setStatus(s)}>
            {s}
          </Button>
        ))}
      />
    </div>
  );
}
