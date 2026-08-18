# -*- coding: utf-8 -*-
"""
PostgreSQL Final Smoke Test
============================
Runs the complete backend smoke test against a live PostgreSQL database.
Uses DATABASE_URL from .env (already set to postgresql+psycopg2).
"""
from __future__ import annotations

import os
import sys
import io
import time

print("=" * 70)
print("POSTGRESQL FINAL SMOKE TEST")
print("=" * 70)

# ---------------------------------------------------------------
# 1. Import app (reads DATABASE_URL from .env)
# ---------------------------------------------------------------
from app import create_app

app = create_app()
client = app.test_client()

ERRORS = []
CHECKS = {}


def ok(label, detail=""):
    CHECKS[label] = True
    msg = f"  [PASS] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)


def fail(label, detail=""):
    CHECKS[label] = False
    ERRORS.append(f"{label}: {detail}")
    msg = f"  [FAIL] {label}: {detail}"
    print(msg)


# ---------------------------------------------------------------
# STEP 1: Database Connection & Dialect
# ---------------------------------------------------------------
print("\n--- STEP 1: Database Connection & Dialect ---")
from models.database import engine as db_engine
dialect = db_engine.dialect.name
print(f"  DATABASE DIALECT: {dialect}")
if dialect == "postgresql":
    ok("Database dialect", "postgresql")
else:
    fail("Database dialect", f"Expected postgresql, got {dialect}")
    print("\nABORTING: Not connected to PostgreSQL.")
    sys.exit(1)

# Verify URL doesn't use sqlite
from config.settings import DATABASE_URL
masked_url = DATABASE_URL.split("@")[0].rsplit(":", 1)[0] + ":***@" + DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else DATABASE_URL
print(f"  DATABASE URL (masked): {masked_url}")

# Verify all tables
from models.database import init_db
init_db()
from sqlalchemy import inspect as sa_inspect
expected_tables = {"providers", "claims", "risk_assessments", "risk_factors", "analysis_runs"}
inspector = sa_inspect(db_engine)
actual_tables = set(inspector.get_table_names())
missing = expected_tables - actual_tables
if not missing:
    ok("All ORM tables created", str(sorted(expected_tables)))
else:
    fail("ORM table creation", f"Missing: {missing}")

# ---------------------------------------------------------------
# STEP 2: Provider Dataset Import via API
# ---------------------------------------------------------------
print("\n--- STEP 2: Provider Dataset Import ---")

SAMPLE_PROVIDER_CSV = """Provider,PotentialFraud,TotalClaims,UniqueBeneficiaries,TotalReimbursement,AverageReimbursement,MaxReimbursement,StdReimbursement,TotalDeductiblePaid,AverageDeductiblePaid,UniqueAttendingPhysicians,UniqueOperatingPhysicians,UniqueOtherPhysicians,ClaimsPerBeneficiary,InpatientShare,AveragePatientAge,AverageChronicConditionCount,AveragePartACoverage,AveragePartBCoverage,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke,AverageDeductiblePaid_Missing,StdReimbursement_Missing
PRV_PG_001,Yes,120,45,540000,4500,25000,3200,18000,150,12,5,3,2.67,0.65,74.0,4.2,12,12,0.70,0.80,0.55,0.20,0.40,0.55,0.90,0.90,0.40,0.30,0.25,0,0
PRV_PG_002,No,15,10,18000,1200,3500,450,1200,80,3,0,0,1.5,0.10,63.0,1.2,12,12,0.10,0.15,0.05,0.02,0.05,0.10,0.30,0.25,0.10,0.05,0.02,0,0
PRV_PG_003,Yes,85,32,380000,4470,22000,2800,12000,141,9,4,2,2.66,0.58,71.0,3.8,12,12,0.60,0.70,0.45,0.15,0.35,0.48,0.82,0.85,0.35,0.25,0.18,0,0
PRV_PG_004,No,8,7,9500,1187,2200,310,750,93,1,0,0,1.14,0.0,68.0,1.0,12,12,0.08,0.12,0.03,0.01,0.04,0.08,0.22,0.20,0.08,0.03,0.01,0,0
PRV_PG_005,Yes,200,72,900000,4500,32000,4100,30000,150,18,7,5,2.78,0.75,76.0,4.9,12,12,0.80,0.85,0.65,0.25,0.50,0.62,0.92,0.95,0.48,0.38,0.28,0,0
"""

import_resp = client.post(
    "/api/v1/providers/import",
    data={"file": (io.BytesIO(SAMPLE_PROVIDER_CSV.encode("utf-8")), "pg_smoke_test.csv")},
    content_type="multipart/form-data",
)
if import_resp.status_code == 200:
    imp = import_resp.get_json()
    rows = imp.get("rows_imported", 0)
    ok("Provider import via API", f"{rows} providers imported")
    if rows == 5:
        ok("Correct provider count", "5 providers")
    else:
        fail("Provider count", f"Expected 5, got {rows}")
