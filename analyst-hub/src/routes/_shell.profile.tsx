import { createFileRoute } from "@tanstack/react-router";
import { Profile } from "@/pages/Profile";

export const Route = createFileRoute("/_shell/profile")({
  head: () => ({
    meta: [
      { title: "Analyst Profile — FraudGuard AI" },
      {
        name: "description",
        content: "Review your FraudGuard AI analyst account: role, department, account status and reporting permissions.",
      },
      { property: "og:title", content: "Analyst Profile — FraudGuard AI" },
      {
        property: "og:description",
        content: "Analyst account details and reporting permissions in FraudGuard AI.",
      },
    ],
  }),
  component: Profile,
});
