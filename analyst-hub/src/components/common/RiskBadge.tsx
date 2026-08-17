import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types";

const styles: Record<RiskLevel, string> = {
  Critical: "bg-risk-critical-soft text-risk-critical ring-risk-critical/25",
  High: "bg-risk-high-soft text-risk-high ring-risk-high/25",
  Medium: "bg-risk-medium-soft text-risk-medium ring-risk-medium/30",
  Low: "bg-risk-low-soft text-risk-low ring-risk-low/25",
};

export function RiskBadge({
  level,
  score,
  className,
}: {
  level: RiskLevel;
  score?: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ring-inset",
        styles[level],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" aria-hidden />
      {level}
      {score !== undefined && <span className="tabular font-mono">{score}%</span>}
    </span>
  );
}

export function riskColor(level: RiskLevel) {
  return {
    Critical: "var(--risk-critical)",
    High: "var(--risk-high)",
    Medium: "var(--risk-medium)",
    Low: "var(--risk-low)",
  }[level];
}
