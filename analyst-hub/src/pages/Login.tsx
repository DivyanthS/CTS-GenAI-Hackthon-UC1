import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Loader2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("analyst@fraudguard.ai");
  const [password, setPassword] = useState("demo1234");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !password.trim()) {
      setError("Enter both your email and password to continue.");
      return;
    }
    setLoading(true);
    // Mocked authentication — replaced by the backend auth endpoint later.
    setTimeout(() => {
      login(email);
      navigate({ to: "/dashboard" });
    }, 700);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-sidebar p-12 text-sidebar-foreground lg:flex">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
            <Shield className="size-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-sidebar-accent-foreground">FraudGuard AI</p>
            <p className="text-[11px] text-sidebar-foreground/60">Claims Payment Integrity</p>
          </div>
        </div>

        <div className="max-w-md">
          <h2 className="text-3xl font-semibold leading-tight text-sidebar-accent-foreground">
            Prioritize the claims that deserve a closer look.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-sidebar-foreground/70">
            An ML model scores claim and provider risk. An evidence-grounded explainer describes
            why. Your investigators make the final determination.
          </p>
          <dl className="mt-10 grid grid-cols-3 gap-6 border-t border-sidebar-border pt-6 text-sidebar-accent-foreground">
            {[
              ["558,211", "Claims scored"],
              ["5,410", "Providers"],
              ["138,556", "Beneficiaries"],
            ].map(([value, label]) => (
              <div key={label}>
                <dt className="text-lg font-semibold tabular">{value}</dt>
                <dd className="text-[11px] text-sidebar-foreground/60">{label}</dd>
              </div>
            ))}
          </dl>
        </div>

        <p className="text-[11px] text-sidebar-foreground/50">
          Risk assessment is not a determination of fraud.
        </p>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="grid size-10 place-items-center rounded-lg bg-primary text-primary-foreground">
              <Shield className="size-5" />
            </span>
            <div>
              <p className="text-sm font-semibold">FraudGuard AI</p>
              <p className="text-[11px] text-muted-foreground">Claims Payment Integrity</p>
            </div>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Access the payment-integrity workspace.
          </p>

          <form onSubmit={submit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <button
                  type="button"
                  className="text-xs text-primary underline-offset-4 hover:underline"
                >
                  Forgot password?
                </button>
              </div>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && (
              <p role="alert" className="rounded-md bg-risk-critical-soft px-3 py-2 text-xs text-risk-critical">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="size-4 animate-spin" />}
              {loading ? "Signing in…" : "Sign In"}
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-muted-foreground">
            Authentication is mocked in this prototype.
          </p>
        </div>
      </div>
    </div>
  );
}
