import { cn } from "@/lib/utils";
import type { CaseStatus } from "@/types";

const styles: Record<CaseStatus, string> = {
  New: "bg-info-soft text-info ring-info/25",
  "Under Review": "bg-secondary text-secondary-foreground ring-border",
  Escalated: "bg-risk-high-soft text-risk-high ring-risk-high/25",
  Resolved: "bg-success-soft text-success ring-success/25",
};

export function StatusBadge({ status, className }: { status: CaseStatus; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        styles[status],
        className,
      )}
    >
      {status}
    </span>
  );
}
