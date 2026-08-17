import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { validateDataset } from "@/services/mockApi";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectDataQualityReportData } from "@/services/reportService";
import type { SchemaField, ValidationCheck } from "@/types";
import { cn } from "@/lib/utils";

type Status = "pass" | "warn" | "fail";

const statusMeta: Record<Status, { icon: typeof CheckCircle2; className: string; label: string }> = {
  pass: { icon: CheckCircle2, className: "text-success bg-success-soft", label: "Pass" },
  warn: { icon: AlertTriangle, className: "text-risk-high bg-risk-high-soft", label: "Warning" },
  fail: { icon: XCircle, className: "text-risk-critical bg-risk-critical-soft", label: "Fail" },
};

function StatusPill({ status }: { status: Status }) {
  const { icon: Icon, className, label } = statusMeta[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium",
        className,
      )}
    >
      <Icon className="size-3.5" />
      {label}
    </span>
  );
}

export function DataQuality() {
  const [result, setResult] = useState<{
    checks: ValidationCheck[];
    schema: SchemaField[];
    health: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setResult(null);
    validateDataset().then(setResult).catch(() => setError("Validation failed to run."));
  };

  useEffect(load, []);

  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!result) return <LoadingState label="Running validation checks…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Quality"
        subtitle="Validation checks and schema conformance for the imported dataset."
        actions={
          <>
            <ReportButton
              type="data-quality"
              label="Download Quality Report"
              mode="download"
              build={async () => ({ type: "data-quality", data: await collectDataQualityReportData() })}
            />
            <Button asChild>
              <Link to="/fraud-analysis">Continue to Analysis</Link>
            </Button>
          </>
        }
      />

      <section className="panel flex flex-col gap-5 p-6 md:flex-row md:items-center">
        <div className="md:w-56">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Dataset health score
          </p>
          <p className="mt-2 text-4xl font-semibold text-success tabular">{result.health}%</p>
        </div>
        <div className="flex-1">
          <div className="h-3 w-full rounded-full bg-secondary" role="presentation">
            <div className="h-3 rounded-full bg-success" style={{ width: `${result.health}%` }} />
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Dataset is usable for scoring. Warnings do not block analysis but may reduce confidence
            for affected records.
          </p>
        </div>
      </section>

      <section className="panel overflow-hidden">
        <header className="border-b border-border p-5">
          <h2 className="text-sm font-semibold">Validation Checks</h2>
        </header>
        <ul className="divide-y divide-border">
          {result.checks.map((check) => (
            <li key={check.name} className="flex items-start justify-between gap-4 px-5 py-3.5">
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">{check.name}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{check.detail}</p>
              </div>
              <StatusPill status={check.status} />
            </li>
          ))}
        </ul>
      </section>

      <section className="panel overflow-hidden">
        <header className="border-b border-border p-5">
          <h2 className="text-sm font-semibold">Schema Conformance</h2>
        </header>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/60 text-xs uppercase tracking-wider text-muted-foreground">
                <th scope="col" className="px-5 py-2.5 text-left font-semibold">Field</th>
                <th scope="col" className="px-5 py-2.5 text-left font-semibold">Type</th>
                <th scope="col" className="px-5 py-2.5 text-left font-semibold">Required</th>
                <th scope="col" className="px-5 py-2.5 text-left font-semibold">Status</th>
                <th scope="col" className="px-5 py-2.5 text-left font-semibold">Note</th>
              </tr>
            </thead>
            <tbody>
              {result.schema.map((f) => (
                <tr key={f.field} className="border-b border-border/70 last:border-0">
                  <td className="px-5 py-3 font-mono text-xs">{f.field}</td>
                  <td className="px-5 py-3 text-muted-foreground">{f.type}</td>
                  <td className="px-5 py-3 text-muted-foreground">{f.required ? "Yes" : "No"}</td>
                  <td className="px-5 py-3"><StatusPill status={f.status} /></td>
                  <td className="px-5 py-3 text-xs text-muted-foreground">{f.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
