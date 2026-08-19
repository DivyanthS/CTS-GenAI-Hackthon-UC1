import { useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ReportPreview } from "@/components/reports/ReportPreview";
import { useAuth } from "@/lib/auth";
import { downloadReport, generateReport } from "@/services/reportService";
import { canAccessReport, type GeneratedReport, type ReportPayload, type ReportType } from "@/types/reports";

export function ReportButton({
  type,
  label,
  build,
  mode = "preview",
  variant = "outline",
  size = "sm",
}: {
  type: ReportType;
  label: string;
  /** Assembles the report payload — may fetch from the (mock) API. */
  build: () => Promise<ReportPayload | null> | ReportPayload | null;
  /** "preview" opens the preview modal; "download" downloads immediately. */
  mode?: "preview" | "download";
  variant?: "default" | "outline" | "secondary" | "ghost";
  size?: "sm" | "default";
}) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [open, setOpen] = useState(false);

  if (!user || !canAccessReport(user.role, type)) return null;

  const run = async () => {
    setLoading(true);
    try {
      const payload = await build();
      if (!payload) {
        toast.error("Report data is not available yet.");
        return;
      }
      const generated = await generateReport(payload, user);
      setReport(generated);
      if (mode === "download") {
        downloadReport(generated);
        toast.success("Report generated successfully", {
          description: `Report ID: ${generated.metadata.report_id}`,
          action: { label: "Preview", onClick: () => setOpen(true) },
        });
      } else {
        setOpen(true);
        toast.success("Report generated successfully", {
          description: `Report ID: ${generated.metadata.report_id}`,
          action: { label: "Download", onClick: () => downloadReport(generated) },
        });
      }
    } catch (err) {
      console.error(err);
      toast.error("The report could not be generated. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button variant={variant} size={size} onClick={run} disabled={loading}>
        {loading ? (
          <Loader2 className="size-4 animate-spin" />
        ) : mode === "download" ? (
          <Download className="size-4" />
        ) : (
          <FileText className="size-4" />
        )}
        {loading ? "Generating…" : label}
      </Button>
      <ReportPreview report={report} open={open} onOpenChange={setOpen} />
    </>
  );
}
