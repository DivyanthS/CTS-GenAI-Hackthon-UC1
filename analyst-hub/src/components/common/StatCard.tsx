import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sublabel,
  icon: Icon,
  tone = "neutral",
  className,
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  icon?: LucideIcon;
  tone?: "neutral" | "critical" | "success" | "info";
  className?: string;
}) {
  const tones = {
    neutral: "text-foreground",
    critical: "text-risk-critical",
    success: "text-success",
    info: "text-info",
  } as const;
  const iconTones = {
    neutral: "bg-secondary text-muted-foreground",
    critical: "bg-risk-critical-soft text-risk-critical",
    success: "bg-success-soft text-success",
    info: "bg-info-soft text-info",
  } as const;

  return (
    <div className={cn("panel flex items-start justify-between gap-4 p-5", className)}>
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className={cn("mt-2 truncate text-3xl font-semibold tabular", tones[tone])}>{value}</p>
        {sublabel && <p className="mt-1.5 text-xs text-muted-foreground">{sublabel}</p>}
      </div>
      {Icon && (
        <span className={cn("grid size-10 shrink-0 place-items-center rounded-lg", iconTones[tone])}>
          <Icon className="size-5" />
        </span>
      )}
    </div>
  );
}
