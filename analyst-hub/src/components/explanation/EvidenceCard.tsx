import { TrendingDown, TrendingUp } from "lucide-react";
import type { Evidence } from "@/types";
import { cn } from "@/lib/utils";

export function formatValue(value: number, unit: Evidence["unit"]) {
  if (unit === "currency")
    return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  if (unit === "percent") return `${value}%`;
  return value.toLocaleString("en-US");
}

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const up = !evidence.difference.startsWith("-");
  const ratio = Math.min(
    100,
    (evidence.provider_value / Math.max(evidence.provider_value, evidence.peer_value)) * 100,
  );
  const peerRatio = Math.min(
    100,
    (evidence.peer_value / Math.max(evidence.provider_value, evidence.peer_value)) * 100,
  );

  return (
    <div className="panel p-5">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-sm font-semibold text-foreground">{evidence.factor}</h4>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold tabular",
            up ? "bg-risk-critical-soft text-risk-critical" : "bg-success-soft text-success",
          )}
        >
          {up ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
          {evidence.difference}
        </span>
      </div>

      <dl className="mt-4 space-y-3">
        <div>
          <div className="flex items-baseline justify-between text-xs">
            <dt className="text-muted-foreground">Provider</dt>
            <dd className="font-semibold text-foreground tabular">
              {formatValue(evidence.provider_value, evidence.unit)}
            </dd>
          </div>
          <div className="mt-1 h-2 rounded-full bg-secondary">
            <div
              className="h-2 rounded-full bg-risk-critical"
              style={{ width: `${ratio}%` }}
              aria-hidden
            />
          </div>
        </div>
        <div>
          <div className="flex items-baseline justify-between text-xs">
            <dt className="text-muted-foreground">Peer average</dt>
            <dd className="font-semibold text-foreground tabular">
              {formatValue(evidence.peer_value, evidence.unit)}
            </dd>
          </div>
          <div className="mt-1 h-2 rounded-full bg-secondary">
            <div
              className="h-2 rounded-full bg-info"
              style={{ width: `${peerRatio}%` }}
              aria-hidden
            />
          </div>
        </div>
      </dl>

      {evidence.note && (
        <p className="mt-4 border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
          {evidence.note}
        </p>
      )}
    </div>
  );
}
