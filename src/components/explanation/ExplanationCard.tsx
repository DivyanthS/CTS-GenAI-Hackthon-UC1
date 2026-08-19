import { Info, ShieldQuestion, Sparkles } from "lucide-react";
import type { Evidence, Explanation } from "@/types";
import { formatValue } from "./EvidenceCard";

export function ExplanationCard({
  explanation,
  evidence,
}: {
  explanation: Explanation;
  evidence: Evidence[];
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-border bg-card shadow-[var(--shadow-panel)]">
      <header className="flex items-start gap-3 border-b border-border bg-[oklch(0.235_0.031_262)] p-5 text-[oklch(0.93_0.01_250)]">
        <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-white/10">
          <Sparkles className="size-5" />
        </span>
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            Why  flagged?
          </h3>
          <p className="mt-1 text-xs opacity-80">
            AI-generated explanation based on model-derived evidence.
          </p>
        </div>
      </header>

      <div className="space-y-6 p-5">
        <p className="text-sm leading-relaxed text-foreground">{explanation.summary}</p>

        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Key factors
          </h4>
          <ol className="mt-3 space-y-3">
            {evidence.map((item, i) => (
              <li key={item.factor} className="rounded-md border border-border bg-secondary/40 p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-semibold text-foreground">
                    <span className="mr-2 font-mono text-xs text-muted-foreground">{i + 1}.</span>
                    {item.factor}
                  </p>
                  <span className="rounded bg-card px-2 py-0.5 text-xs font-semibold text-risk-critical tabular ring-1 ring-inset ring-risk-critical/20">
                    {item.difference}
                  </span>
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-3 text-xs sm:grid-cols-3">
                  <div>
                    <dt className="text-muted-foreground">Provider value</dt>
                    <dd className="font-semibold text-foreground tabular">
                      {formatValue(item.provider_value, item.unit)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Peer value</dt>
                    <dd className="font-semibold text-foreground tabular">
                      {formatValue(item.peer_value, item.unit)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Difference</dt>
                    <dd className="font-semibold text-foreground tabular">{item.difference}</dd>
                  </div>
                </dl>
                {item.note && (
                  <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{item.note}</p>
                )}
              </li>
            ))}
          </ol>
        </div>

        <div className="flex items-center gap-2 rounded-md bg-info-soft px-3 py-2 text-xs text-info">
          <Info className="size-4 shrink-0" />
          Explanation generated from model-derived evidence
          {explanation.model ? ` · ${explanation.model}` : ""}
        </div>

        <div className="flex items-start gap-2 rounded-md border border-dashed border-border p-3 text-xs leading-relaxed text-muted-foreground">
          <ShieldQuestion className="mt-0.5 size-4 shrink-0" />
          {explanation.disclaimer}
        </div>
      </div>
    </section>
  );
}
