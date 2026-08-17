import axios from "axios";
import type {
  Claim,
  Provider,
  RiskLevel,
  CaseStatus,
} from "@/types";

/* =========================================================
   API CONFIGURATION
   ========================================================= */

export const API_BASE_URL =
  import.meta.env["VITE_API_BASE_URL"] ||
  "http://127.0.0.1:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000,
});

/* =========================================================
   AXIOS ERROR HANDLING
   ========================================================= */

api.interceptors.response.use(
  (response) => response,

  (error) => {
    console.error(
      "Backend API error:",
      error?.response?.data ||
        error?.message ||
        error,
    );

    return Promise.reject(error);
  },
);

/* =========================================================
   BACKEND TYPES
   ========================================================= */

export interface BackendAnalytics {
  fraud_flagged: number;
  fraud_rate: number;
  not_flagged: number;
  threshold: number;
  total_claims: number;
  total_providers: number;
  total_reimbursement: number;
  average_claim_reimbursement: number;
  average_provider_claims: number;
  average_provider_average_reimbursement: number;
  average_provider_inpatient_claims: number;
}

export interface BackendProvider {
  Provider: string;

  TotalClaims: number;
  UniqueBeneficiaries: number;

  TotalReimbursement: number;
  AverageReimbursement: number;
  MaxReimbursement: number;
  StdReimbursement: number;

  AveragePatientAge: number;
  AverageDeductiblePaid: number;

  AveragePartACoverage: number;
  AveragePartBCoverage: number;

  ClaimsPerBeneficiary: number;
  InpatientShare: number;

  UniqueAttendingPhysicians: number;
  UniqueOperatingPhysicians: number;
  UniqueOtherPhysicians: number;

  decision?: "FRAUD_FLAG" | "NOT_FLAGGED";
  fraud_probability?: number;
  threshold?: number;

  [key: string]: unknown;
}

export interface BackendProvidersResponse {
  page: number;
  page_size: number;
  providers: BackendProvider[];
  total: number;
  total_pages: number;
}

export interface BackendProviderResponse {
  provider: BackendProvider;
}

/* =========================================================
   BACKEND CLAIM
   ========================================================= */

export interface BackendClaim {
  ClaimID: string;
  Provider: string;

  BeneID?: string;
  ClaimType?: string;

  InscClaimAmtReimbursed?: number;

  ClaimStartDt?: string;
  ClaimEndDt?: string;

  AttendingPhysician?: string;
  OperatingPhysician?: string;
  OtherPhysician?: string;

  // Optional dataset label indicating whether this claim is marked as potential fraud in the source dataset.
  // Values observed in the combined dataset are "Yes" / "No" but keep flexible for null/number variants.
  PotentialFraud?: string | number | boolean | null;

  [key: string]: unknown;
}

export interface BackendClaimsResponse {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  provider_id?: string | null;
  claims: BackendClaim[];
}

export interface BackendPrediction {
  provider_id: string;
  fraud_probability: number;
  threshold: number;
  decision:
    | "FRAUD_FLAG"
    | "NOT_FLAGGED";
}

export interface EvidenceFactorResponse {
  name: string;
  provider_value?: number | null;
  claim_value?: number | null;
  peer_value?: number | null;
  difference_percent?: number | null;
  direction?: string | null;
  impact?: string | null;
  note?: string | null;
}

export interface ClaimExplanationResponse {
  claim_id: string;
  provider_id?: string | null;
  risk?: {
    scope: string;
    fraud_probability?: number | null;
    threshold?: number | null;
    decision?: string | null;
  } | null;
  summary?: string | null;
  evidence_basis?: {
    peer_definition?: string | null;
    provider_cohort_size?: number | null;
  } | null;
  factors?: EvidenceFactorResponse[] | null;
  model_contributions?: unknown[] | null;
  related_claims?: Array<{
    claim_id?: string | null;
    claim_type?: string | null;
    reimbursement?: number | null;
    claim_start_date?: string | null;
    claim_end_date?: string | null;
  }> | null;
  review_focus?: string[] | null;
  disclaimer?: string | null;
}

/* =========================================================
   RISK MAPPING
   ========================================================= */

function getRiskLevel(
  probability: number,
): RiskLevel {
  if (probability >= 0.75) {
    return "Critical";
  }

  if (probability >= 0.50) {
    return "High";
  }

  if (probability >= 0.23) {
    return "Medium";
  }

  return "Low";
}

/* =========================================================
   STATUS MAPPING
   ========================================================= */

function getStatus(
  decision?: string,
): CaseStatus {
  if (decision === "FRAUD_FLAG") {
    return "New";
  }

  return "Resolved";
}

/* =========================================================
   PROVIDER MAPPING
   ========================================================= */

function mapProvider(
  provider: BackendProvider,
): Provider {
  const probability = Number(
    provider.fraud_probability ?? 0,
  );

  const totalClaims = Number(
    provider.TotalClaims ?? 0,
  );

  const inpatientShare = Number(
    provider.InpatientShare ?? 0,
  );

  return {
    provider_id:
      provider.Provider,

    risk_score: Number(
      (probability * 100).toFixed(2),
    ),

    risk_level:
      getRiskLevel(probability),

    claim_count:
      totalClaims,

    beneficiary_count:
      Number(
        provider.UniqueBeneficiaries ?? 0,
      ),

    total_reimbursement:
      Number(
        provider.TotalReimbursement ?? 0,
      ),

    average_reimbursement:
      Number(
        provider.AverageReimbursement ?? 0,
      ),

    inpatient_claims:
      Math.round(
        totalClaims *
          inpatientShare,
      ),

    outpatient_claims:
      Math.round(
        totalClaims *
          (1 - inpatientShare),
      ),

    status:
      getStatus(
        provider.decision,
      ),
  };
}

