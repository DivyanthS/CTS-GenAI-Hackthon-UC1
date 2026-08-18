# Healthcare Fraud-Risk Detection REST API

A Flask REST API for predicting healthcare provider fraud risk using a validated XGBoost classifier and SHAP explainability.

---

## Overview & Architecture

This service faithfully deploys the validated XGBoost ML model developed in Kaggle notebook `cts-fraud-detection-eda (1).ipynb`.

### Key Pipeline Stages
```
RAW Claims CSV (117 cols)
   ↓
Validation & Preprocessing
   ↓
Provider-Level Aggregation (117 → 30 features)
   ↓
XGBoost Probability Prediction
   ↓
Risk Classification (Threshold = 0.23)
   ↓
SHAP Feature Attribution & Natural-Language Explanation
   ↓
JSON Response
```

> **IMPORTANT**: Fraud predictions are made at the **Provider level**. Individual claims are aggregated to provider features. No claim is individually labeled as fraudulent.

---

## Model Performance (Locked Benchmark)

- **Model Type**: XGBoost Classifier (`XGBClassifier`)
- **Classification Threshold**: `0.23` (selected via OOF predictions with recall constraint ≥ 0.80)
- **ROC-AUC**: `0.9575`
- **PR-AUC**: `0.7509`
- **Accuracy**: `0.9002`
- **Precision**: `0.4804`
- **Recall**: `0.8515`
- **F1 Score**: `0.6143`
- **Confusion Matrix**: `[[888, 93], [15, 86]]`

---

## API Reference

### 1. `POST /predict`
Upload raw claims CSV to generate provider-level fraud risk predictions.

- **Content-Type**: `multipart/form-data`
- **Body**: `file` (CSV file containing raw claims)

#### Response Example
```json
{
  "status": "success",
  "model_version": "v1",
  "threshold": 0.23,
  "n_providers": 2,
  "providers": [
    {
      "provider_id": "PRV55912",
      "fraud_probability": 0.871234,
      "risk_level": "HIGH",
      "decision": "FLAGGED",
      "explanation": "Provider PRV55912 received a fraud probability of 0.87 (87.1%) and was classified as HIGH RISK. The strongest factors increasing the fraud risk were total reimbursement amount and claims per patient ratio. These were partially offset by average patient age, which are consistent with legitimate provider behaviour. This provider should be prioritised for immediate further investigation.",
      "top_factors": [
        {
          "feature": "TotalReimbursement",
          "value": 158670,
          "shap_value": 0.9273,
          "direction": "increases_risk"
        },
        {
          "feature": "ClaimsPerBeneficiary",
          "value": 3.45,
          "shap_value": 0.412,
          "direction": "increases_risk"
        },
        {
          "feature": "AveragePatientAge",
          "value": 74.2,
          "shap_value": -0.1839,
          "direction": "decreases_risk"
        }
      ]
    }
  ]
}
```

### 2. `GET /health`
Liveness probe returning system status, loaded model version, and thresholds.

### 3. `GET /model-info`
Returns active model version, 30-feature schema, locked threshold, and validated performance metrics.

---

## Risk Banding Configuration

Risk levels are used for triage and prioritization:

| Risk Level | Decision | Probability Range |
|---|---|---|
| **LOW** | `NOT_FLAGGED` | `probability < 0.23` |
| **MEDIUM** | `FLAGGED_FOR_REVIEW` | `0.23 <= probability < 0.60` |
| **HIGH** | `FLAGGED` | `probability >= 0.60` |

*The classification decision uses the locked binary threshold `0.23` (`probability >= 0.23`). Risk band boundaries can be configured via environment variables (`RISK_LOW_MAX`, `RISK_MEDIUM_MAX`).*

---

## Project Structure

```
fraud-api/
├── app.py                      # Flask REST API entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
├── Dockerfile                  # Container definition
├── .dockerignore
├── .env.example                # Environment variables template
├── models/
│   └── v1/
│       ├── model.joblib        # Trained XGBoost model artifact
│       ├── feature_schema.json # 30 feature names in exact training order
│       └── config.json         # Model threshold and metadata
├── src/
│   ├── preprocessing.py        # Raw CSV validation & clean-up
│   ├── feature_engineering.py  # Provider-level feature aggregation (117 → 30)
│   ├── predictor.py            # Model inference engine & version loader
│   ├── explainer.py            # SHAP TreeExplainer & natural-language generation
│   ├── risk.py                 # Risk level banding & decision logic
│   └── validation.py           # HTTP input validation & error formatting
├── tests/
│   ├── test_features.py        # Unit tests for 30 engineered features
│   ├── test_prediction.py      # Model compatibility & threshold tests
│   └── test_api.py             # Integration tests for API endpoints
└── data/
    └── sample.csv              # Sample claims dataset for testing
```

---

## Local Setup & Running

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run API server
python app.py
```

Server binds to `http://0.0.0.0:7860`.

### Testing
```bash
pytest tests/ -v
```

---

## Docker Deployment

Build and run with Docker:

```bash
docker build -t fraud-api .
docker run -p 7860:7860 fraud-api
```

This application is ready for deployment to **Hugging Face Spaces**, AWS ECS, GCP Cloud Run, or any container platform.
