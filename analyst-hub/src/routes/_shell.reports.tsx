import { createFileRoute } from "@tanstack/react-router";
import { Reports } from "@/pages/Reports";

export const Route = createFileRoute("/_shell/reports")({
  head: () => ({
    meta: [
      { title: "Reports | FraudGuard AI" },
      { name: "description", content: "Review analysis runs and access backend-generated PDF reports." },
      { property: "og:title", content: "Reports | FraudGuard AI" },
      { property: "og:description", content: "Open run details and PDF reports from the backend." },
    ],
  }),
  component: Reports,
});
