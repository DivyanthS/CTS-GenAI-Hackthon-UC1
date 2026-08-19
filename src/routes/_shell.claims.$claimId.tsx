import { createFileRoute } from "@tanstack/react-router";
import { ClaimDetails } from "@/pages/ClaimDetails";

export const Route = createFileRoute("/_shell/claims/$claimId")({
  head: () => ({
    meta: [
      { title: "Claim Details | FraudGuard AI" },
      { name: "description", content: "Risk score, model evidence and AI-generated explanation for a single claim." },
      { property: "og:title", content: "Claim Details | FraudGuard AI" },
      { property: "og:description", content: "Risk score, model evidence and AI-generated explanation for a single claim." },
    ],
  }),
  component: ClaimDetails,
});
