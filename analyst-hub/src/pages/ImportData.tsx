import { useMemo, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { CheckCircle2, FileSpreadsheet, Loader2, Upload, X } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { validateCsv, importProviders, analyzeCsv } from "@/services/api";
import { cn } from "@/lib/utils";

const formatBytes = (bytes: number) => {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** unitIndex;
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
};

function parseCsvText(text: string) {
  const rows: string[][] = [];
  let current = "";
  let row: string[] = [];
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      row.push(current);
      current = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") {
        i += 1;
      }
      row.push(current);
      if (row.some((cell) => cell.trim() !== "")) {
        rows.push(row);
      }
      row = [];
      current = "";
      continue;
    }

    current += char;
  }

  if (current.length > 0 || row.length > 0) {
    row.push(current);
    if (row.some((cell) => cell.trim() !== "")) {
      rows.push(row);
    }
  }

  return rows;
}

export function ImportData() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<Record<string, unknown> | null>(null);
  const [previewRows, setPreviewRows] = useState<string[][]>([]);
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [importResult, setImportResult] = useState<Record<string, unknown> | null>(null);
  const [analysisResult, setAnalysisResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const summary = useMemo(() => {
    if (!validation) return null;
    return {
      valid: Boolean((validation as any).valid),
      rows: Number((validation as any).rows ?? 0),
      columns: Number((validation as any).columns ?? 0),
      providers: Number((validation as any).providers ?? 0),
      beneficiaries: Number((validation as any).beneficiaries ?? 0),
      health: Number((validation as any).health_score ?? 0),
    };
  }, [validation]);

  const applyValidationResult = (result: Record<string, unknown>) => {
    setValidation(result);
    sessionStorage.setItem("dataset-validation", JSON.stringify(result));
  };

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    if (!/\.csv$/i.test(file.name)) {
      setError("Unsupported file type. Upload a CSV file containing provider-level data.");
      setSelectedFile(null);
      setValidation(null);
      setPreviewRows([]);
      setPreviewColumns([]);
      return;
    }

    setError(null);
    setSelectedFile(file);
    setImportResult(null);
    setAnalysisResult(null);
    setUploading(true);
    setValidating(true);

    try {
      const result = await validateCsv(file);
      applyValidationResult(result);
      sessionStorage.setItem("last-uploaded-file", file.name);

      const text = await file.text();
      const parsed = parseCsvText(text);
      if (parsed.length > 0) {
        const cols = parsed[0].map((value) => value.trim() || `Column ${value}`);
        const dataRows = parsed.slice(1, 21).map((row) => [...row]);
        setPreviewColumns(cols);
        setPreviewRows(dataRows);
      } else {
        setPreviewColumns([]);
        setPreviewRows([]);
      }
    } catch (e: any) {
      const message = e?.response?.data?.message ?? e?.message ?? "Backend validation failed for the selected CSV.";
      setError(message);
    } finally {
      setUploading(false);
      setValidating(false);
    }
  };

  const handleImport = async () => {
    if (!selectedFile) {
      setError("Please select a CSV file before importing provider data.");
      return;
    }

    setImporting(true);
    setError(null);
    try {
      const result = await importProviders(selectedFile);
      setImportResult(result);
      sessionStorage.setItem("providers-import-result", JSON.stringify(result));
    } catch (e: any) {
      const message = e?.response?.data?.message ?? e?.message ?? "Provider import failed.";
      setError(message);
    } finally {
      setImporting(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError("Please select a CSV file before running analysis.");
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeCsv(selectedFile);
      setAnalysisResult(result);
      sessionStorage.setItem("analysis-result", JSON.stringify(result));
    } catch (e: any) {
      const message = e?.response?.data?.message ?? e?.message ?? "Dataset analysis failed.";
      setError(message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Import Provider Dataset"
        subtitle="Upload a CSV containing provider-level data for validation, preview, import, and analysis."
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
          void handleFile(e.dataTransfer.files?.[0]);
        }}
        className={cn(
          "panel flex flex-col items-center justify-center gap-3 border-2 border-dashed px-6 py-16 text-center transition-colors",
          dragging ? "border-primary bg-info-soft" : "border-border",
        )}
      >
        <span className="grid size-14 place-items-center rounded-full bg-secondary text-muted-foreground">
          {uploading || validating ? <Loader2 className="size-6 animate-spin" /> : <Upload className="size-6" />}
        </span>
        <p className="text-sm font-semibold text-foreground">Drag &amp; Drop provider CSV here</p>
        <p className="text-xs text-muted-foreground">OR</p>
        <Button variant="outline" onClick={() => inputRef.current?.click()} disabled={uploading || validating}>
          Choose File
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="sr-only"
          aria-label="Upload provider dataset"
          onChange={(e) => void handleFile(e.target.files?.[0])}
        />
        <p className="mt-2 text-xs text-muted-foreground">CSV only. Provider data is imported from the uploaded file.</p>
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

      {selectedFile && (
        <section className="panel p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <span className="grid size-11 place-items-center rounded-lg bg-success-soft text-success">
                <FileSpreadsheet className="size-5" />
              </span>
              <div>
                <p className="text-sm font-semibold text-foreground">{selectedFile.name}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{formatBytes(selectedFile.size)}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setSelectedFile(null)}>
                Remove file
              </Button>
            </div>
          </div>

          {summary && (
            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <div className="rounded-md border border-border bg-secondary/40 p-4">
                <dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Rows</dt>
                <dd className="mt-2 text-xl font-semibold tabular">{summary.rows.toLocaleString()}</dd>
              </div>
              <div className="rounded-md border border-border bg-secondary/40 p-4">
                <dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Columns</dt>
                <dd className="mt-2 text-xl font-semibold tabular">{summary.columns.toLocaleString()}</dd>
              </div>
              <div className="rounded-md border border-border bg-secondary/40 p-4">
                <dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Providers</dt>
                <dd className="mt-2 text-xl font-semibold tabular">{summary.providers.toLocaleString()}</dd>
              </div>
              <div className="rounded-md border border-border bg-secondary/40 p-4">
                <dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Valid Records</dt>
                <dd className="mt-2 text-xl font-semibold tabular">{summary.valid ? "Yes" : "No"}</dd>
              </div>
              <div className="rounded-md border border-border bg-secondary/40 p-4">
                <dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Dataset Health</dt>
                <dd className="mt-2 text-xl font-semibold tabular">{summary.health}%</dd>
              </div>
            </div>
          )}

          {validation && Array.isArray((validation as any).checks) && (
            <div className="mt-6 rounded-md border border-border bg-secondary/30 p-4">
              <div className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">Validation Checks</div>
              <div className="space-y-2">
                {(validation as any).checks.map((check: any, index: number) => (
                  <div key={`${check.name}-${index}`} className="flex flex-wrap items-start justify-between gap-3 rounded border border-border bg-background/70 px-3 py-2">
                    <div>
                      <div className="text-sm font-medium text-foreground">{check.name}</div>
                      <div className="text-xs text-muted-foreground">{check.message ?? check.detail}</div>
                    </div>
                    <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                      {check.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {previewColumns.length > 0 && (
            <div className="mt-6">
              <div className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">Dataset Preview</div>
              <div className="overflow-x-auto rounded-md border border-border">
                <table className="min-w-full border-collapse text-left text-xs">
                  <thead className="bg-secondary/80">
                    <tr>
                      {previewColumns.map((column) => (
                        <th key={column} className="whitespace-nowrap border-b border-border px-3 py-2 font-semibold text-foreground">
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row, index) => (
                      <tr key={`${row.join("-")}-${index}`} className="border-b border-border/70 last:border-0">
                        {row.map((cell, cellIndex) => (
                          <td key={`${cell}-${cellIndex}`} className="max-w-[220px] truncate border-r border-border/70 px-3 py-2 text-muted-foreground last:border-r-0">
                            {cell || "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button variant="outline" onClick={() => navigate({ to: "/providers" })}>
              View Providers
            </Button>
            <Button onClick={handleImport} disabled={importing}>
              {importing ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
              {importing ? "Importing…" : "Import Provider Data"}
            </Button>
            <Button variant="secondary" onClick={handleAnalyze} disabled={analyzing}>
              {analyzing ? <Loader2 className="size-4 animate-spin" /> : <FileSpreadsheet className="size-4" />}
              {analyzing ? "Analyzing…" : "Analyze Dataset"}
            </Button>
          </div>

          {importResult && (
            <div className="mt-6 rounded-md border border-success/30 bg-success-soft px-4 py-3 text-sm text-success">
              {String((importResult as any).message ?? "Provider data imported successfully.")}
              {" "}
              {typeof (importResult as any).rows_imported !== "undefined" && `Imported rows: ${(importResult as any).rows_imported}.`}
            </div>
          )}

          {analysisResult && (
            <div className="mt-4 rounded-md border border-info/30 bg-info-soft px-4 py-3 text-sm text-info">
              {typeof (analysisResult as any).run_id !== "undefined" && `Run ID: ${(analysisResult as any).run_id}. `}
              {typeof (analysisResult as any).providers_analyzed !== "undefined" && `Providers analyzed: ${(analysisResult as any).providers_analyzed}.`}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
