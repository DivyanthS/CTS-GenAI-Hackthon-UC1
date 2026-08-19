import type {
  Claim,
  DashboardSummary,
  DatasetInfo,
  Explanation,
  Investigation,
  Provider,
  RiskResult,
  SchemaField,
  ValidationCheck,
} from "@/types";
import { mockClaims } from "@/data/mockClaims";
import { mockProviders } from "@/data/mockProviders";
import { mockInvestigations } from "@/data/mockInvestigations";
import { buildExplanation, buildRiskResult } from "@/data/mockExplanations";
import {
  DATASET_CONTEXT,
  mockDashboard,
  schemaFields,
  validationChecks,
} from "@/data/mockDashboard";

const delay = <T,>(value: T, ms = 550): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), ms));

export async function uploadDataset(file: File): Promise<DatasetInfo> {
  return delay(
    {
      file_name: file.name || DATASET_CONTEXT.file_name,
      file_size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
      rows: DATASET_CONTEXT.rows,
      columns: DATASET_CONTEXT.columns,
      providers: DATASET_CONTEXT.providers,
      beneficiaries: DATASET_CONTEXT.beneficiaries,
      status: "uploaded" as const,
    },
    1200,
  );
}

export async function validateDataset(): Promise<{
  checks: ValidationCheck[];
  schema: SchemaField[];
  health: number;
}> {
  return delay({ checks: validationChecks, schema: schemaFields, health: 94 }, 900);
}

export async function runAnalysis(): Promise<{
  scored_claims: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  run_id: string;
}> {
  return delay(
    {
      scored_claims: DATASET_CONTEXT.rows,
      critical: 486,
      high: 1_356,
      medium: 12_704,
      low: 543_665,
      run_id: "RUN-4821",
    },
    600,
  );
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return delay(mockDashboard);
}

export async function getClaims(): Promise<Claim[]> {
  return delay(mockClaims);
}

export async function getClaim(claimId: string): Promise<Claim | undefined> {
  return delay(mockClaims.find((c) => c.claim_id === claimId));
}

export async function getRiskResult(claimId: string): Promise<RiskResult | undefined> {
  return delay(buildRiskResult(claimId));
}

export async function getProviders(): Promise<Provider[]> {
  return delay(mockProviders);
}

export async function getProvider(providerId: string): Promise<Provider | undefined> {
  return delay(mockProviders.find((p) => p.provider_id === providerId));
}

export async function getInvestigations(): Promise<Investigation[]> {
  return delay(mockInvestigations);
}

export async function getInvestigation(caseId: string): Promise<Investigation | undefined> {
  return delay(mockInvestigations.find((c) => c.case_id === caseId));
}

export async function getExplanation(
  providerId: string,
  level: string,
): Promise<Explanation> {
  return delay(buildExplanation(providerId, level), 800);
}
