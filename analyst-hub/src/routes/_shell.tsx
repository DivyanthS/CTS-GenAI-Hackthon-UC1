import { Outlet, createFileRoute, useRouterState } from "@tanstack/react-router";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { TopBar } from "@/components/layout/TopBar";
import { Toaster } from "@/components/ui/sonner";

export const Route = createFileRoute("/_shell")({
  component: ShellLayout,
});

const titles: Record<string, { title: string; crumbs: { label: string; to?: string }[] }> = {
  "/dashboard": { title: "Dashboard", crumbs: [{ label: "Overview" }, { label: "Dashboard" }] },
  "/import": { title: "Import Data", crumbs: [{ label: "Data" }, { label: "Import Data" }] },
  "/data-quality": { title: "Data Quality", crumbs: [{ label: "Data" }, { label: "Data Quality" }] },
  "/fraud-analysis": {
    title: "Fraud Risk Analysis",
    crumbs: [{ label: "Risk Intelligence" }, { label: "Fraud Analysis" }],
  },
  "/claims": { title: "Claims", crumbs: [{ label: "Risk Intelligence" }, { label: "Claims" }] },
  "/providers": {
    title: "Provider Risk Intelligence",
    crumbs: [{ label: "Risk Intelligence" }, { label: "Providers" }],
  },
  "/investigations": {
    title: "Investigation Queue",
    crumbs: [{ label: "Investigation" }, { label: "Queue" }],
  },
  "/analytics": { title: "Analytics", crumbs: [{ label: "Analytics" }] },
  "/profile": { title: "Analyst Profile", crumbs: [{ label: "Account" }, { label: "Profile" }] },
  "/settings": { title: "Settings", crumbs: [{ label: "System" }, { label: "Settings" }] },
};

function resolve(pathname: string) {
  if (pathname.startsWith("/claims/"))
    return { title: "Claim Details", crumbs: [{ label: "Claims", to: "/claims" }, { label: "Claim Details" }] };
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
