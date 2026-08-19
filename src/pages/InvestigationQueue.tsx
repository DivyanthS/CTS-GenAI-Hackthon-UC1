import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/common/DataTable";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { getInvestigations } from "@/services/mockApi";
import { ReportButton } from "@/components/reports/ReportButton";
import type { CaseStatus, Investigation } from "@/types";

const STATUSES: (CaseStatus | "All")[] = ["All", "New", "Under Review", "Escalated", "Resolved"];

export function InvestigationQueue() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<CaseStatus | "All">("All");

  useEffect(() => {
    getInvestigations()
      .then(setCases)
      .catch(() => setError("Unable to load the investigation queue."))
      .finally(() => setLoading(false));
  }, []);

  const rows = status === "All" ? cases : cases.filter((c) => c.status === status);

  const columns: Column<Investigation>[] = [
    { key: "case_id", header: "Case", sortValue: (r) => r.case_id, render: (r) => <span className="font-mono text-xs font-medium text-primary">{r.case_id}</span> },
    { key: "provider_id", header: "Provider", sortValue: (r) => r.provider_id, render: (r) => <span className="font-mono text-xs">{r.provider_id}</span> },
    { key: "priority", header: "Priority", sortValue: (r) => r.risk_score, render: (r) => <RiskBadge level={r.priority} score={r.risk_score} /> },
    { key: "status", header: "Status", sortValue: (r) => r.status, render: (r) => <StatusBadge status={r.status} /> },
    { key: "created_at", header: "Created", sortValue: (r) => r.created_at, render: (r) => <span className="text-xs text-muted-foreground">{r.created_at}</span> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Investigation Queue"
        subtitle="Triage flagged claims. Investigators make the final determination."
        actions={
          <ReportButton
            type="queue"
            label="Export Queue Report"
            build={() => ({
              type: "queue",
              data: { filters: { status, risk: "All", claim_type: "All" }, cases: rows },
            })}
          />
        }
      />
      <DataTable
        data={rows}
        columns={columns}
        rowKey={(r) => r.case_id}
        searchable={(r) => `${r.case_id} ${r.claim_id} ${r.provider_id} ${r.assigned_to}`}
        searchPlaceholder="Search case, claim or investigator…"
        loading={loading}
        error={error}
        emptyTitle="No cases in this view"
        onRowClick={(r) => navigate({ to: "/investigations/$caseId", params: { caseId: r.case_id } })}
        toolbar={STATUSES.map((s) => (
          <Button key={s} size="sm" variant={status === s ? "default" : "outline"} onClick={() => setStatus(s)}>
            {s}
          </Button>
        ))}
      />
    </div>
  );
}
