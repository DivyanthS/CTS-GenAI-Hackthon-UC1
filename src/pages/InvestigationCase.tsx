import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ExplanationCard } from "@/components/explanation/ExplanationCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getInvestigation, getRiskResult } from "@/services/mockApi";
import { ReportButton } from "@/components/reports/ReportButton";
import { collectInvestigationReportData } from "@/services/reportService";
import type { CaseStatus, Investigation, RiskResult } from "@/types";

const ACTIONS: CaseStatus[] = ["Under Review", "Escalated", "Resolved"];

export function InvestigationCase() {
  const { caseId } = useParams({ from: "/_shell/investigations/$caseId" });
  const [item, setItem] = useState<Investigation | null>(null);
  const [risk, setRisk] = useState<RiskResult | null>(null);
  const [status, setStatus] = useState<CaseStatus | null>(null);
  const [note, setNote] = useState("");
  const [notes, setNotes] = useState<{ text: string; at: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    getInvestigation(caseId)
      .then(async (c) => {
        setItem(c ?? null);
        setStatus(c?.status ?? null);
        if (c) setRisk((await getRiskResult(c.claim_id)) ?? null);
      })
      .catch(() => setError("Unable to load this case."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [caseId]);

  if (loading) return <LoadingState label="Loading case…" />;
  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!item) return <EmptyState title="Case not found" description={`No case with ID ${caseId}.`} />;

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/investigations">
          <ArrowLeft className="size-4" /> Back to queue
        </Link>
      </Button>

      <PageHeader
        title={`Case ${item.case_id}`}
        subtitle={`Provider ${item.provider_id}`}
        actions={
          <div className="flex items-center gap-2">
            <RiskBadge level={item.priority} score={item.risk_score} />
            {status && <StatusBadge status={status} />}
            <ReportButton
              type="investigation"
              label="Download Investigation Report"
              mode="download"
              build={async () => {
                const data = await collectInvestigationReportData(item.case_id, {
                  notes,
                  ...(status ? { status } : {}),
                });
                return data ? { type: "investigation", data } : null;
              }}
            />
          </div>
        }
      />

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Investigator decision</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          The model surfaces risk signals; the outcome of this case is decided by you.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {ACTIONS.map((a) => (
            <Button key={a} size="sm" variant={status === a ? "default" : "outline"} onClick={() => setStatus(a)}>
              Mark {a}
            </Button>
          ))}
        </div>
        <div className="mt-5">
          <label htmlFor="case-note" className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Case note
          </label>
          <Textarea
            id="case-note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Document findings, contacts and next steps…"
            className="mt-2"
            rows={4}
          />
          <Button
            className="mt-3"
            size="sm"
            disabled={!note.trim()}
            onClick={() => {
              setNotes((prev) => [{ text: note.trim(), at: new Date().toLocaleString() }, ...prev]);
              setNote("");
            }}
          >
            Add note
          </Button>
        </div>
      </section>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Case timeline</h2>
        <ol className="mt-4 space-y-4 border-l border-border pl-5">
          {notes.map((n) => (
            <li key={`${n.at}-${n.text}`} className="relative">
              <span className="absolute -left-[26px] top-1.5 size-2.5 rounded-full bg-info" aria-hidden />
              <p className="text-sm text-foreground">{n.text}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{n.at}</p>
            </li>
          ))}
          <li className="relative">
            <span className="absolute -left-[26px] top-1.5 size-2.5 rounded-full bg-muted-foreground" aria-hidden />
            <p className="text-sm text-foreground">Case created from model scoring run</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{item.created_at}</p>
          </li>
        </ol>
      </section>

      {risk && <ExplanationCard explanation={risk.explanation} evidence={risk.evidence} />}
    </div>
  );
}
