import { LogOut, Mail, ShieldCheck } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ROLE_LABELS, useAuth, type UserRole } from "@/lib/auth";
import { reportsForRole } from "@/types/reports";

export function Profile() {
  const { user, logout, setRole } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const details: [string, string][] = [
    ["Analyst name", user.name],
    ["Email", user.email],
    ["Role", user.title],
    ["Access level", ROLE_LABELS[user.role]],
    ["Department", user.department],
    ["Account status", user.account_status],
    ["Employee ID", user.employee_id],
    ["Last login", user.last_login],
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analyst Profile"
        subtitle="Your account details and reporting permissions."
        actions={
          <Button
            variant="outline"
            onClick={() => {
              logout();
              navigate({ to: "/login" });
            }}
          >
            <LogOut className="size-4" /> Logout
          </Button>
        }
      />

      <section className="panel p-6">
        <div className="flex items-center gap-4">
          <span className="grid size-14 place-items-center rounded-full bg-secondary text-lg font-semibold text-secondary-foreground">
            {user.name.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <h2 className="text-lg font-semibold text-foreground">{user.name}</h2>
            <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Mail className="size-3.5" /> {user.email}
            </p>
            <p className="mt-0.5 text-xs font-medium text-primary">{user.title}</p>
          </div>
        </div>

        <dl className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {details.map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">{label}</dt>
              <dd className="mt-1 text-sm font-medium text-foreground">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="panel p-6">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <ShieldCheck className="size-4 text-primary" /> Reporting access
        </h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Report types available at your access level. Authorization is also enforced by the backend.
        </p>

        <div className="mt-4 max-w-xs">
          <label className="text-xs uppercase tracking-wider text-muted-foreground" htmlFor="role">
            Access level
          </label>
          <Select value={user.role} onValueChange={(v) => setRole(v as UserRole)}>
            <SelectTrigger id="role" className="mt-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(ROLE_LABELS) as UserRole[]).map((role) => (
                <SelectItem key={role} value={role}>
                  {ROLE_LABELS[role]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <ul className="mt-5 grid gap-3 md:grid-cols-2">
          {reportsForRole(user.role).map((r) => (
            <li key={r.type} className="rounded-md border border-border bg-card p-3">
              <p className="text-sm font-medium text-foreground">{r.title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{r.description}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
