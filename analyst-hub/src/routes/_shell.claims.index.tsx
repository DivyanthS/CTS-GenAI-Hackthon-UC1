import { createFileRoute } from "@tanstack/react-router";
import { Claims } from "@/pages/Claims";

export const Route = createFileRoute("/_shell/claims/")({
  head: () => ({
    meta: [
      { title: "Scored Claims | FraudGuard AI" },
      { name: "description", content: "Browse, filter and sort scored claims by risk level, claim type and status." },
      { property: "og:title", content: "Scored Claims | FraudGuard AI" },
      { property: "og:description", content: "Browse, filter and sort scored claims by risk level and status." },
    ],
  }),
  component: Claims,
});
