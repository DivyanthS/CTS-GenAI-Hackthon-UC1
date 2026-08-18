from __future__ import annotations

import io
from typing import Any
import pandas as pd
from utils.dataframe_utils import normalize_dataframe_columns, COLUMN_ALIASES, CHRONIC_COLUMNS


class DatasetService:
    """
    Validates CSV datasets, analyzes schema conformance, and calculates data health scores.
    """

    def validate_csv_bytes(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """
        Perform comprehensive validation checks on an uploaded CSV file.
        """
        if not file_bytes:
            return {
                "valid": False,
                "health_score": 0,
                "rows": 0,
                "columns": 0,
                "providers": 0,
                "beneficiaries": 0,
                "checks": [
                    {
                        "name": "File Empty Check",
                        "status": "FAIL",
                        "message": "Uploaded file is empty (0 bytes).",
                    }
                ],
                "schema": [],
            }

        try:
            # Try utf-8 then latin1
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1", low_memory=False)
        except Exception as exc:
            return {
                "valid": False,
                "health_score": 0,
                "rows": 0,
                "columns": 0,
                "providers": 0,
                "beneficiaries": 0,
                "checks": [
                    {
                        "name": "CSV Parse Check",
                        "status": "FAIL",
                        "message": f"Failed to parse CSV file: {str(exc)}",
                    }
                ],
                "schema": [],
            }

        if df.empty:
            return {
                "valid": False,
                "health_score": 0,
                "rows": 0,
                "columns": len(df.columns),
                "providers": 0,
                "beneficiaries": 0,
                "checks": [
                    {
                        "name": "Dataset Empty Check",
                        "status": "FAIL",
                        "message": "Dataset contains 0 rows.",
                    }
                ],
                "schema": [],
            }

        # Normalize columns
        df_norm = normalize_dataframe_columns(df)

        checks: list[dict[str, str]] = []
        health_penalties = 0

        # Check 1: Provider column
        if "Provider" in df_norm.columns:
            null_providers = df_norm["Provider"].isna().sum()
            if null_providers == 0:
                checks.append({
                    "name": "Provider Identifier",
                    "status": "PASS",
                    "message": f"Provider IDs are present across all {len(df_norm):,} rows.",
                })
            else:
                health_penalties += 15
                checks.append({
                    "name": "Provider Identifier",
                    "status": "WARNING",
                    "message": f"{null_providers:,} rows have missing Provider IDs.",
                })
        else:
            health_penalties += 40
            checks.append({
                "name": "Provider Identifier",
                "status": "FAIL",
                "message": "Missing mandatory 'Provider' column.",
            })

        # Check 2: ClaimID column
        if "ClaimID" in df_norm.columns:
            null_claims = df_norm["ClaimID"].isna().sum()
            dup_claims = df_norm["ClaimID"].duplicated().sum()
            if null_claims == 0 and dup_claims == 0:
                checks.append({
                    "name": "Claim Identifier",
                    "status": "PASS",
                    "message": f"Claim IDs are unique and present ({len(df_norm):,} rows).",
                })
            elif dup_claims > 0:
                health_penalties += 10
                checks.append({
                    "name": "Claim Identifier",
                    "status": "WARNING",
                    "message": f"Found {dup_claims:,} duplicate Claim IDs.",
                })
            else:
                health_penalties += 15
                checks.append({
                    "name": "Claim Identifier",
                    "status": "WARNING",
                    "message": f"{null_claims:,} rows have missing Claim IDs.",
                })
        else:
            health_penalties += 40
            checks.append({
                "name": "Claim Identifier",
                "status": "FAIL",
                "message": "Missing mandatory 'ClaimID' column.",
            })

        # Check 3: Reimbursement Amount
        if "InscClaimAmtReimbursed" in df_norm.columns:
            reimb_s = pd.to_numeric(df_norm["InscClaimAmtReimbursed"], errors="coerce")
            null_reimb = reimb_s.isna().sum()
            if null_reimb == 0:
                checks.append({
                    "name": "Reimbursement Values",
                    "status": "PASS",
                    "message": f"Reimbursement amounts are numeric with 0 nulls (total: ${reimb_s.sum():,.2f}).",
                })
            else:
                health_penalties += 5
                checks.append({
                    "name": "Reimbursement Values",
                    "status": "WARNING",
                    "message": f"{null_reimb:,} reimbursement rows have non-numeric or missing values.",
                })
        else:
            health_penalties += 10
            checks.append({
                "name": "Reimbursement Values",
                "status": "WARNING",
                "message": "Reimbursement column missing; defaulting to $0.00.",
            })

        # Check 4: Beneficiary IDs
        if "BeneID" in df_norm.columns:
            unique_bene = df_norm["BeneID"].nunique()
            checks.append({
                "name": "Beneficiary Data",
                "status": "PASS",
                "message": f"Contains {unique_bene:,} unique beneficiaries.",
            })
        else:
            health_penalties += 5
            checks.append({
                "name": "Beneficiary Data",
                "status": "WARNING",
                "message": "Beneficiary ID column not found; synthetic IDs will be assigned.",
            })

        # Check 5: Claim Types
        if "ClaimType" in df_norm.columns:
            types = df_norm["ClaimType"].dropna().unique().tolist()
            checks.append({
                "name": "Claim Type Distribution",
                "status": "PASS",
                "message": f"Claim types detected: {', '.join(map(str, types))}.",
            })
        else:
            checks.append({
                "name": "Claim Type Distribution",
                "status": "WARNING",
                "message": "ClaimType not specified; defaulting to Outpatient.",
            })

        # Schema inspection
        schema_items: list[dict[str, Any]] = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            is_req = col in ["Provider", "ClaimID"]
            null_count = df[col].isna().sum()
            status = "pass" if null_count == 0 else "warn"
            schema_items.append({
                "field": col,
                "type": dtype_str,
                "required": is_req,
                "status": status,
                "note": f"{null_count} nulls" if null_count > 0 else "Complete",
            })

        health_score = max(0, 100 - health_penalties)
        is_valid = health_penalties < 50 and "Provider" in df_norm.columns and "ClaimID" in df_norm.columns

        unique_providers = int(df_norm["Provider"].nunique()) if "Provider" in df_norm.columns else 0
        unique_bene = int(df_norm["BeneID"].nunique()) if "BeneID" in df_norm.columns else 0

        return {
            "valid": is_valid,
            "health_score": health_score,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "providers": unique_providers,
            "beneficiaries": unique_bene,
            "checks": checks,
            "schema": schema_items,
        }
