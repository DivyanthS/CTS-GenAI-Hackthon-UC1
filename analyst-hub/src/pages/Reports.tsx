import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { LoadingState, ErrorState } from "@/components/common/States";
import { API_BASE_URL, api, downloadPdf, getReportJson, getRuns } from "@/services/api";
import type { BackendRun } from "@/services/api";

const currency = (value: number | null | undefined) => {
  const numeric = Number(value ?? 0);
  return `$${numeric.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
};

export function Reports() {
  const [runs, setRuns] = useState<BackendRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [reportJson, setReportJson] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextRuns = await getRuns();
      setRuns(nextRuns);
      if (nextRuns.length > 0 && !selectedRunId) {
        setSelectedRunId(nextRuns[0].run_id);
      }
    } catch {
      setError("Unable to load analysis runs from the backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRuns();
  }, []);

  useEffect(() => {
    if (!selectedRunId) {
      setReportJson(null);
      return;
    }

    const loadReport = async () => {
      setReportLoading(true);
      try {
        const data = await getReportJson(selectedRunId);
        setReportJson(data);
      } catch {
        setError("Unable to load the selected report JSON from the backend.");
      } finally {
        setReportLoading(false);
      }
    };

    void loadReport();
  }, [selectedRunId]);

  const selectedRun = useMemo(
    () => runs.find((run) => run.run_id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  const handleViewPdf = () => {
    if (!selectedRunId) return;
    window.open(`${API_BASE_URL}/reports/${encodeURIComponent(selectedRunId)}/pdf`, "_blank", "noopener,noreferrer");
  };

  const handleDownloadPdf = async () => {
    if (!selectedRunId) return;
    try {
      const blob = await downloadPdf(selectedRunId);
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = `Fraud_Report_${selectedRunId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(href);
    } catch {
      setError("Unable to download the backend-generated PDF report.");
    }
  };

  if (loading) return <LoadingState label="Loading analysis runs…" />;
  if (error) return <ErrorState description={error} onRetry={loadRuns} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Review analysis runs, inspect structured JSON, and open the backend-generated PDF report."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleViewPdf} disabled={!selectedRunId}>
              View PDF
            </Button>
            <Button size="sm" onClick={handleDownloadPdf} disabled={!selectedRunId}>
              Download PDF
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        <section className="panel overflow-hidden">
          <header className="border-b border-border p-4">
            <h2 className="text-sm font-semibold">Analysis Runs</h2>
          </header>
          <div className="max-h-[720px] overflow-y-auto">
            {runs.length === 0 ? (
              <div className="p-4 text-sm text-muted-foreground">No analysis runs found.</div>
            ) : (
              <ul className="divide-y divide-border">
                {runs.map((run) => (
                  <li key={run.run_id}>
                    <button
                      type="button"
                      className={[
                        "w-full px-4 py-3 text-left transition-colors hover:bg-secondary/50",
                        selectedRunId === run.run_id ? "bg-secondary/80" : "",
                      ].join(" ")}
                      onClick={() => setSelectedRunId(run.run_id)}
                    >
                      <p className="font-mono text-xs font-medium text-primary">{run.run_id}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{run.filename ?? "Untitled run"}</p>
                      <div className="mt-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
                        <span>{run.status ?? "unknown"}</span>
                        <span>{currency(run.total_reimbursement)}</span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="panel overflow-hidden">
          <header className="border-b border-border p-4">
            <h2 className="text-sm font-semibold">Run Detail</h2>
          </header>

          {selectedRun ? (
            <div className="space-y-4 p-4">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Run ID</div>
                  <div className="mt-2 font-mono text-xs text-foreground">{selectedRun.run_id}</div>
                </div>
                <div className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Status</div>
                  <div className="mt-2 text-sm font-medium">{selectedRun.status ?? "unknown"}</div>
                </div>
                <div className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Providers</div>
                  <div className="mt-2 text-sm font-medium">{selectedRun.total_providers ?? 0}</div>
                </div>
                <div className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Claims</div>
                  <div className="mt-2 text-sm font-medium">{selectedRun.total_claims ?? 0}</div>
                </div>
              </div>

              <div className="rounded-md border border-border bg-secondary/30 p-3 text-xs text-muted-foreground">
                <div className="flex flex-wrap gap-4">
                  <span>Rows: {selectedRun.total_rows ?? 0}</span>
                  <span>Columns: {selectedRun.total_columns ?? 0}</span>
                  <span>Beneficiaries: {selectedRun.total_beneficiaries ?? 0}</span>
                  <span>Reimbursement: {currency(selectedRun.total_reimbursement)}</span>
                </div>
              </div>

              <div className="rounded-md border border-border bg-black/5 p-3">
                <div className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">Structured JSON</div>
                {reportLoading ? (
                  <LoadingState label="Loading report JSON…" />
                ) : reportJson ? (
                  <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap break-words text-[11px] leading-6 text-foreground">
                    {JSON.stringify(reportJson, null, 2)}
                  </pre>
                ) : (
                  <div className="text-sm text-muted-foreground">No report available for this run.</div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4 text-sm text-muted-foreground">Select a run to view its report data.</div>
          )}
        </section>
      </div>
    </div>
  );
}
