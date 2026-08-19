import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EvidenceCard } from "@/components/explanation/EvidenceCard";
import { ExplanationCard } from "@/components/explanation/ExplanationCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { getClaim, getRiskResult } from "@/services/mockApi";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectClaimReportData } from "@/services/reportService";
import type { Claim, RiskResult } from "@/types";

const currency = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export function ClaimDetails() {
  const { claimId } = useParams({ from: "/_shell/claims/$claimId" });
  const [claim, setClaim] = useState<Claim | null>(null);
  const [risk, setRisk] = useState<RiskResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([getClaim(claimId), getRiskResult(claimId)])
      .then(([c, r]) => {
        setClaim(c ?? null);
        setRisk(r ?? null);
      })
      .catch(() => setError("Unable to load claim details."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [claimId]);

  if (loading) return <LoadingState label="Loading claim details…" />;
  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!claim || !risk)
    return (
      <EmptyState
        title="Claim not found"
        description={`No scored claim exists with ID ${claimId}.`}
      />
    );

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/claims">
          <ArrowLeft className="size-4" /> Back to claims
        </Link>
      </Button>

      <PageHeader
        title={`Claim ${claim.claim_id}`}
        subtitle={`Provider ${claim.provider_id} · Beneficiary ${claim.bene_id}`}
        actions={
          <div className="flex items-center gap-2">
            <RiskBadge level={risk.risk_level} score={risk.risk_score} />
            <StatusBadge status={claim.status} />
            <ReportButton
              type="claim"
              label="Download Claim Report"
              mode="download"
              build={async () => {
                const data = await collectClaimReportData(claim.claim_id);
                return data ? { type: "claim", data } : null;
              }}
            />
          </div>
        }
      />

      <section className="panel p-6">
        <dl className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Claim type", claim.claim_type],
            ["Reimbursement", currency(claim.reimbursement)],
            ["Service period", `${claim.claim_start_date} → ${claim.claim_end_date}`],
            ["Model prediction", risk.prediction],
            ["Attending physician", claim.attending_physician ?? "—"],
            ["Operating physician", claim.operating_physician ?? "—"],
            ["Diagnosis codes", (claim.diagnosis_codes ?? []).join(", ") || "—"],
            ["Procedure codes", (claim.procedure_codes ?? []).join(", ") || "—"],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">{label}</dt>
              <dd className="mt-1 text-sm font-medium text-foreground">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <div>
        <h2 className="text-sm font-semibold text-foreground">Model evidence</h2>
        <div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {risk.evidence.map((e) => (
            <EvidenceCard key={e.factor} evidence={e} />
          ))}
        </div>
      </div>

      <ExplanationCard explanation={risk.explanation} evidence={risk.evidence} />
    </div>
  );
}
