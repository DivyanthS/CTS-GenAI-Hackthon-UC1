import { useState } from "react";
import { FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ReportPreview } from "@/components/reports/ReportPreview";
import { useAuth } from "@/lib/auth";
import { downloadReport, generateReport } from "@/services/reportService";
import {
  REPORT_DEFINITIONS,
  canAccessReport,
  type GeneratedReport,
  type ReportPayload,
  type ReportType,
} from "@/types/reports";

export interface ReportOption {
  type: ReportType;
  label?: string;
  build: () => Promise<ReportPayload | null> | ReportPayload | null;
}

export function ReportTypeSelector({
  options,
  label = "Generate Report",
}: {
  options: ReportOption[];
  label?: string;
}) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [open, setOpen] = useState(false);

  if (!user) return null;
  const available = options.filter((o) => canAccessReport(user.role, o.type));
  if (!available.length) return null;

  const run = async (option: ReportOption) => {
    setLoading(true);
    try {
      const payload = await option.build();
      if (!payload) {
        toast.error("Report data is not available yet.");
        return;
      }
      const generated = await generateReport(payload, user);
      setReport(generated);
      setOpen(true);
      toast.success("Report generated successfully", {
        description: `Report ID: ${generated.metadata.report_id}`,
        action: { label: "Download", onClick: () => downloadReport(generated) },
      });
    } catch (err) {
      console.error(err);
      toast.error("The report could not be generated. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button disabled={loading}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <FileText className="size-4" />}
            {loading ? "Generating…" : label}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80">
          <DropdownMenuLabel>Available for your role</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {available.map((option) => {
            const def = REPORT_DEFINITIONS.find((d) => d.type === option.type)!;
            return (
              <DropdownMenuItem
                key={option.type}
                onSelect={() => void run(option)}
                className="flex-col items-start gap-0.5"
              >
                <span className="text-sm font-medium">{option.label ?? def.title}</span>
                <span className="text-xs text-muted-foreground">{def.description}</span>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
      <ReportPreview report={report} open={open} onOpenChange={setOpen} />
    </>
  );
}
