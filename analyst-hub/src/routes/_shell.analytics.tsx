import { createFileRoute } from "@tanstack/react-router";
import { Analytics } from "@/pages/Analytics";

export const Route = createFileRoute("/_shell/analytics")({
  head: () => ({
    meta: [
      { title: "Risk Analytics | FraudGuard AI" },
      { name: "description", content: "Portfolio-level risk distribution, reimbursement exposure and provider peer deviations." },
      { property: "og:title", content: "Risk Analytics | FraudGuard AI" },
      { property: "og:description", content: "Risk distribution, reimbursement exposure and peer deviations." },
    ],
  }),
  component: Analytics,
});
