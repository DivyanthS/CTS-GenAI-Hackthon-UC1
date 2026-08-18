import { useEffect, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getModelStatus, getThreshold, updateThreshold } from "@/services/api";

export function Settings() {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [thresholds, setThresholds] = useState({ low_threshold: 0.23, high_threshold: 0.6, critical_threshold: 0.8 });
  const [modelStatus, setModelStatus] = useState<{ active_version?: string; status?: string; model_type?: string; decision_threshold?: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [status, threshold] = await Promise.all([getModelStatus(), getThreshold()]);
      setModelStatus(status);
      setThresholds({
        low_threshold: Number(threshold.low_threshold ?? 0.23),
        high_threshold: Number(threshold.high_threshold ?? 0.6),
        critical_threshold: Number(threshold.critical_threshold ?? 0.8),
      });
    } catch {
      setError("Unable to load system thresholds and model status.");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const saveThresholds = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateThreshold(thresholds);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setError("Unable to update the risk thresholds.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Operational model state, risk thresholds, and scoring configuration."
        actions={<Button onClick={saveThresholds} disabled={saving}>{saving ? "Saving…" : saved ? "Saved" : "Save changes"}</Button>}
      />

      {error && (
        <div className="rounded-md border border-risk-critical/30 bg-risk-critical-soft px-4 py-3 text-sm text-risk-critical">
          {error}
        </div>
      )}

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Model Configuration</h2>
        <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="active-model">Active Model</Label>
            <Input id="active-model" value={modelStatus?.model_type ?? "Loading…"} readOnly />
          </div>
          <div className="space-y-2">
            <Label htmlFor="model-version">Model Version</Label>
            <Input id="model-version" value={modelStatus?.active_version ?? "Loading…"} readOnly />
          </div>
          <div className="space-y-2">
            <Label htmlFor="model-status">Model Status</Label>
            <Input id="model-status" value={modelStatus?.status ?? "Loading…"} readOnly />
          </div>
          <div className="space-y-2">
            <Label htmlFor="threshold-current">Decision Threshold</Label>
            <Input id="threshold-current" value={String(modelStatus?.decision_threshold ?? thresholds.low_threshold)} readOnly />
          </div>
        </div>
      </section>

      <section className="panel p-6">
        <h2 className="text-sm font-semibold">Risk Thresholds</h2>
        <div className="mt-5 grid gap-5 sm:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="low-threshold">Low Threshold</Label>
            <Input
              id="low-threshold"
              type="number"
              min={0}
              max={1}
              step="0.01"
              value={thresholds.low_threshold}
              onChange={(e) => setThresholds((prev) => ({ ...prev, low_threshold: Number(e.target.value) }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="high-threshold">High Threshold</Label>
            <Input
              id="high-threshold"
              type="number"
              min={0}
              max={1}
              step="0.01"
              value={thresholds.high_threshold}
              onChange={(e) => setThresholds((prev) => ({ ...prev, high_threshold: Number(e.target.value) }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="critical-threshold">Critical Threshold</Label>
            <Input
              id="critical-threshold"
              type="number"
              min={0}
              max={1}
              step="0.01"
              value={thresholds.critical_threshold}
              onChange={(e) => setThresholds((prev) => ({ ...prev, critical_threshold: Number(e.target.value) }))}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
