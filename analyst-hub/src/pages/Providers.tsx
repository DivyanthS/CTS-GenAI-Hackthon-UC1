import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/common/DataTable";
import { RiskBadge } from "@/components/common/RiskBadge";
import { getProviders } from "@/services/api";
import type { Provider } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function Providers() {
  const navigate = useNavigate();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProviders(1, 100)
      .then((response) => setProviders(response.providers ?? []))
      .catch(() => setError("Unable to load providers from the backend."))
      .finally(() => setLoading(false));
  }, []);

  const columns: Column<Provider>[] = [
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
      sortValue: (r) => Number(r.risk_probability ?? r.risk_score / 100),
      render: (r) => `${((Number(r.risk_probability ?? r.risk_score / 100) ?? 0) * 100).toFixed(1)}%`,
    },
    { key: "claims", header: "Total Claims", align: "right", sortValue: (r) => r.claim_count, render: (r) => r.claim_count.toLocaleString() },
    { key: "benes", header: "Beneficiaries", align: "right", sortValue: (r) => r.beneficiary_count, render: (r) => r.beneficiary_count.toLocaleString() },
    { key: "total", header: "Reimbursement", align: "right", sortValue: (r) => r.total_reimbursement, render: (r) => currency(r.total_reimbursement) },
    { key: "action", header: "Action", render: (r) => <span className="text-xs font-medium text-primary">Open</span> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Provider Risk Intelligence"
        subtitle="Provider-level risk scoring, reimbursement exposure, and investigation prioritization."
      />
      <DataTable
        data={providers}
        columns={columns}
        rowKey={(r) => r.provider_id}
        searchable={(r) => `${r.provider_id} ${r.risk_level}`}
        searchPlaceholder="Search by provider ID or risk level…"
        loading={loading}
        error={error}
        emptyTitle="No providers found"
        onRowClick={(r) => navigate({ to: "/providers/$providerId", params: { providerId: r.provider_id } })}
      />
    </div>
  );
}
