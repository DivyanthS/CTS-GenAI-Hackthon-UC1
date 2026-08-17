import { Link, useRouterState } from "@tanstack/react-router";
import {
  BarChart3,
  FileSearch,
  FolderSearch,
  Gauge,
  LayoutDashboard,
  ScanSearch,
  Settings,
  Shield,
  Upload,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const groups = [
  {
    label: "Overview",
    items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Data",
    items: [
      { to: "/import", label: "Import Data", icon: Upload },
      { to: "/data-quality", label: "Data Quality", icon: Gauge },
    ],
  },
  {
    label: "Risk Intelligence",
    items: [
      { to: "/fraud-analysis", label: "Fraud Analysis", icon: ScanSearch },
      { to: "/claims", label: "Claims", icon: FileSearch },
      { to: "/providers", label: "Providers", icon: Users },
    ],
  },
  {
    label: "Investigation",
    items: [{ to: "/investigations", label: "Investigation Queue", icon: FolderSearch }],
  },
  {
    label: "Analytics",
    items: [{ to: "/analytics", label: "Analytics", icon: BarChart3 }],
  },
  {
    label: "System",
    items: [{ to: "/settings", label: "Settings", icon: Settings }],
  },
] as const;

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground lg:flex">
      <div className="flex items-center gap-3 border-b border-sidebar-border px-5 py-5">
        <span className="grid size-9 place-items-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
          <Shield className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-sidebar-accent-foreground">
            FraudGuard AI
          </p>
          <p className="truncate text-[11px] text-sidebar-foreground/60">
            Claims Payment Integrity
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {groups.map((group) => (
          <div key={group.label}>
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-sidebar-foreground/45">
              {group.label}
            </p>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = pathname.startsWith(item.to);
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      className={cn(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                        active
                          ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                      )}
                    >
                      <item.icon className="size-4 shrink-0" />
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-full bg-sidebar-accent text-xs font-semibold text-sidebar-accent-foreground">
            AW
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-sidebar-accent-foreground">
              A. Whitfield
            </p>
            <p className="truncate text-[11px] text-sidebar-foreground/60">Analyst</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
