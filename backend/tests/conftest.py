from __future__ import annotations

import io
import pytest
from app import create_app
from models.database import Base, engine


SAMPLE_CSV_DATA = """Provider,ClaimID,BeneID,ClaimType,InscClaimAmtReimbursed,DeductibleAmtPaid,ClaimStartDt,ClaimEndDt,AttendingPhysician,OperatingPhysician,OtherPhysician,Age,ChronicConditionCount,NoOfMonths_PartACov,NoOfMonths_PartBCov,ChronicCond_Alzheimer,ChronicCond_Heartfailure,ChronicCond_KidneyDisease,ChronicCond_Cancer,ChronicCond_ObstrPulmonary,ChronicCond_Depression,ChronicCond_Diabetes,ChronicCond_IschemicHeart,ChronicCond_Osteoporasis,ChronicCond_rheumatoidarthritis,ChronicCond_stroke
PRV0001,CLM0001,BENE001,Inpatient,15000,1068,2024-01-01,2024-01-05,PHY001,PHY002,,75,4,12,12,1,1,0,0,1,0,1,0,0,0,0
PRV0001,CLM0002,BENE002,Inpatient,12000,1068,2024-01-10,2024-01-15,PHY001,,,80,5,12,12,1,1,1,0,1,0,1,1,0,0,0
PRV0001,CLM0003,BENE003,Outpatient,8000,500,2024-02-01,2024-02-01,PHY001,,,68,2,12,12,0,1,0,0,0,0,1,0,0,0,0
PRV0002,CLM0004,BENE004,Outpatient,500,50,2024-01-05,2024-01-05,PHY003,,,65,1,12,12,0,0,0,0,0,0,1,0,0,0,0
PRV0002,CLM0005,BENE005,Outpatient,600,60,2024-01-12,2024-01-12,PHY004,,,70,2,12,12,0,0,0,0,0,0,0,1,0,0,0
PRV0003,CLM0006,BENE006,Outpatient,1200,100,2024-01-15,2024-01-15,PHY005,,,72,3,12,12,0,1,0,0,0,1,1,0,0,0,0
PRV0003,CLM0007,BENE007,Inpatient,3500,1068,2024-02-10,2024-02-12,PHY006,PHY007,,78,4,12,12,1,0,1,0,0,0,1,1,0,0,0
PRV0004,CLM0008,BENE008,Outpatient,300,30,2024-01-20,2024-01-20,PHY008,,,62,0,12,12,0,0,0,0,0,0,0,0,0,0,0
PRV0004,CLM0009,BENE009,Outpatient,250,25,2024-02-15,2024-02-15,PHY008,,,64,1,12,12,0,0,0,0,0,0,1,0,0,0,0
PRV0005,CLM0010,BENE010,Inpatient,25000,1068,2024-03-01,2024-03-10,PHY009,PHY010,PHY011,85,6,12,12,1,1,1,1,1,1,1,1,1,1,1
"""


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing."""
    test_app = create_app()
    test_app.config["TESTING"] = True
    yield test_app


@pytest.fixture(scope="session")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="session", autouse=True)
def populate_test_database(client):
    """Seed the database with sample CSV upload before running tests."""
    data = {
        "file": (io.BytesIO(SAMPLE_CSV_DATA.encode("utf-8")), "test_claims.csv")
    }
    resp = client.post(
        "/api/v1/analyze/csv",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