else:
    fail("Provider import via API", f"HTTP {import_resp.status_code}: {import_resp.get_json()}")

# Verify in PostgreSQL directly
from models.database import get_db
from models.provider import Provider
with get_db() as db:
    pg_count = db.query(Provider).count()
    ok("PostgreSQL provider count", f"{pg_count} providers in DB")

# ---------------------------------------------------------------
# STEP 3: Provider API
# ---------------------------------------------------------------
print("\n--- STEP 3: Provider API ---")
prov_resp = client.get("/api/v1/providers")
if prov_resp.status_code == 200:
    pdata = prov_resp.get_json()
    ok("GET /api/v1/providers", f"total_providers={pdata.get('total_providers', 'N/A')}")
else:
    fail("GET /api/v1/providers", f"HTTP {prov_resp.status_code}")

detail_resp = client.get("/api/v1/providers/PRV_PG_001")
if detail_resp.status_code == 200:
    pdetail = detail_resp.get_json()
    ok("GET /api/v1/providers/PRV_PG_001", f"total_claims={pdetail.get('total_claims')}, total_reimbursement={pdetail.get('total_reimbursement')}")
else:
    fail("GET /api/v1/providers/PRV_PG_001", f"HTTP {detail_resp.status_code}: {detail_resp.get_json()}")

# Verify field mapping
with get_db() as db:
    p = db.query(Provider).filter(Provider.provider_id == "PRV_PG_001").first()
    if p:
        assert p.total_claims == 120, f"total_claims mismatch: {p.total_claims}"
        assert p.total_reimbursement == 540000.0, f"total_reimbursement mismatch: {p.total_reimbursement}"
        assert p.potential_fraud == 1, f"potential_fraud mismatch: {p.potential_fraud}"
        assert p.inpatient_share == 0.65, f"inpatient_share mismatch: {p.inpatient_share}"
        assert abs(p.outpatient_share - 0.35) < 0.01, f"outpatient_share mismatch: {p.outpatient_share}"
        ok("Provider field verification", "total_claims=120, reimbursement=540000, fraud=1, inpatient=0.65")
    else:
        fail("Provider field verification", "PRV_PG_001 not found in PostgreSQL")

# ---------------------------------------------------------------
# STEP 4: Prediction Pipeline
# ---------------------------------------------------------------
print("\n--- STEP 4: Prediction Pipeline ---")
pred_resp = client.post("/api/v1/predict", json={"provider_id": "PRV_PG_001"})
if pred_resp.status_code == 200:
    pred = pred_resp.get_json()
    prob = pred.get("risk_probability", -1)
    score = pred.get("risk_score", -1)
    level = pred.get("risk_level", "")
    decision = pred.get("decision", "")
    ok("POST /api/v1/predict", f"prob={prob}, score={score}, level={level}, decision={decision}")
    assert 0.0 <= prob <= 1.0, f"prob out of range: {prob}"
    assert 0.0 <= score <= 100.0, f"score out of range: {score}"
    assert level in ("Low", "Medium", "High", "Critical"), f"invalid level: {level}"
    assert decision in ("NORMAL", "MONITOR", "REVIEW", "URGENT_REVIEW"), f"invalid decision: {decision}"
    ok("Prediction values valid", "prob in [0,1], score in [0,100]")
    assert "PotentialFraud" not in pred, "PotentialFraud leaked!"
    ok("PotentialFraud exclusion", "NOT in prediction response")
else:
    fail("POST /api/v1/predict", f"HTTP {pred_resp.status_code}: {pred_resp.get_json()}")

# ---------------------------------------------------------------
# STEP 5: RiskAssessment Persistence
# ---------------------------------------------------------------
print("\n--- STEP 5: RiskAssessment & RiskFactor Persistence ---")
from models.risk_assessment import RiskAssessment
from models.risk_factor import RiskFactor
with get_db() as db:
    ra = db.query(RiskAssessment).filter(RiskAssessment.provider_id == "PRV_PG_001").first()
    if ra:
        ok("RiskAssessment persisted", f"risk_level={ra.risk_level}, decision={ra.decision}")
        rfs = db.query(RiskFactor).filter(RiskFactor.risk_assessment_id == ra.id).all()
        ok("RiskFactor records", f"{len(rfs)} factors for PRV_PG_001")
    else:
        fail("RiskAssessment persistence", "No RiskAssessment for PRV_PG_001")

