import { createFileRoute } from "@tanstack/react-router";
import { ImportData } from "@/pages/ImportData";

export const Route = createFileRoute("/_shell/import")({
  head: () => ({
    meta: [
      { title: "Import Claims Data | FraudGuard AI" },
      { name: "description", content: "Upload a CSV or JSON claims dataset for validation and fraud risk analysis." },
      { property: "og:title", content: "Import Claims Data | FraudGuard AI" },
      { property: "og:description", content: "Upload a CSV or JSON claims dataset for validation and risk analysis." },
    ],
  }),
  component: ImportData,
});
