import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
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
    <span className={cn("inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium", className)}>
      <Icon className="size-3.5" />
      {label}
    </span>
  );
}

export function DataQuality() {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem("dataset-validation");
      if (!saved) {
        setResult(null);
        setError("No validation result is available. Upload a dataset from the Import Data page first.");
        return;
      }

      const parsed = JSON.parse(saved);
      setResult(parsed);
      setError(null);
    } catch {
      setError("Unable to read the backend validation result.");
    }
  }, []);

  if (error) return <ErrorState description={error} onRetry={() => window.location.reload()} />;
  if (!result) return <LoadingState label="Waiting for validation result…" />;

  const checks = Array.isArray(result.checks) ? result.checks : [];
  const schema = Array.isArray(result.schema) ? result.schema : [];
  const health = Number(result.health_score ?? 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Quality"
        subtitle="Validation checks and schema conformance for the uploaded CSV."
        actions={
          <Button asChild>
            <Link to="/import">Back to Import Data</Link>
          </Button>
        }
      />

      <section className="panel flex flex-col gap-5 p-6 md:flex-row md:items-center">
        <div className="md:w-56">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Dataset health score</p>
          <p className="mt-2 text-4xl font-semibold text-success tabular">{health}%</p>
        </div>
        <div className="flex-1">
          <div className="h-3 w-full rounded-full bg-secondary" role="presentation">
            <div className="h-3 rounded-full bg-success" style={{ width: `${health}%` }} />
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            {result.valid ? "The uploaded dataset passed validation checks and is ready for import." : "Validation warnings or errors require review before import."}
          </p>
        </div>
      </section>

      <section className="panel overflow-hidden">
        <header className="border-b border-border p-5">
          <h2 className="text-sm font-semibold">Validation Checks</h2>
        </header>
        <ul className="divide-y divide-border">
          {checks.map((check: any, index: number) => (
            <li key={`${check.name}-${index}`} className="flex items-start justify-between gap-4 px-5 py-3.5">
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">{check.name}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{check.message ?? check.detail ?? "No message returned."}</p>
              </div>
              <StatusPill status={String(check.status || "warn").toLowerCase() === "pass" ? "pass" : String(check.status || "warn").toLowerCase() === "fail" ? "fail" : "warn"} />
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
              {schema.map((field: any, index: number) => (
                <tr key={`${field.field ?? "field"}-${index}`} className="border-b border-border/70 last:border-0">
                  <td className="px-5 py-3 font-mono text-xs">{field.field ?? "Unknown"}</td>
                  <td className="px-5 py-3 text-muted-foreground">{field.type ?? "Unknown"}</td>
                  <td className="px-5 py-3 text-muted-foreground">{field.required ? "Yes" : "No"}</td>
                  <td className="px-5 py-3"><StatusPill status={String(field.status || "warn").toLowerCase() === "pass" ? "pass" : String(field.status || "warn").toLowerCase() === "fail" ? "fail" : "warn"} /></td>
                  <td className="px-5 py-3 text-xs text-muted-foreground">{field.note ?? "No note returned."}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
