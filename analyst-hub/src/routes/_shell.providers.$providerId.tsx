import { createFileRoute } from "@tanstack/react-router";
import { ProviderDetails } from "@/pages/ProviderDetails";

export const Route = createFileRoute("/_shell/providers/$providerId")({
  head: () => ({
    meta: [
      { title: "Provider Profile | FraudGuard AI" },
      { name: "description", content: "Provider billing profile, peer comparison and AI interpretation of model-derived signals." },
      { property: "og:title", content: "Provider Profile | FraudGuard AI" },
      { property: "og:description", content: "Provider billing profile, peer comparison and AI interpretation." },
    ],
  }),
  component: ProviderDetails,
});
