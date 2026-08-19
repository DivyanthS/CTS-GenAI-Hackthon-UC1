import { createFileRoute } from "@tanstack/react-router";
import { Settings } from "@/pages/Settings";

export const Route = createFileRoute("/_shell/settings")({
  head: () => ({
    meta: [
      { title: "Settings | FraudGuard AI" },
      { name: "description", content: "Profile, notification and application preferences for the payment-integrity workspace." },
      { property: "og:title", content: "Settings | FraudGuard AI" },
      { property: "og:description", content: "Profile, notification and application preferences." },
    ],
  }),
  component: Settings,
});
