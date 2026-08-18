import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Brain, CheckCircle2, Loader2, Play } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { analyzeCsv } from "@/services/api";
import { cn } from "@/lib/utils";

export function FraudAnalysis() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    const fileName = sessionStorage.getItem("last-uploaded-file");
    if (!fileName) {
      setError("Upload a CSV from the Import Data page before running backend analysis.");
      return;
    }

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    const file = fileInput?.files?.[0];
    if (!file) {
      setError("No CSV file is currently available for backend analysis.");
      return;
    }

    setRunning(true);
    setError(null);
    try {
      const nextResult = await analyzeCsv(file);
      setResult(nextResult);
      sessionStorage.setItem("analysis-result", JSON.stringify(nextResult));
    } catch (e: any) {
      const message = e?.response?.data?.message ?? e?.message ?? "Backend analysis failed.";
      setError(message);
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    const saved = sessionStorage.getItem("analysis-result");
    if (!saved) return;
    try {
      setResult(JSON.parse(saved));
    } catch {
      setResult(null);
    }
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fraud Risk Analysis"
        subtitle="Run the backend CSV analysis flow and inspect the returned provider risk summary."
        actions={
          <Button onClick={() => void start()} disabled={running}>
            {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            {running ? "Analyzing…" : result ? "Re-run Analysis" : "Run Analysis"}
          </Button>
        }
      />

      {error && (
        <div className="rounded-md border border-risk-critical/30 bg-risk-critical-soft px-4 py-3 text-sm text-risk-critical">{error}</div>
      )}

      {!result && !error && (
        <div className="panel p-6 text-sm text-muted-foreground">
          Upload a CSV from the Import Data page to run the backend analysis flow.
        </div>
      )}

      {result && (
        <section className="panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Analysis complete</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {typeof result.run_id !== "undefined" ? `Run ${result.run_id}` : "Backend analysis completed"}
              </p>
            </div>
            <Button asChild variant="outline">
              <Link to="/providers">View Providers</Link>
            </Button>
          </div>

          <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Providers", result.providers_analyzed ?? result.total_providers ?? 0, "text-info bg-info-soft"],
              ["High Risk", result.high_risk ?? result.high ?? 0, "text-risk-high bg-risk-high-soft"],
              ["Medium Risk", result.medium_risk ?? result.medium ?? 0, "text-risk-medium bg-risk-medium-soft"],
              ["Low Risk", result.low_risk ?? result.low ?? 0, "text-risk-low bg-risk-low-soft"],
            ].map(([label, value, tone]) => (
              <div key={String(label)} className={cn("rounded-md p-4", tone)}>
                <dt className="text-xs font-medium uppercase tracking-wider">{String(label)}</dt>
                <dd className="mt-1 text-2xl font-semibold tabular">{Number(value).toLocaleString()}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-4 text-xs text-muted-foreground">
            {result.message ? <span>{result.message}</span> : <span>Backend analysis result was returned successfully.</span>}
          </div>
        </section>
      )}

      <section className="panel p-6">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-info-soft text-info">
            <Brain className="size-5" />
          </span>
          <div>
            <h2 className="text-sm font-semibold">Model pipeline</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              The frontend uses the backend dataset analysis endpoint and displays the returned provider risk summary.
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 text-sm text-foreground">
          <CheckCircle2 className="size-4 text-success" />
          <span>Backend result consumption only</span>
        </div>
      </section>
    </div>
  );
}
