import { useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export function Settings() {
  const [saved, setSaved] = useState(false);
  const [threshold, setThreshold] = useState("70");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Workspace profile, alerting and scoring preferences."
        actions={
          <Button
            onClick={() => {
              setSaved(true);
              setTimeout(() => setSaved(false), 2000);
            }}
          >
            {saved ? "Saved" : "Save changes"}
          </Button>
        }
      />

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Investigator profile</h2>
        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Full name</Label>
            <Input id="name" defaultValue="Alex Morgan" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" type="email" defaultValue="alex.morgan@payer.example" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="team">Team</Label>
            <Input id="team" defaultValue="Special Investigations Unit" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="threshold">Review threshold (risk score)</Label>
            <Input
              id="threshold"
              type="number"
              min={0}
              max={100}
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          </div>
        </div>
      </section>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Notifications</h2>
        <ul className="mt-4 divide-y divide-border">
          {[
            ["Critical risk alerts", "Notify me when a claim scores in the critical band."],
            ["Daily queue digest", "Summary of new and escalated cases each morning."],
            ["Analysis run completion", "Notify me when a scoring run finishes."],
          ].map(([title, desc], i) => (
            <li key={title} className="flex items-center justify-between gap-4 py-4">
              <div>
                <p className="text-sm font-medium text-foreground">{title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{desc}</p>
              </div>
              <Switch defaultChecked={i !== 2} aria-label={title} />
            </li>
          ))}
        </ul>
      </section>

      <p className="rounded-md border border-dashed border-border px-4 py-3 text-xs text-muted-foreground">
        Prototype settings are stored in-session only. No backend is connected.
      </p>
    </div>
  );
}
