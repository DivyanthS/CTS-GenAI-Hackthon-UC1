import { createFileRoute } from "@tanstack/react-router";
import { InvestigationCase } from "@/pages/InvestigationCase";

export const Route = createFileRoute("/_shell/investigations/$caseId")({
  head: () => ({
    meta: [
      { title: "Investigation Case | FraudGuard AI" },
      { name: "description", content: "Investigator workflow, case timeline and status transitions for a flagged claim." },
      { property: "og:title", content: "Investigation Case | FraudGuard AI" },
      { property: "og:description", content: "Investigator workflow, case timeline and status transitions." },
    ],
  }),
  component: InvestigationCase,
});
