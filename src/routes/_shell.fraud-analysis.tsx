import { createFileRoute } from "@tanstack/react-router";
import { FraudAnalysis } from "@/pages/FraudAnalysis";

export const Route = createFileRoute("/_shell/fraud-analysis")({
  head: () => ({
    meta: [
      { title: "Fraud Risk Analysis | FraudGuard AI" },
      { name: "description", content: "Run the ML risk pipeline over the selected dataset and generate evidence-grounded explanations." },
      { property: "og:title", content: "Fraud Risk Analysis | FraudGuard AI" },
      { property: "og:description", content: "Run the ML risk pipeline and generate evidence-grounded explanations." },
    ],
  }),
  component: FraudAnalysis,
});
