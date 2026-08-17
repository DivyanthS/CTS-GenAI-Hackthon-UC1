import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";

import { PageHeader } from "@/components/common/PageHeader";
import {
  DataTable,
  type Column,
} from "@/components/common/DataTable";
import { RiskBadge } from "@/components/common/RiskBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";

import { getClaims } from "@/services/api";
import type { Claim } from "@/types";

const PAGE_SIZE = 50;

const currency = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  return `$${value.toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })}`;
};

export function Claims() {
  const navigate = useNavigate();

  // ============================================================
  // DATA STATE
  // ============================================================

  const [claims, setClaims] = useState<Claim[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  // ============================================================
  // FILTER STATE
  // ============================================================

  const [providerId, setProviderId] =
    useState<string>("");

  // ============================================================
  // PAGINATION STATE
  // ============================================================

  const [page, setPage] = useState(1);

  const [total, setTotal] = useState(0);

  const [totalPages, setTotalPages] = useState(0);

  // ============================================================
  // LOAD CLAIMS
  // ============================================================

  useEffect(() => {
    let cancelled = false;

    async function loadClaims() {
      try {
        setLoading(true);
        setError(null);

        const response = await getClaims(
          page,
          PAGE_SIZE,
          providerId.trim() || undefined,
        );

        if (cancelled) {
          return;
        }

        setClaims(response.claims);
        setTotal(response.total);
        setTotalPages(response.total_pages);
      } catch (err) {
        if (cancelled) {
          return;
        }

        console.error(
          "Failed to load claims:",
          err,
        );

        setClaims([]);
        setTotal(0);
        setTotalPages(0);

        setError(
          "Unable to load claims from the backend.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadClaims();

    return () => {
      cancelled = true;
    };
  }, [page, providerId]);

  // ============================================================
  // TABLE COLUMNS
  // ============================================================

  const columns: Column<Claim>[] = [
    {
      key: "claim_id",
      header: "Claim ID",
      sortValue: (row) => row.claim_id,

      render: (row) => (
        <span className="font-mono text-xs font-medium text-primary">
          {row.claim_id}
        </span>
      ),
    },

    {
      key: "provider_id",
      header: "Provider",
      sortValue: (row) => row.provider_id,

      render: (row) => (
        <span className="font-mono text-xs">
          {row.provider_id}
        </span>
      ),
    },

    {
      key: "claim_type",
      header: "Type",
      sortValue: (row) => row.claim_type,

      render: (row) => (
        <span>
          {row.claim_type}
        </span>
      ),
    },

    {
      key: "reimbursement",
      header: "Reimbursement",
      align: "right",
      sortValue: (row) =>
        row.reimbursement ?? 0,

      render: (row) =>
        currency(row.reimbursement),
    },

    {
      key: "risk",
      header: "Claim risk",
      render: () => <span className="text-xs text-muted-foreground">Not available</span>,
    },

    {
      key: "status",
      header: "Status",
      render: () => <span className="text-xs text-muted-foreground">Not available</span>,
    },

    {
      key: "date",
      header: "Claim Start",
      sortValue: (row) =>
        row.claim_start_date ?? "",

      render: (row) => (
        <span className="text-xs text-muted-foreground">
          {row.claim_start_date || "—"}
        </span>
      ),
    },
  ];

  // ============================================================
  // PAGE NAVIGATION
  // ============================================================

  const goToPreviousPage = () => {
    if (page > 1) {
      setPage((current) => current - 1);
    }
  };

  const goToNextPage = () => {
    if (page < totalPages) {
      setPage((current) => current + 1);
    }
  };

  // ============================================================
  // PROVIDER FILTER
  // ============================================================

  const handleProviderFilter = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setProviderId(event.target.value);
    setPage(1);
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="space-y-6">
      {/* ========================================================
          HEADER
         ======================================================== */}

      <PageHeader
        title="Claims"
        subtitle="Claim records with provider-level risk available in claim details."
      />

      {/* ========================================================
          PROVIDER FILTER
         ======================================================== */}

      <div className="flex flex-col gap-3 rounded-lg border bg-card p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-1 flex-col gap-2">
          <label
            htmlFor="provider-filter"
            className="text-sm font-medium"
          >
            Provider ID
          </label>

          <input
            id="provider-filter"
            type="text"
            value={providerId}
            onChange={handleProviderFilter}
            placeholder="Search provider e.g. PRV55912"
            className="h-9 w-full rounded-md border bg-background px-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary md:max-w-sm"
          />
        </div>

        {providerId && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setProviderId("");
              setPage(1);
            }}
          >
            Clear Provider
          </Button>
        )}
      </div>

      {/* ========================================================
          TABLE
         ======================================================== */}

      <DataTable
        data={claims}
        columns={columns}
        rowKey={(row) => row.claim_id}
        searchable={(row) =>
          `${row.claim_id} ${row.provider_id} ${row.bene_id}`
        }
        searchPlaceholder="Search claim, provider or beneficiary…"
        loading={loading}
        error={error}
        emptyTitle="No claims match your filters"
        onRowClick={(row) =>
          navigate({
            to: "/claims/$claimId",
            params: {
              claimId: row.claim_id,
            },
          })
        }
      />

      {/* ========================================================
          PAGINATION
         ======================================================== */}

      {!loading && !error && total > 0 && (
        <div className="flex flex-col gap-3 rounded-lg border bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Result information */}

          <div className="text-sm text-muted-foreground">
            Showing{" "}
            <span className="font-medium text-foreground">
              {(page - 1) * PAGE_SIZE + 1}
            </span>{" "}
            to{" "}
            <span className="font-medium text-foreground">
              {Math.min(
                page * PAGE_SIZE,
                total,
              )}
            </span>{" "}
            of{" "}
            <span className="font-medium text-foreground">
              {total.toLocaleString()}
            </span>{" "}
            claims
          </div>

          {/* Pagination controls */}

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || loading}
              onClick={goToPreviousPage}
            >
              Previous
            </Button>

            <div className="min-w-[120px] text-center text-sm">
              Page{" "}
              <span className="font-medium">
                {page}
              </span>{" "}
              of{" "}
              <span className="font-medium">
                {totalPages}
              </span>
            </div>

            <Button
              variant="outline"
              size="sm"
              disabled={
                page >= totalPages ||
                loading
              }
              onClick={goToNextPage}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
