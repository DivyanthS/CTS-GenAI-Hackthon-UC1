import { useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, ChevronsUpDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  sortValue?: (row: T) => string | number;
  render: (row: T) => ReactNode;
  className?: string;
  align?: "left" | "right";
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  searchable?: (row: T) => string;
  searchPlaceholder?: string;
  pageSize?: number;
  loading?: boolean;
  error?: string | null;
  onRowClick?: (row: T) => void;
  toolbar?: ReactNode;
  emptyTitle?: string;
}

export function DataTable<T>({
  data,
  columns,
  rowKey,
  searchable,
  searchPlaceholder = "Search…",
  pageSize = 10,
  loading = false,
  error = null,
  onRowClick,
  toolbar,
  emptyTitle,
}: DataTableProps<T>) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);

  const filtered = useMemo(() => {
    if (!searchable || !query.trim()) return data;
    const q = query.trim().toLowerCase();
    return data.filter((row) => searchable(row).toLowerCase().includes(q));
  }, [data, query, searchable]);

  const sorted = useMemo(() => {
    if (!sort) return filtered;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortValue) return filtered;
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av).localeCompare(String(bv)) * dir;
    });
  }, [filtered, sort, columns]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const current = Math.min(page, totalPages);
  const rows = sorted.slice((current - 1) * pageSize, current * pageSize);

  const toggleSort = (key: string) =>
    setSort((prev) =>
      prev?.key === key ? { key, dir: prev.dir === "asc" ? "desc" : "asc" } : { key, dir: "desc" },
    );

  if (loading) return <LoadingState />;
  if (error) return <ErrorState description={error} />;

  return (
    <div className="panel overflow-hidden">
      {(searchable || toolbar) && (
        <div className="flex flex-col gap-3 border-b border-border p-4 md:flex-row md:items-center md:justify-between">
          {searchable && (
            <div className="relative w-full md:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                aria-label={searchPlaceholder}
                placeholder={searchPlaceholder}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
          )}
          {toolbar && <div className="flex flex-wrap items-center gap-2">{toolbar}</div>}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/60">
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={cn(
                    "whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground",
                    col.align === "right" && "text-right",
                  )}
                >
                  {col.sortValue ? (
                    <button
                      type="button"
                      onClick={() => toggleSort(col.key)}
                      className={cn(
                        "inline-flex items-center gap-1 rounded transition-colors hover:text-foreground",
                        col.align === "right" && "flex-row-reverse",
                      )}
                    >
                      {col.header}
                      {sort?.key === col.key ? (
                        sort.dir === "asc" ? (
                          <ArrowUp className="size-3" />
                        ) : (
                          <ArrowDown className="size-3" />
                        )
                      ) : (
                        <ChevronsUpDown className="size-3 opacity-50" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn(
                  "border-b border-border/70 last:border-0 transition-colors",
                  onRowClick && "cursor-pointer hover:bg-accent/50",
                )}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      "whitespace-nowrap px-4 py-3 text-foreground",
                      col.align === "right" && "text-right tabular",
                      col.className,
                    )}
                  >
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length === 0 && <EmptyState {...(emptyTitle ? { title: emptyTitle } : {})} />}

      {sorted.length > pageSize && (
        <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3">
          <p className="text-xs text-muted-foreground tabular">
            Showing {(current - 1) * pageSize + 1}–{Math.min(current * pageSize, sorted.length)} of{" "}
            {sorted.length}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={current === 1}
              onClick={() => setPage(current - 1)}
            >
              Previous
            </Button>
            <span className="text-xs text-muted-foreground tabular">
              Page {current} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={current === totalPages}
              onClick={() => setPage(current + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
