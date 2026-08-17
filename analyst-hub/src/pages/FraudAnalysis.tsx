import { useEffect, useRef, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Brain, CheckCircle2, Loader2, Play } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { runAnalysis } from "@/services/mockApi";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectDashboardReportData } from "@/services/reportService";
import { cn } from "@/lib/utils";

const STEPS = [
  "Loading dataset into scoring engine",
  "Engineering provider-level features",
  "Running ensemble risk model",
  "Comparing providers to peer cohorts",
  "Generating evidence-grounded explanations",
];

type Result = Awaited<ReturnType<typeof runAnalysis>>;

export function FraudAnalysis() {
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(-1);
  const [result, setResult] = useState<Result | null>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const start = () => {
    setRunning(true);
    setResult(null);
    setStep(0);
    STEPS.forEach((_, i) => {
      timers.current.push(setTimeout(() => setStep(i + 1), (i + 1) * 900));
    });
    timers.current.push(
      setTimeout(() => {
        runAnalysis()
          .then(setResult)
          .finally(() => setRunning(false));
      }, STEPS.length * 900),
    );
  };

  const progress = step < 0 ? 0 : Math.round((step / STEPS.length) * 100);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fraud Risk Analysis"
        subtitle="Score the dataset with the ML pipeline and generate explanations for flagged claims."
        actions={
          <>
            <ReportButton
              type="analysis-summary"
              label="Download Analysis Report"
              mode="download"
              build={async () => ({ type: "analysis-summary", data: await collectDashboardReportData() })}
            />
          <Button onClick={start} disabled={running}>
            {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            {running ? "Analyzing…" : result ? "Re-run Analysis" : "Run Analysis"}
          </Button>
          </>
        }
      />

      <section className="panel p-6">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-info-soft text-info">
            <Brain className="size-5" />
          </span>
          <div>
            <h2 className="text-sm font-semibold">Model pipeline</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Scores are statistical indicators of anomalous billing patterns. A human investigator
              makes the final determination.
            </p>
          </div>
        </div>

        <div className="mt-6">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span className="tabular">{progress}%</span>
          </div>
          <div className="mt-2 h-2.5 w-full rounded-full bg-secondary">
            <div
              className="h-2.5 rounded-full bg-info transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <ol className="mt-6 space-y-3">
          {STEPS.map((label, i) => {
            const done = step > i;
            const active = step === i && running;
            return (
              <li key={label} className="flex items-center gap-3 text-sm">
                <span
                  className={cn(
                    "grid size-6 shrink-0 place-items-center rounded-full text-xs",
                    done
                      ? "bg-success-soft text-success"
                      : active
                        ? "bg-info-soft text-info"
                        : "bg-secondary text-muted-foreground",
                  )}
                >
                  {done ? (
                    <CheckCircle2 className="size-4" />
                  ) : active ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </span>
                <span className={done || active ? "text-foreground" : "text-muted-foreground"}>
                  {label}
                </span>
              </li>
            );
          })}
        </ol>

        {step < 0 && (
          <p className="mt-6 rounded-md border border-dashed border-border px-4 py-3 text-xs text-muted-foreground">
            No analysis run yet. Start a run to score claims and populate the investigation queue.
          </p>
        )}
      </section>

      {result && (
        <section className="panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Analysis complete</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Run {result.run_id} · {result.scored_claims.toLocaleString()} claims scored
              </p>
            </div>
            <Button asChild variant="outline">
              <Link to="/claims">Review scored claims</Link>
            </Button>
          </div>

          <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Critical", result.critical, "text-risk-critical bg-risk-critical-soft"],
              ["High", result.high, "text-risk-high bg-risk-high-soft"],
              ["Medium", result.medium, "text-risk-medium bg-risk-medium-soft"],
              ["Low", result.low, "text-risk-low bg-risk-low-soft"],
            ].map(([label, value, tone]) => (
              <div key={label as string} className={cn("rounded-md p-4", tone as string)}>
                <dt className="text-xs font-medium uppercase tracking-wider">{label as string}</dt>
                <dd className="mt-1 text-2xl font-semibold tabular">
                  {(value as number).toLocaleString()}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}
    </div>
  );
}
