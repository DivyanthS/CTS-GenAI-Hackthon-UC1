import { Link } from "@tanstack/react-router";
import { Bell, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { UserMenu } from "@/components/layout/UserMenu";

export function TopBar({
  title,
  breadcrumb,
}: {
  title: string;
  breadcrumb: { label: string; to?: string }[];
}) {
  return (
    <header className="sticky top-0 z-20 flex flex-col gap-3 border-b border-border bg-card/90 px-6 py-3 backdrop-blur md:flex-row md:items-center md:justify-between">
      <div className="min-w-0">
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-muted-foreground">
          {breadcrumb.map((crumb, i) => (
            <span key={crumb.label} className="flex items-center gap-1.5">
              {i > 0 && <span aria-hidden>/</span>}
              {crumb.to ? (
                <Link to={crumb.to} className="transition-colors hover:text-foreground">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-foreground">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
        <h2 className="truncate text-base font-semibold text-foreground">{title}</h2>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative hidden w-64 md:block">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input aria-label="Search claims and providers" placeholder="Search claims, providers…" className="pl-9" />
        </div>
        <button
          type="button"
          aria-label="Notifications"
          className="relative grid size-9 place-items-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
        >
          <Bell className="size-4" />
          <span className="absolute right-2 top-2 size-1.5 rounded-full bg-risk-critical" />
        </button>
        <UserMenu />
      </div>
    </header>
  );
}
