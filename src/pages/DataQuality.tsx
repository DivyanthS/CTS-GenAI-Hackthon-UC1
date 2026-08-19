
import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { CheckCircle2, FileCheck2, PlayCircle } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { validateDataset } from "@/services/mockApi";

export function DataQuality() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setReady(false);

    validateDataset()
      .then(() => setReady(true))
      .catch(() => setError("Unable to check the imported dataset."));
  };

  useEffect(() => {
    load();
  }, []);

  if (error) {
    return <ErrorState description={error} onRetry={load} />;
  }

  if (!ready) {
    return <LoadingState label="Checking analysis readiness…" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analysis Check"
        subtitle="Verify that the imported dataset is ready for fraud analysis."
      />

      {/* Analysis Readiness */}
      <section className="panel p-6">
        <div className="flex items-start gap-4">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-success-soft">
            <CheckCircle2 className="size-6 text-success" />
          </div>

          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Dataset Ready
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              The imported dataset is ready to proceed with fraud analysis.
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-center gap-3 rounded-lg border border-border p-4">
            <CheckCircle2 className="size-5 text-success" />

            <span className="text-sm font-medium">
              Dataset imported successfully
            </span>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border p-4">
            <CheckCircle2 className="size-5 text-success" />

            <span className="text-sm font-medium">
              Required provider information available
            </span>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border p-4">
            <CheckCircle2 className="size-5 text-success" />

            <span className="text-sm font-medium">
              Claim data available
            </span>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border p-4">
            <CheckCircle2 className="size-5 text-success" />

            <span className="text-sm font-medium">
              Dataset is suitable for fraud analysis
            </span>
          </div>
        </div>
      </section>

      {/* Ready to Start */}
      <section className="panel p-6">
        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-info/10">
              <FileCheck2 className="size-6 text-info" />
            </div>

            <div>
              <h2 className="text-sm font-semibold text-foreground">
                Ready to Start
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                Your dataset has passed the required checks. You can now run
                the fraud detection analysis.
              </p>
            </div>
          </div>

          <Button asChild className="shrink-0">
            <Link to="/fraud-analysis">
              <PlayCircle className="size-4" />
              Run Fraud Analysis
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
