from __future__ import annotations

import io
import pytest
from services.provider_import_service import ProviderImportService

SAMPLE_PROVIDER_CSV = """Provider,PotentialFraud,TotalClaims,UniqueBeneficiaries,TotalReimbursement,AverageReimbursement,MaxReimbursement,StdReimbursement,TotalDeductiblePaid,AverageDeductiblePaid,UniqueAttendingPhysicians,UniqueOperatingPhysicians,UniqueOtherPhysicians,ClaimsPerBeneficiary,InpatientShare,AveragePatientAge,AverageChronicConditionCount,AveragePartACoverage,AveragePartBCoverage,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke,AverageDeductiblePaid_Missing,StdReimbursement_Missing
PRV70001,Yes,50,20,150000,3000,12000,1500,5000,100,5,2,1,2.5,0.4,72.5,3.2,12,12,0.5,0.6,0.3,0.1,0.2,0.4,0.7,0.8,0.3,0.2,0.1,0,0
PRV70002,No,10,8,12000,1200,3000,400,600,60,2,0,0,1.25,0.0,65.0,1.1,12,12,0.1,0.2,0.0,0.0,0.0,0.1,0.3,0.2,0.1,0.0,0.0,0,0
PRV70003,1,120,45,450000,3750,25000,2800,15000,125,12,4,3,2.67,0.6,76.0,4.1,12,12,0.7,0.8,0.5,0.2,0.4,0.5,0.9,0.9,0.4,0.3,0.2,0,0
"""


def test_provider_import_service():
    service = ProviderImportService()
    result = service.import_dataset(
        file_input=SAMPLE_PROVIDER_CSV.encode("utf-8"),
        filename="test_provider_data.csv",
    )

    assert result["status"] == "success"
    assert result["rows_imported"] == 3
    assert result["providers_count"] == 3
    assert result["potential_fraud_distribution"]["flagged_1"] == 2
    assert result["potential_fraud_distribution"]["not_flagged_0"] == 1


def test_provider_import_endpoint(client):
    data = {
        "file": (io.BytesIO(SAMPLE_PROVIDER_CSV.encode("utf-8")), "api_providers.csv"),
    }
    response = client.post(
        "/api/v1/providers/import",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    res = response.get_json()
    assert res["status"] == "success"
    assert res["rows_imported"] == 3


def test_provider_import_empty_file(client):
    data = {
        "file": (io.BytesIO(b""), "empty.csv"),
    }
    response = client.post(
        "/api/v1/providers/import",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    res = response.get_json()
    assert res["error"] == "IMPORT_VALIDATION_ERROR"
