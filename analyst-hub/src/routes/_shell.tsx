import { Outlet, createFileRoute, useRouterState } from "@tanstack/react-router";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { TopBar } from "@/components/layout/TopBar";
import { Toaster } from "@/components/ui/sonner";

export const Route = createFileRoute("/_shell")({
  component: ShellLayout,
});

const titles: Record<string, { title: string; crumbs: { label: string; to?: string }[] }> = {
  "/dashboard": { title: "Dashboard", crumbs: [{ label: "Overview" }, { label: "Dashboard" }] },
  "/providers": {
    title: "Provider Risk Intelligence",
    crumbs: [{ label: "Operations" }, { label: "Providers" }],
  },
  "/investigations": {
    title: "Investigation Queue",
    crumbs: [{ label: "Review" }, { label: "Investigation Queue" }],
  },
  "/analytics": { title: "Analytics", crumbs: [{ label: "Insights" }, { label: "Analytics" }] },
  "/reports": { title: "Reports", crumbs: [{ label: "Insights" }, { label: "Reports" }] },
  "/settings": { title: "Settings", crumbs: [{ label: "System" }, { label: "Settings" }] },
};

function resolve(pathname: string) {
  if (pathname.startsWith("/providers/"))
    return {
      title: "Provider Profile",
      crumbs: [{ label: "Providers", to: "/providers" }, { label: "Provider Profile" }],
    };
  if (pathname.startsWith("/investigations/"))
    return {
      title: "Investigation Case",
      crumbs: [{ label: "Investigation Queue", to: "/investigations" }, { label: "Case" }],
    };
  if (pathname.startsWith("/reports/"))
    return {
      title: "Analysis Report",
      crumbs: [{ label: "Reports", to: "/reports" }, { label: "Run Detail" }],
    };
  return titles[pathname] ?? { title: "FraudGuard AI", crumbs: [{ label: "FraudGuard AI" }] };
}

function ShellLayout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { title, crumbs } = resolve(pathname);

  return (
    <div className="flex min-h-screen w-full bg-background">
      <AppSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} breadcrumb={crumbs} />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
      <Toaster />
    </div>
  );
}
