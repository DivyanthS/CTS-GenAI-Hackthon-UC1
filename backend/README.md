# Healthcare Fraud Detection Analyst Hub — Backend

Production-ready Flask backend for healthcare claims fraud detection and payment integrity analysis. 

The backend supports full end-to-end dataset ingestion via CSV upload, statistical benchmark anomaly risk scoring (Low, Medium, High, Critical), database persistence with SQLAlchemy ORM, explainable evidence generation, Recharts-ready analytics, and multi-format report generation (JSON and PDF).

---

## 1. Key Features

- **Decoupled Risk Engine**: Standardized `RiskEngine` interface allowing seamless swapping between the built-in dataset-grounded `DummyRiskEngine` and a real ML model (`RealModelRiskEngine` / XGBoost / External REST ML service) without modifying routes or data pipelines.
- **SQLAlchemy ORM**: Full persistence for `AnalysisRun`, `Provider`, `Claim`, `RiskAssessment`, and `RiskFactor` entities using SQLite by default (configurable to PostgreSQL/MySQL).
- **Dataset-Grounded Risk Scoring**: Dummy engine calculates dynamic statistical benchmarks (mean, median, standard deviation, IQR, and percentiles) and assigns weighted component scores across 7 dimensions (claims volume, total reimbursement, average reimbursement, claims per beneficiary, inpatient concentration, physician concentration patterns, and deductible behavior).
- **Explainable Evidence**: Generates automated, human-readable evidence summaries for High and Critical providers comparing individual provider values with dataset peer benchmarks.
- **Multi-Format Reports**: Generates full 13-section management reports in structured JSON format and downloadable formatted PDF reports using ReportLab.
- **Data Validation & Quality Scoring**: Dedicated `/api/v1/validate` endpoint for checking CSV health, schema conformance, and identifying missingness or anomalies before ingestion.
- **Full Frontend API Compatibility**: Backward-compatible responses for the React/TanStack frontend (`analyst-hub`).

---

## 2. Architecture & Directory Structure

```text
backend/
├── app.py                      # Flask application factory, CORS, and blueprint registration
├── config/
│   ├── __init__.py
│   └── settings.py             # App, database, engine, and directory settings
├── models/
│   ├── __init__.py
│   ├── database.py             # SQLAlchemy engine, SessionLocal, Base, init_db
│   ├── analysis_run.py         # AnalysisRun ORM model
│   ├── provider.py             # Provider ORM model (28+ statistics and risk fields)
│   ├── claim.py                # Claim ORM model (claim fields + raw_data JSON)
│   ├── risk_assessment.py      # RiskAssessment ORM model
│   └── risk_factor.py          # RiskFactor ORM model
├── schemas/
│   ├── __init__.py
│   ├── upload.py               # Upload & Validation Pydantic schemas
│   ├── prediction.py           # Prediction & Risk factor schemas
│   ├── provider.py             # Provider list and detail schemas
│   ├── claim.py                # Claim list and detail schemas
│   ├── analytics.py            # Analytics summary and chart schemas
│   └── report.py               # Report summary schemas
├── services/
│   ├── __init__.py
│   ├── upload_service.py       # Ingestion, feature extraction, scoring & ORM bulk persistence
│   ├── dataset_service.py      # CSV validation & data quality health scoring
│   ├── provider_data.py        # Database-backed provider queries and details
│   ├── claim_data.py           # Database-backed claim queries and pagination
│   ├── analytics_service.py    # Analytics aggregations and graph datasets
│   ├── report_service.py       # 13-section JSON and ReportLab PDF report generator
│   ├── feature_engineering/
│   │   ├── __init__.py
│   │   └── provider_features.py# 30-feature provider engineering matrix
│   ├── evidence/
│   │   ├── __init__.py
│   │   └── claim_evidence_service.py # Dataset-grounded claim explanation context
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract RiskEngine interface
│   │   ├── dummy_risk_engine.py# Statistical benchmark dummy risk engine
│   │   ├── real_model_engine.py# XGBoost / Real model adapter
│   │   └── risk_classifier.py  # Risk tier classification & priority mapping
│   └── prediction/
│       ├── __init__.py
│       ├── prediction_service.py # Provider prediction coordinator
│       └── model_adapter.py    # Canonical model output normalizer
├── utils/
│   ├── __init__.py
│   ├── json_utils.py           # Recursive NaN/Inf/numpy/date JSON serializer
│   ├── dataframe_utils.py      # Column alias normalization and defaults
│   └── risk_utils.py           # Deterministic provider name & run ID generator
├── tests/                      # Pytest unit and integration test suite
├── data/
│   └── uploads/                # Ingested CSV file storage
├── reports/                    # Generated report cache
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── pytest.ini                  # Pytest configuration
```

---

## 3. Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.12 and 3.13)

### Installation Steps

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

---

## 4. Environment Configuration

The backend is configured via `.env`:

