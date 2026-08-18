from __future__ import annotations

import io
import json
import math
import sys
from app import create_app

SAMPLE_CSV = """Provider,ClaimID,BeneID,ClaimType,InscClaimAmtReimbursed,DeductibleAmtPaid,ClaimStartDt,ClaimEndDt,AttendingPhysician,OperatingPhysician,OtherPhysician,Age,ChronicConditionCount,NoOfMonths_PartACov,NoOfMonths_PartBCov,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke
PRV51001,CLM90001,BENE101,Inpatient,18500,1068,2024-01-01,2024-01-08,PHY101,PHY102,,77,4,12,12,1,1,1,0,1,0,1,1,0,0,0
PRV51001,CLM90002,BENE102,Inpatient,22000,1068,2024-01-15,2024-01-22,PHY101,,,82,5,12,12,1,1,1,1,1,0,1,1,0,1,0
PRV51001,CLM90003,BENE103,Inpatient,14200,1068,2024-02-01,2024-02-06,PHY101,,,69,3,12,12,0,1,1,0,0,0,1,0,0,0,0
PRV51002,CLM90004,BENE104,Outpatient,450,50,2024-01-05,2024-01-05,PHY103,,,64,1,12,12,0,0,0,0,0,0,1,0,0,0,0
PRV51002,CLM90005,BENE105,Outpatient,520,60,2024-01-12,2024-01-12,PHY104,,,68,2,12,12,0,0,0,0,0,0,0,1,0,0,0
PRV51003,CLM90006,BENE106,Outpatient,1400,120,2024-01-15,2024-01-15,PHY105,,,71,2,12,12,0,1,0,0,0,1,1,0,0,0,0
PRV51003,CLM90007,BENE107,Inpatient,4200,1068,2024-02-10,2024-02-14,PHY106,PHY107,,79,4,12,12,1,0,1,0,0,0,1,1,0,0,0
PRV51004,CLM90008,BENE108,Outpatient,280,30,2024-01-20,2024-01-20,PHY108,,,61,0,12,12,0,0,0,0,0,0,0,0,0,0,0
PRV51004,CLM90009,BENE109,Outpatient,310,25,2024-02-15,2024-02-15,PHY108,,,63,1,12,12,0,0,0,0,0,0,1,0,0,0,0
PRV51005,CLM90010,BENE110,Inpatient,32000,1068,2024-03-01,2024-03-12,PHY109,PHY110,PHY111,88,7,12,12,1,1,1,1,1,1,1,1,1,1,1
"""


