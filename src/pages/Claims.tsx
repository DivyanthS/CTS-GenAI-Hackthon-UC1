import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/common/DataTable";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { getClaims } from "@/services/mockApi";
import type { Claim, RiskLevel } from "@/types";

const LEVELS: (RiskLevel | "All")[] = ["All", "Critical", "High", "Medium", "Low"];
const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function Claims() {
  const navigate = useNavigate();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState<RiskLevel | "All">("All");

  useEffect(() => {
    setLoading(true);
    getClaims()
      .then(setClaims)
      .catch(() => setError("Unable to load claims."))
      .finally(() => setLoading(false));
  }, []);

  const rows = level === "All" ? claims : claims.filter((c) => c.risk_level === level);

  const columns: Column<Claim>[] = [
    {
      key: "claim_id",
      header: "Claim ID",
      sortValue: (r) => r.claim_id,
      render: (r) => <span className="font-mono text-xs font-medium text-primary">{r.claim_id}</span>,
    },
    {
      key: "provider_id",
      header: "Provider",
      sortValue: (r) => r.provider_id,
      render: (r) => <span className="font-mono text-xs">{r.provider_id}</span>,
    },
    { key: "claim_type", header: "Type", sortValue: (r) => r.claim_type, render: (r) => r.claim_type },
    {
      key: "reimbursement",
      header: "Reimbursement",
      align: "right",
      sortValue: (r) => r.reimbursement,
      render: (r) => currency(r.reimbursement),
    },
    {
      key: "risk",
      header: "Risk",
      sortValue: (r) => r.risk_score,
      render: (r) => <RiskBadge level={r.risk_level} score={r.risk_score} />,
    },
    {
      key: "status",
      header: "Status",
      sortValue: (r) => r.status,
      render: (r) => <StatusBadge status={r.status} />,
    },
    {
      key: "date",
      header: "Claim Start",
      sortValue: (r) => r.claim_start_date,
      render: (r) => <span className="text-xs text-muted-foreground">{r.claim_start_date}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Scored Claims" subtitle="Filter and sort claims by model risk level." />
      <DataTable
        data={rows}
        columns={columns}
        rowKey={(r) => r.claim_id}
        searchable={(r) => `${r.claim_id} ${r.provider_id} ${r.bene_id}`}
        searchPlaceholder="Search claim, provider or beneficiary…"
        loading={loading}
        error={error}
        emptyTitle="No claims match your filters"
        onRowClick={(r) => navigate({ to: "/claims/$claimId", params: { claimId: r.claim_id } })}
        toolbar={LEVELS.map((l) => (
          <Button
            key={l}
            size="sm"
            variant={level === l ? "default" : "outline"}
            onClick={() => setLevel(l)}
          >
            {l}
          </Button>
        ))}
      />
    </div>
  );
}
