import { createFileRoute } from "@tanstack/react-router";
import { Providers } from "@/pages/Providers";

export const Route = createFileRoute("/_shell/providers/")({
  head: () => ({
    meta: [
      { title: "Provider Risk Intelligence | FraudGuard AI" },
      { name: "description", content: "Provider-level risk scores, claim volume, beneficiaries and reimbursement totals." },
      { property: "og:title", content: "Provider Risk Intelligence | FraudGuard AI" },
      { property: "og:description", content: "Provider-level risk scores, volume and reimbursement totals." },
    ],
  }),
  component: Providers,
});
