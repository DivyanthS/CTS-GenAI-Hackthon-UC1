import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/common/DataTable";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { getProviders } from "@/services/mockApi";
import type { Provider } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function Providers() {
  const navigate = useNavigate();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProviders()
      .then(setProviders)
      .catch(() => setError("Unable to load providers."))
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
      key: "risk",
      header: "Risk",
      sortValue: (r) => r.risk_score,
      render: (r) => <RiskBadge level={r.risk_level} score={r.risk_score} />,
    },
    { key: "claims", header: "Claims", align: "right", sortValue: (r) => r.claim_count, render: (r) => r.claim_count.toLocaleString() },
    { key: "benes", header: "Beneficiaries", align: "right", sortValue: (r) => r.beneficiary_count, render: (r) => r.beneficiary_count.toLocaleString() },
    { key: "total", header: "Total Reimbursement", align: "right", sortValue: (r) => r.total_reimbursement, render: (r) => currency(r.total_reimbursement) },
    { key: "avg", header: "Avg / Claim", align: "right", sortValue: (r) => r.average_reimbursement, render: (r) => currency(r.average_reimbursement) },
    { key: "status", header: "Status", sortValue: (r) => r.status, render: (r) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Provider Risk Intelligence"
        subtitle="Provider-level risk scores, billing volume and reimbursement exposure."
      />
      <DataTable
        data={providers}
        columns={columns}
        rowKey={(r) => r.provider_id}
        searchable={(r) => r.provider_id}
        searchPlaceholder="Search provider ID…"
        loading={loading}
        error={error}
        emptyTitle="No providers found"
        onRowClick={(r) =>
          navigate({ to: "/providers/$providerId", params: { providerId: r.provider_id } })
        }
      />
    </div>
  );
}