def assert_no_nan_inf(data, path=""):
    """Check that JSON structure has no NaN or Infinity."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert_no_nan_inf(v, f"{path}.{k}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            assert_no_nan_inf(item, f"{path}[{i}]")
    elif isinstance(data, float):
        assert math.isfinite(data), f"Non-finite float at {path}: {data}"


def main():
    print("--- 1. Initializing Flask App & Checking Health ---")
    app = create_app()
    client = app.test_client()

    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.data}"
    health_data = health_resp.get_json()
    print("Health Status:", health_data)
    assert health_data["status"] == "ok"
    assert health_data["database"] == "connected"
    assert health_data["risk_engine"] == "dummy"

    print("\n--- 2. Validating Dataset via POST /api/v1/validate ---")
    val_resp = client.post(
        "/api/v1/validate",
        data={"file": (io.BytesIO(SAMPLE_CSV.encode("utf-8")), "claims.csv")},
        content_type="multipart/form-data",
    )
    assert val_resp.status_code == 200
    val_data = val_resp.get_json()
    assert_no_nan_inf(val_data)
    print(f"Validation Health Score: {val_data['health_score']}/100, Valid: {val_data['valid']}")

    print("\n--- 3. Uploading CSV via POST /api/v1/analyze/csv ---")
    upload_resp = client.post(
        "/api/v1/analyze/csv",
        data={"file": (io.BytesIO(SAMPLE_CSV.encode("utf-8")), "claims.csv")},
        content_type="multipart/form-data",
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.get_json()
    assert_no_nan_inf(upload_data)
    run_id = upload_data["run_id"]
    print(f"Upload Complete! Run ID: {run_id}")
    print("Risk Summary:", upload_data["risk_summary"])
    print("Top Risky Providers Count:", len(upload_data["top_risky_providers"]))

    print("\n--- 4. Calling GET /api/v1/analytics ---")
    analytics_resp = client.get("/api/v1/analytics")
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.get_json()
    assert_no_nan_inf(analytics_data)
    print("Analytics Summary:", analytics_data)

    print("\n--- 5. Calling GET /api/v1/analytics/charts ---")
    charts_resp = client.get("/api/v1/analytics/charts")
    assert charts_resp.status_code == 200
    charts_data = charts_resp.get_json()
    assert_no_nan_inf(charts_data)
    print("Risk Distribution Chart:", charts_data["risk_distribution"])
    print("Reimbursement by Risk Chart:", charts_data["reimbursement_by_risk"])

    print("\n--- 6. Calling GET /api/v1/providers ---")
    providers_resp = client.get("/api/v1/providers?page=1&page_size=10")
    assert providers_resp.status_code == 200
    providers_data = providers_resp.get_json()
    assert_no_nan_inf(providers_data)
    print(f"Total Providers: {providers_data['total']}, Returned: {len(providers_data['providers'])}")

    top_prov_id = providers_data["providers"][0]["provider_id"]
    print(f"\n--- 7. Calling GET /api/v1/providers/{top_prov_id} ---")
    single_prov_resp = client.get(f"/api/v1/providers/{top_prov_id}")
    assert single_prov_resp.status_code == 200
    single_prov_data = single_prov_resp.get_json()
    assert_no_nan_inf(single_prov_data)
    print(f"Provider: {single_prov_data['provider']['provider_name']}, Risk: {single_prov_data['risk']}")
    print(f"Risk Factors Count: {len(single_prov_data['risk_factors'])}")

    print("\n--- 8. Calling GET /api/v1/claims ---")
    claims_resp = client.get("/api/v1/claims?page=1&page_size=5")
    assert claims_resp.status_code == 200
    claims_data = claims_resp.get_json()
    assert_no_nan_inf(claims_data)
    print(f"Total Claims: {claims_data['total']}, Returned: {len(claims_data['claims'])}")

    sample_claim_id = claims_data["claims"][0]["claim_id"]
    print(f"\n--- 9. Calling GET /api/v1/claims/{sample_claim_id}/explanation ---")
    expl_resp = client.get(f"/api/v1/claims/{sample_claim_id}/explanation")
    assert expl_resp.status_code == 200
    expl_data = expl_resp.get_json()
    assert_no_nan_inf(expl_data)
    print(f"Claim Explanation Summary: {expl_data['summary']}")
    print(f"Factors: {len(expl_data['factors'])}, Review Focus: {expl_data['review_focus']}")

    print("\n--- 10. Calling POST /api/v1/predict ---")
    pred_resp = client.post(
        "/api/v1/predict",
        json={"provider_id": top_prov_id},
    )
    assert pred_resp.status_code == 200
    pred_data = pred_resp.get_json()
    assert_no_nan_inf(pred_data)
    print(f"Single Prediction for {top_prov_id}: Score={pred_data['risk_score']}, Level={pred_data['risk_level']}, Decision={pred_data['decision']}")

    print(f"\n--- 11. Calling GET /api/v1/reports/{run_id}/json ---")
    rep_json_resp = client.get(f"/api/v1/reports/{run_id}/json")
    assert rep_json_resp.status_code == 200
    rep_json_data = rep_json_resp.get_json()
    assert_no_nan_inf(rep_json_data)
    print("Report Executive Summary:", rep_json_data["executive_summary"])

    print(f"\n--- 12. Calling GET /api/v1/reports/{run_id}/pdf ---")
    rep_pdf_resp = client.get(f"/api/v1/reports/{run_id}/pdf")
    assert rep_pdf_resp.status_code == 200
    assert rep_pdf_resp.content_type == "application/pdf"
    print(f"PDF Generated Successfully! Size: {len(rep_pdf_resp.data):,} bytes")

    print("\n========================================================")
    print("ALL 15 ACCEPTANCE FLOW VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("========================================================")


if __name__ == "__main__":
    main()
