import { useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { CheckCircle2, FileSpreadsheet, Loader2, Upload, X } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { uploadDataset } from "@/services/mockApi";
import type { DatasetInfo } from "@/types";
import { cn } from "@/lib/utils";

export function ImportData() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    const ok = /\.(csv|json)$/i.test(file.name);
    if (!ok) {
      setError("Unsupported file type. Upload a .csv or .json dataset.");
      setDataset(null);
      return;
    }
    setError(null);
    setUploading(true);
    uploadDataset(file)
      .then(setDataset)
      .catch(() => setError("Upload failed. Try again."))
      .finally(() => setUploading(false));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Import Claims Data"
        subtitle="Upload a CSV or JSON dataset for validation and risk analysis."
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        className={cn(
          "panel flex flex-col items-center justify-center gap-3 border-2 border-dashed px-6 py-16 text-center transition-colors",
          dragging ? "border-primary bg-info-soft" : "border-border",
        )}
      >
        <span className="grid size-14 place-items-center rounded-full bg-secondary text-muted-foreground">
          {uploading ? <Loader2 className="size-6 animate-spin" /> : <Upload className="size-6" />}
        </span>
        <p className="text-sm font-semibold text-foreground">Drag &amp; Drop your file here</p>
        <p className="text-xs text-muted-foreground">OR</p>
        <Button variant="outline" onClick={() => inputRef.current?.click()} disabled={uploading}>
          Browse Files
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.json"
          className="sr-only"
          aria-label="Upload dataset file"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <p className="mt-2 text-xs text-muted-foreground">Supported formats: CSV, JSON</p>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-center justify-between gap-3 rounded-md border border-risk-critical/30 bg-risk-critical-soft px-4 py-3 text-sm text-risk-critical"
        >
          {error}
          <button type="button" aria-label="Dismiss error" onClick={() => setError(null)}>
            <X className="size-4" />
          </button>
        </div>
      )}

      {!dataset && !uploading && !error && (
        <p className="text-center text-xs text-muted-foreground">
          No dataset uploaded yet. Frontend-only mock upload — no data leaves your browser.
        </p>
      )}

      {dataset && (
        <section className="panel p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <span className="grid size-11 place-items-center rounded-lg bg-success-soft text-success">
                <FileSpreadsheet className="size-5" />
              </span>
              <div>
                <p className="text-sm font-semibold text-foreground">{dataset.file_name}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{dataset.file_size}</p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-md bg-success-soft px-2.5 py-1 text-xs font-medium text-success">
              <CheckCircle2 className="size-3.5" /> Upload complete
            </span>
          </div>

          <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Rows", dataset.rows.toLocaleString()],
              ["Columns", dataset.columns.toLocaleString()],
              ["Providers", dataset.providers.toLocaleString()],
              ["Beneficiaries", dataset.beneficiaries.toLocaleString()],
            ].map(([label, value]) => (
              <div key={label} className="rounded-md border border-border bg-secondary/40 p-4">
                <dt className="text-xs uppercase tracking-wider text-muted-foreground">{label}</dt>
                <dd className="mt-1 text-xl font-semibold tabular">{value}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button
              disabled={validating}
              onClick={() => {
                setValidating(true);
                setTimeout(() => navigate({ to: "/data-quality" }), 600);
              }}
            >
              {validating && <Loader2 className="size-4 animate-spin" />}
              {validating ? "Validating…" : "Validate Dataset"}
            </Button>
            <Button variant="ghost" onClick={() => setDataset(null)}>
              Remove file
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}
