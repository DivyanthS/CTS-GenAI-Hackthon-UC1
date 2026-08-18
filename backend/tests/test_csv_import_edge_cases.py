from __future__ import annotations

import io
import pytest
from services.provider_import_service import ProviderImportService


def test_import_missing_required_column():
    svc = ProviderImportService()
    # Missing 'InpatientShare' column
    bad_csv = """Provider,PotentialFraud,TotalClaims,UniqueBeneficiaries,TotalReimbursement,AverageReimbursement,MaxReimbursement,StdReimbursement,TotalDeductiblePaid,AverageDeductiblePaid,UniqueAttendingPhysicians,UniqueOperatingPhysicians,UniqueOtherPhysicians,ClaimsPerBeneficiary,AveragePatientAge,AverageChronicConditionCount,AveragePartACoverage,AveragePartBCoverage,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke,AverageDeductiblePaid_Missing,StdReimbursement_Missing
PRV1,Yes,10,5,5000,500,1000,100,500,50,2,1,0,2.0,70,2,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0
"""
    with pytest.raises(ValueError) as exc_info:
        svc.import_dataset(bad_csv.encode("utf-8"))
    assert "InpatientShare" in str(exc_info.value)


def test_import_various_potential_fraud_formats():
    svc = ProviderImportService()
    csv_data = """Provider,PotentialFraud,TotalClaims,UniqueBeneficiaries,TotalReimbursement,AverageReimbursement,MaxReimbursement,StdReimbursement,TotalDeductiblePaid,AverageDeductiblePaid,UniqueAttendingPhysicians,UniqueOperatingPhysicians,UniqueOtherPhysicians,ClaimsPerBeneficiary,InpatientShare,AveragePatientAge,AverageChronicConditionCount,AveragePartACoverage,AveragePartBCoverage,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke,AverageDeductiblePaid_Missing,StdReimbursement_Missing
PRV_YES_1,Yes,10,5,5000,500,1000,100,500,50,2,1,0,2.0,0.5,70,2,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0
PRV_YES_2,1,10,5,5000,500,1000,100,500,50,2,1,0,2.0,0.5,70,2,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0
PRV_NO_1,No,10,5,5000,500,1000,100,500,50,2,1,0,2.0,0.5,70,2,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0
PRV_NO_2,0,10,5,5000,500,1000,100,500,50,2,1,0,2.0,0.5,70,2,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0
"""
    result = svc.import_dataset(csv_data.encode("utf-8"), filename="fraud_formats.csv")
    assert result["rows_imported"] == 4
    assert result["potential_fraud_distribution"]["flagged_1"] == 2
    assert result["potential_fraud_distribution"]["not_flagged_0"] == 2


def test_import_with_missing_indicators_derivation():
    svc = ProviderImportService()
    # Missing AverageDeductiblePaid_Missing and StdReimbursement_Missing columns in CSV
    csv_data = """Provider,PotentialFraud,TotalClaims,UniqueBeneficiaries,TotalReimbursement,AverageReimbursement,MaxReimbursement,StdReimbursement,TotalDeductiblePaid,AverageDeductiblePaid,UniqueAttendingPhysicians,UniqueOperatingPhysicians,UniqueOtherPhysicians,ClaimsPerBeneficiary,InpatientShare,AveragePatientAge,AverageChronicConditionCount,AveragePartACoverage,AveragePartBCoverage,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke
PRV_MISS_1,0,10,5,5000,500,1000,,500,,2,1,0,2.0,0.5,70,2,12,12,0,0,0,0,0,0,0,0,0,0,0
"""
    result = svc.import_dataset(csv_data.encode("utf-8"), filename="missing_auto.csv")
    assert result["status"] == "success"
    assert result["rows_imported"] == 1