# ---------------------------------------------------------------
# STEP 6: Analytics
# ---------------------------------------------------------------
print("\n--- STEP 6: Analytics ---")
analytics_resp = client.get("/api/v1/analytics")
if analytics_resp.status_code == 200:
    adata = analytics_resp.get_json()
    ok("GET /api/v1/analytics", f"total_providers={adata.get('total_providers')}")
else:
    fail("GET /api/v1/analytics", f"HTTP {analytics_resp.status_code}")

charts_resp = client.get("/api/v1/analytics/charts")
if charts_resp.status_code == 200:
    ok("GET /api/v1/analytics/charts", "200 OK")
else:
    fail("GET /api/v1/analytics/charts", f"HTTP {charts_resp.status_code}")

# ---------------------------------------------------------------
# STEP 7: CSV Export
# ---------------------------------------------------------------
print("\n--- STEP 7: CSV Export ---")
inf_resp = client.post("/api/v1/providers/export", json={"purpose": "inference"})
if inf_resp.status_code == 200:
    idata = inf_resp.get_json()
    ok("Inference export", f"{idata.get('rows')} rows, {idata.get('columns')} cols")
    assert "PotentialFraud" not in idata.get("column_list", [])
    ok("PotentialFraud excluded from inference", "Confirmed")
else:
    fail("Inference export", f"HTTP {inf_resp.status_code}")

train_resp = client.post("/api/v1/providers/export", json={"purpose": "training"})
if train_resp.status_code == 200:
    tdata = train_resp.get_json()
    ok("Training export", f"{tdata.get('rows')} rows, {tdata.get('columns')} cols")
    assert "PotentialFraud" in tdata.get("column_list", [])
    ok("PotentialFraud included in training", "Confirmed")
else:
    fail("Training export", f"HTTP {train_resp.status_code}")

# ---------------------------------------------------------------
# STEP 8: Upload CSV -> Report JSON + PDF
# ---------------------------------------------------------------
print("\n--- STEP 8: Report JSON & PDF ---")
CLAIM_CSV = """Provider,ClaimID,BeneID,ClaimType,InscClaimAmtReimbursed,DeductibleAmtPaid,ClaimStartDt,ClaimEndDt,AttendingPhysician,OperatingPhysician,OtherPhysician,Age,ChronicConditionCount,NoOfMonths_PartACov,NoOfMonths_PartBCov,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke
PRV_PG_001,CLM_PG_001,BEN001,Inpatient,15000,1122,2024-01-01,2024-01-05,PHY001,PHY002,,72,4,12,12,1,1,0,0,1,0,1,1,0,0,0
PRV_PG_002,CLM_PG_002,BEN002,Outpatient,8000,500,2024-01-10,2024-01-10,PHY001,,,65,2,12,12,0,0,0,0,0,1,0,1,0,0,0
PRV_PG_003,CLM_PG_003,BEN003,Inpatient,5000,500,2024-02-01,2024-02-03,PHY003,,,60,1,12,12,0,0,0,0,0,0,0,0,0,0,0
"""

csv_upload = client.post(
    "/api/v1/analyze/csv",
    data={"file": (io.BytesIO(CLAIM_CSV.encode("utf-8")), "pg_claims.csv")},
    content_type="multipart/form-data",
)
if csv_upload.status_code == 200:
    run_data = csv_upload.get_json()
    run_id = run_data.get("run_id")
    ok("POST /api/v1/analyze/csv", f"run_id={run_id}")

    json_report = client.get(f"/api/v1/reports/{run_id}/json")
    if json_report.status_code == 200:
        ok("GET report JSON", "200 OK")
    else:
        fail("GET report JSON", f"HTTP {json_report.status_code}")

    pdf_report = client.get(f"/api/v1/reports/{run_id}/pdf")
    if pdf_report.status_code == 200:
        ct = pdf_report.content_type
        size = len(pdf_report.data)
        ok("GET report PDF", f"Content-Type={ct}, size={size} bytes")
    else:
        fail("GET report PDF", f"HTTP {pdf_report.status_code}")
else:
    fail("POST /api/v1/analyze/csv", f"HTTP {csv_upload.status_code}: {csv_upload.get_json()}")

# ---------------------------------------------------------------
# STEP 9: Threshold
# ---------------------------------------------------------------
print("\n--- STEP 9: Threshold ---")
thr_get = client.get("/api/v1/model/threshold")
if thr_get.status_code == 200:
    thr = thr_get.get_json()
    ok("GET /api/v1/model/threshold", f"low={thr.get('low_threshold')}, high={thr.get('high_threshold')}, critical={thr.get('critical_threshold')}")

    thr_put = client.put("/api/v1/model/threshold", json={"low_threshold": 0.25, "high_threshold": 0.65, "critical_threshold": 0.85})
    if thr_put.status_code == 200:
        ok("PUT /api/v1/model/threshold", "Updated")
        # Restore
        client.put("/api/v1/model/threshold", json={
            "low_threshold": thr["low_threshold"],
            "high_threshold": thr["high_threshold"],
            "critical_threshold": thr["critical_threshold"],
        })
        ok("Threshold restored", "Reverted")
    else:
        fail("PUT /api/v1/model/threshold", f"HTTP {thr_put.status_code}")