/* =========================================================
   CLAIM MAPPING
   ========================================================= */

/*
 * IMPORTANT:
 *
 * The current /claims backend endpoint returns raw
 * claim-level records.
 *
 * It does NOT currently return a claim-level
 * fraud_probability.
 *
 * Therefore this mapper currently uses 0 as the
 * claim probability.
 *
 * Provider-level fraud prediction is already available
 * through /providers and /predict.
 *
 * Later we can add real claim-level scoring to the
 * backend without changing the Claims page structure.
 */

export function mapBackendClaim(
  claim: BackendClaim,
): Claim {
  const claimType =
    claim.ClaimType ===
    "Inpatient"
      ? "Inpatient"
      : "Outpatient";

  return {
    claim_id:
      String(
        claim.ClaimID ?? "",
      ),

    provider_id:
      String(
        claim.Provider ?? "",
      ),

    bene_id:
      String(
        claim.BeneID ?? "",
      ),

    claim_type:
      claimType,

    reimbursement:
      Number(
        claim.InscClaimAmtReimbursed ??
          0,
      ),

    claim_start_date:
      String(
        claim.ClaimStartDt ?? "",
      ),

    claim_end_date:
      String(
        claim.ClaimEndDt ?? "",
      ),

  };
}

/* =========================================================
   ANALYTICS
   ========================================================= */

export async function getAnalytics(): Promise<
  BackendAnalytics
> {
  const response =
    await api.get<BackendAnalytics>(
      "/analytics",
    );

  return response.data;
}

/* =========================================================
   PROVIDERS - PAGINATED
   ========================================================= */

export async function getProviders(
  page = 1,
  pageSize = 50,
) {
  const response =
    await api.get<BackendProvidersResponse>(
      "/providers",
      {
        params: {
          page,
          page_size:
            pageSize,
        },
      },
    );

  return {
    ...response.data,

    providers:
      response.data.providers.map(
        mapProvider,
      ),
  };
}

/* =========================================================
   SINGLE PROVIDER
   ========================================================= */

export async function getProvider(
  providerId: string,
): Promise<Provider> {
  const response =
    await api.get<BackendProviderResponse>(
      `/providers/${encodeURIComponent(
        providerId,
      )}`,
    );

  return mapProvider(
    response.data.provider,
  );
}

/* =========================================================
   PROVIDER PREDICTION
   ========================================================= */

export async function predictProvider(
  providerId: string,
): Promise<BackendPrediction> {
  const response =
    await api.post<BackendPrediction>(
      "/predict",
      {
        provider_id:
          providerId,
      },
    );

  return response.data;
}

/* =========================================================
   CLAIMS - PAGINATED
   ========================================================= */

export async function getClaims(
  page = 1,
  pageSize = 50,
  providerId?: string,
): Promise<{
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  provider_id?: string | null;
  claims: Claim[];
}> {
  const response =
    await api.get<BackendClaimsResponse>(
      "/claims",
      {
        params: {
          page,
          page_size:
            pageSize,

          ...(providerId
            ? {
                provider_id:
                  providerId,
              }
            : {}),
        },
      },
    );

  const data =
    response.data;

  /*
   * THIS IS THE IMPORTANT FIX.
   *
   * Backend:
   *     BackendClaim[]
   *
   * Frontend:
   *     Claim[]
   *
   * Convert every record before
   * returning the response.
   */

  const mappedClaims =
    data.claims.map(mapBackendClaim);

  return {
    page:
      data.page,

    page_size:
      data.page_size,

    total:
      data.total,

    total_pages:
      data.total_pages,

    provider_id:
      data.provider_id ?? null,

    claims:
      mappedClaims,
  };
}
export async function getClaim(
  claimId: string,
): Promise<BackendClaim> {
  const response = await api.get<{
    claim: BackendClaim;
  }>(
    `/claims/${encodeURIComponent(claimId)}`,
  );

  return response.data.claim;
}

/* =========================================================
   CLAIM EXPLANATION / EVIDENCE
   ========================================================= */

export async function getClaimExplanation(
  claimId: string,
): Promise<ClaimExplanationResponse> {
  const response = await api.get<ClaimExplanationResponse>(
    `/claims/${encodeURIComponent(claimId)}/explanation`,
  );

  return response.data as ClaimExplanationResponse;
}

/* =========================================================
   CSV ANALYSIS
   ========================================================= */

export async function analyzeCsv(
  file: File,
) {
  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );

  const response =
    await api.post(
      "/analyze/csv",
      formData,
      {
        headers: {
          "Content-Type":
            "multipart/form-data",
        },

        timeout:
          120_000,
      },
    );

  return response.data;
}

/* =========================================================
   HEALTH CHECK
   ========================================================= */

export async function checkHealth() {
  const backendBaseUrl =
    API_BASE_URL.replace(
      "/api/v1",
      "",
    );

  const response =
    await axios.get(
      `${backendBaseUrl}/health`,
      {
        timeout:
          10_000,
      },
    );

  return response.data;
}
