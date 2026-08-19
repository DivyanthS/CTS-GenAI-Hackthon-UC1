import { createFileRoute } from "@tanstack/react-router";
import { DataQuality } from "@/pages/DataQuality";

export const Route = createFileRoute("/_shell/data-quality")({
  head: () => ({
    meta: [
      { title: "Data Quality | FraudGuard AI" },
      { name: "description", content: "Dataset health, validation checks and schema conformance for the claims dataset." },
      { property: "og:title", content: "Data Quality | FraudGuard AI" },
      { property: "og:description", content: "Dataset health, validation checks and schema conformance." },
    ],
  }),
  component: DataQuality,
});
