import { createFileRoute } from "@tanstack/react-router";
import { InvestigationQueue } from "@/pages/InvestigationQueue";

export const Route = createFileRoute("/_shell/investigations/")({
  head: () => ({
    meta: [
      { title: "Investigation Queue | FraudGuard AI" },
      { name: "description", content: "Prioritize potentially suspicious claims for investigator review and triage." },
      { property: "og:title", content: "Investigation Queue | FraudGuard AI" },
      { property: "og:description", content: "Prioritize potentially suspicious claims for investigator review." },
    ],
  }),
  component: InvestigationQueue,
});
