import { createFileRoute } from "@tanstack/react-router";
import { Dashboard } from "@/pages/Dashboard";

export const Route = createFileRoute("/_shell/dashboard")({
  head: () => ({
    meta: [
      { title: "Claims Payment Integrity Dashboard | FraudGuard AI" },
      { name: "description", content: "Monitor suspicious claims, provider behavior and investigation workload across the claims dataset." },
      { property: "og:title", content: "Claims Payment Integrity Dashboard | FraudGuard AI" },
      { property: "og:description", content: "Monitor suspicious claims, provider behavior and investigation workload." },
    ],
  }),
  component: Dashboard,
});
