import { createFileRoute } from "@tanstack/react-router";
import { Login } from "@/pages/Login";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "FraudGuard AI — Claims Payment Integrity" },
      { name: "description", content: "Sign in to FraudGuard AI to review AI-assisted claims risk scores, model evidence and investigation cases." },
      { property: "og:title", content: "FraudGuard AI — Claims Payment Integrity" },
      { property: "og:description", content: "AI-assisted claims payment integrity and fraud risk detection for investigators." },
    ],
  }),
  component: Login,
});