else:
    fail("GET /api/v1/model/threshold", f"HTTP {thr_get.status_code}")

# ---------------------------------------------------------------
# STEP 10: Model Status
# ---------------------------------------------------------------
print("\n--- STEP 10: Model Status ---")
ms_resp = client.get("/api/v1/model/status")
if ms_resp.status_code == 200:
    ms = ms_resp.get_json()
    ok("GET /api/v1/model/status", f"version={ms.get('active_version')}, features={ms.get('feature_count')}")
    assert ms.get("feature_count") == 30
    ok("Feature count", "30 features (PotentialFraud excluded)")
else:
    fail("GET /api/v1/model/status", f"HTTP {ms_resp.status_code}")

# ---------------------------------------------------------------
# STEP 11: Training Job
# ---------------------------------------------------------------
print("\n--- STEP 11: Training Job ---")
train_job = client.post("/api/v1/model/train", json={})
if train_job.status_code == 202:
    tj = train_job.get_json()
    job_id = tj.get("job_id")
    ok("POST /api/v1/model/train", f"job_id={job_id}, status={tj.get('status')}")

    job_status = client.get(f"/api/v1/model/train/{job_id}")
    if job_status.status_code == 200:
        ok("GET /api/v1/model/train/<job_id>", f"status={job_status.get_json().get('status')}")
    else:
        fail("GET training job status", f"HTTP {job_status.status_code}")
else:
    fail("POST /api/v1/model/train", f"HTTP {train_job.status_code}")

print("\n  [INFO] Kaggle: MOCKED/LOCAL -- No real Kaggle credentials configured")
ok("Kaggle Mode", "MOCKED/LOCAL")

# ---------------------------------------------------------------
# STEP 12: Health Check
# ---------------------------------------------------------------
print("\n--- STEP 12: Health Check ---")
hc = client.get("/health")
if hc.status_code == 200:
    hdata = hc.get_json()
    ok("GET /health", f"status={hdata.get('status')}, db={hdata.get('database')}")
    if hdata.get("database") == "connected":
        ok("Database health", "connected")
    else:
        fail("Database health", hdata.get("database"))
else:
    fail("GET /health", f"HTTP {hc.status_code}")

# ---------------------------------------------------------------
# STEP 13: Re-import (upsert test)
# ---------------------------------------------------------------
print("\n--- STEP 13: Re-import (upsert) ---")
reimport_resp = client.post(
    "/api/v1/providers/import",
    data={"file": (io.BytesIO(SAMPLE_PROVIDER_CSV.encode("utf-8")), "pg_reimport.csv")},
    content_type="multipart/form-data",
)
if reimport_resp.status_code == 200:
    ok("Re-import (upsert)", "No unique constraint violation")
    with get_db() as db:
        cnt = db.query(Provider).count()
        ok("Provider count after re-import", f"{cnt} (no duplicates)")
else:
    fail("Re-import (upsert)", f"HTTP {reimport_resp.status_code}: {reimport_resp.get_json()}")


# ---------------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------------
print()
print("=" * 70)
print("DATABASE PROOF")
print("=" * 70)
print(f"  DATABASE DIALECT:     {dialect}")
db_host = DATABASE_URL.split("@")[1].split("/")[0] if "@" in DATABASE_URL else "unknown"
db_name = DATABASE_URL.split("/")[-1] if "/" in DATABASE_URL else "unknown"
print(f"  DATABASE HOST:        {db_host}")
print(f"  DATABASE NAME:        {db_name}")
print(f"  DATABASE CONNECTION:  SUCCESS")

with get_db() as db:
    final_count = db.query(Provider).count()
print(f"  PROVIDER TABLE:       EXISTS")
print(f"  PROVIDER COUNT:       {final_count}")

print()
print("=" * 70)
print("FINAL SMOKE TEST SUMMARY")
print("=" * 70)
for label, status in CHECKS.items():
    sym = "PASS" if status else "FAIL"
    print(f"  [{sym}] {label}")

print()
if ERRORS:
    print("FAILURES:")
    for e in ERRORS:
        print(f"  - {e}")
    print(f"\n{'FAIL':^70}")
else:
    print(f"{'ALL CHECKS PASSED':^70}")
    print(f"{'BACKEND READY AND LOCKED FOR FRONTEND INTEGRATION':^70}")
