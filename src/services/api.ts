import axios from "axios";

/**
 * Axios client prepared for the future backend.
 * No live calls are made yet — every page reads from services/mockApi.ts.
 *
 * Planned contract:
 *  POST /api/data/upload
 *  POST /api/data/validate
 *  POST /api/fraud/analyze
 *  GET  /api/dashboard/summary
 *  GET  /api/claims
 *  GET  /api/claims/{claim_id}
 *  GET  /api/providers
 *  GET  /api/providers/{provider_id}
 *  POST /api/explanation
 *  GET  /api/investigations
 *  POST /api/investigations
 *  PUT  /api/investigations/{id}
 */
export const API_BASE_URL = "http://localhost:5000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);

export const endpoints = {
  uploadDataset: "/data/upload",
  validateDataset: "/data/validate",
  runAnalysis: "/fraud/analyze",
  dashboardSummary: "/dashboard/summary",
  claims: "/claims",
  claim: (id: string) => `/claims/${id}`,
  providers: "/providers",
  provider: (id: string) => `/providers/${id}`,
  explanation: "/explanation",
  investigations: "/investigations",
  investigation: (id: string) => `/investigations/${id}`,
};