```env
APP_NAME=Fraud Detection Analyst Hub Backend
APP_ENV=development

HOST=0.0.0.0
PORT=8000

# Database URL (SQLite by default, or postgresql://user:pass@localhost/dbname)
DATABASE_URL=sqlite:///fraud_detection.db

# Risk Engine Selection: "dummy" (default) or "real"
RISK_ENGINE=dummy
RISK_MODEL_VERSION=1.0

# Storage Directories
UPLOAD_DIR=data/uploads
REPORT_DIR=reports

# Allowed CORS Origins
FRONTEND_URL=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# Upload Limit (100 MB in bytes)
MAX_CONTENT_LENGTH=104857600
```

---

## 5. Running the Backend

### Start Server
```bash
python app.py
```
The server will start at `http://127.0.0.1:8000`.

### Running Tests
Execute the comprehensive test suite with pytest:
```bash
pytest
```
Or with verbose output:
```bash
pytest -v
```

---

## 6. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server, database, and risk engine health status |
| `POST` | `/api/v1/validate` | Validate CSV quality, schema, and health score |
| `POST` | `/api/v1/analyze/csv` | Ingest CSV dataset, compute features, score, and persist |
| `POST` | `/api/v1/analyze` | Alias for CSV analysis |
| `GET` | `/api/v1/runs` | List all historical analysis runs |
| `GET` | `/api/v1/runs/{run_id}` | Retrieve metadata for a specific analysis run |
| `POST` | `/api/v1/predict` | Predict risk for a single provider |
| `GET` | `/api/v1/providers` | Paginated list of providers (with risk filters & sorting) |
| `GET` | `/api/v1/providers/{provider_id}` | Complete provider profile, risk factors, and stats |
| `GET` | `/api/v1/claims` | Paginated list of claims (with provider & type filters) |
| `GET` | `/api/v1/claims/{claim_id}` | Retrieve a single claim record |
| `GET` | `/api/v1/claims/{claim_id}/explanation` | Dataset-grounded claim explanation and context |
| `GET` | `/api/v1/analytics` | Overall portfolio metrics, totals, and fraud rates |
| `GET` | `/api/v1/analytics/charts` | Recharts-compatible graph datasets |
| `GET` | `/api/v1/reports/{run_id}/json` | Full 13-section analytical report in JSON |
| `GET` | `/api/v1/reports/{run_id}/pdf` | Multi-page downloadable PDF report |

---

## 7. Dummy Risk Engine Methodology

The `DummyRiskEngine` is fully grounded in the uploaded dataset:

1. **Feature Engineering**: Derives provider-level aggregates from claims:
   - `TotalClaims`, `UniqueBeneficiaries`, `TotalReimbursement`, `AverageReimbursement`, `MaxReimbursement`, `StdReimbursement`, `ClaimsPerBeneficiary`, `InpatientShare`, `UniqueAttendingPhysicians`, etc.
2. **Benchmark Derivation**: Calculates dataset-wide mean, median, standard deviation, IQR, and percentiles across all providers.
3. **Percentile Normalization**: Evaluates 7 distinct anomaly dimensions on a 0–100 percentile scale:
   - `claim_volume_score`
   - `reimbursement_score`
   - `average_reimbursement_score`
   - `claims_per_beneficiary_score`
   - `inpatient_score`
   - `physician_pattern_score`
   - `deductible_score`
4. **Weighted Composite Scoring**:
   $$\text{Risk Score} = 0.20 \times \text{Volume} + 0.25 \times \text{Reimbursement} + 0.15 \times \text{AvgReimbursement} + 0.15 \times \text{ClaimsPerBene} + 0.10 \times \text{Inpatient} + 0.10 \times \text{Physician} + 0.05 \times \text{Deductible}$$
5. **Deterministic Adjustment**: Applies a deterministic Provider ID hash modifier ($\pm 3.0$) to avoid artificial identical ties while remaining 100% reproducible.
6. **Risk Classification & Decision Hierarchy**:
   - `80.0 – 100.0`: **Critical** $\rightarrow$ `URGENT_REVIEW` (Priority: P1)
   - `60.0 – 79.9`: **High** $\rightarrow$ `REVIEW` (Priority: P2)
   - `30.0 – 59.9`: **Medium** $\rightarrow$ `MONITOR` (Priority: P3)
   - `0.0 – 29.9`: **Low** $\rightarrow$ `NORMAL` (Priority: P4)

---

## 8. Replacing the Dummy Engine with a Real Model

To integrate a real ML model (e.g. trained XGBoost, LightGBM, or an external microservice):

1. **Implement `RiskEngine`** in `services/risk/`:
   ```python
   from services.risk.base import RiskEngine

   class MyRealRiskEngine(RiskEngine):
       @property
       def engine_type(self) -> str:
           return "production_model"

       @property
       def version(self) -> str:
           return "2.0"

       def predict_provider(self, features: dict, benchmarks: dict | None = None) -> dict:
           # Call ML model / API
           ...

       def predict_batch(self, provider_features_df, dataset_claims_df=None):
           # Run batch model inference
           ...
   ```
2. **Switch the engine in `.env`**:
   ```env
   RISK_ENGINE=real
   ```
3. The rest of the backend (routes, upload ingestion, ORM persistence, analytics, charts, and report generation) will work without any further changes.
