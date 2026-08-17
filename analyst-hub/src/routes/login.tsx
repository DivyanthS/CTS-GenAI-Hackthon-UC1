import { createFileRoute } from "@tanstack/react-router";
import { Login } from "@/pages/Login";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — FraudGuard AI" },
      {
        name: "description",
        content: "Sign in to the FraudGuard AI payment-integrity workspace to review claim risk signals and investigation cases.",
      },
      { property: "og:title", content: "Sign in — FraudGuard AI" },
      {
        property: "og:description",
        content: "Secure access to the FraudGuard AI claims payment integrity workspace.",
      },
    ],
  }),
  component: Login,
});
