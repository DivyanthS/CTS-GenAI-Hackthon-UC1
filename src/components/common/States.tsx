import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LoadingState({ label = "Loading data…", className }: { label?: string; className?: string }) {
  return (
    <div
      role="status"
      className={cn("panel flex flex-col items-center justify-center gap-3 p-12 text-center", className)}
    >
      <Loader2 className="size-6 animate-spin text-primary" />
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

export function EmptyState({
  title = "No records found",
  description = "Adjust your filters or search to see more results.",
  icon: Icon = Inbox,
  action,
  className,
}: {
  title?: string;
  description?: string;
  icon?: LucideIcon;
  action?: { label: string; onClick: () => void };
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 p-12 text-center", className)}>
      <span className="grid size-11 place-items-center rounded-full bg-secondary text-muted-foreground">
        <Icon className="size-5" />
      </span>
      <p className="mt-1 text-sm font-semibold text-foreground">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      {action && (
        <Button variant="outline" size="sm" className="mt-3" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description = "The request could not be completed. Try again.",
  onRetry,
  className,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "panel flex flex-col items-center justify-center gap-2 border-risk-critical/25 p-12 text-center",
        className,
      )}
    >
      <span className="grid size-11 place-items-center rounded-full bg-risk-critical-soft text-risk-critical">
        <AlertTriangle className="size-5" />
      </span>
      <p className="mt-1 text-sm font-semibold text-foreground">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}
