# Risk Sentinel

Build TOP DESIGN LEVEL  production-quality React + TypeScript web application for an enterprise

Claims Payment Integrity and Fraud Risk Detection Platform.

PROJECT NAME:

FraudGuard AI

PURPOSE:

This platform helps insurance/payment-integrity investigators identify potentially

suspicious healthcare claims and providers, understand why the ML model assigned

a high-risk score, compare providers against peers, and prioritize cases for

investigation.

IMPORTANT:

This is an AI-assisted risk detection system.

It must NOT claim that fraud has been proven.

The ML model produces a risk score/prediction.

An explainable LLM provides a human-readable explanation based ONLY on

model-derived evidence.

A human investigator makes the final decision.

==================================================

TECHNOLOGY

==================================================

Use:

- React

- Vite

- TypeScript

- Tailwind CSS

- shadcn/ui

- React Router

- Axios

- Recharts

- Lucide React

Use clean, reusable components.

Do NOT put the entire application inside App.tsx.

Use a proper folder structure:

src/

  components/

    layout/

    dashboard/

    claims/

    providers/

    investigation/

    explanation/

    data/

    common/

  pages/

    Login.tsx

    Dashboard.tsx

    ImportData.tsx

    DataQuality.tsx

    FraudAnalysis.tsx

    Claims.tsx

    ClaimDetails.tsx

    Providers.tsx

    ProviderDetails.tsx

    InvestigationQueue.tsx

    InvestigationCase.tsx

    Analytics.tsx

    Settings.tsx

  data/

    mockDashboard.ts

    mockClaims.ts

    mockProviders.ts

    mockInvestigations.ts

    mockExplanations.ts

  services/

    api.ts

    mockApi.ts

  types/

    index.ts

==================================================

DESIGN DIRECTION

==================================================

Create a modern enterprise fintech/healthcare analytics interface.

Visual style:

- Professional

- Clean

- Premium

- Trustworthy

- Data-heavy but not cluttered

- Suitable for an insurance payment-integrity analyst

- Desktop-first but responsive

- Dark navy/charcoal sidebar

- Light main workspace

- Use red/orange only for risk indicators

- Use green for successful validation/resolution

- Use blue/neutral colors for normal information

Do NOT make it look like a generic AI chatbot.

This is an enterprise investigation platform.

==================================================

GLOBAL LAYOUT

==================================================

After login, use:

LEFT SIDEBAR

------------------------------------------------

FraudGuard AI

Claims Payment Integrity

Overview

  Dashboard

Data

  Import Data

  Data Quality

Risk Intelligence

  Fraud Analysis

  Claims

  Providers

Investigation

  Investigation Queue

Analytics

  Analytics

System

  Settings

BOTTOM:

User profile

Analyst

------------------------------------------------

TOP NAVBAR

Page title

Breadcrumb

Search

Notifications

User profile

==================================================

PAGE 1 — LOGIN

==================================================

Create a professional login screen.

Logo:

Shield icon

Product:

FraudGuard AI

Subtitle:

Claims Payment Integrity

Fields:

Email

Password

Button:

Sign In

Also include:

Forgot password?

After login navigate to Dashboard.

For now authentication can be mocked.

==================================================

PAGE 2 — DASHBOARD

==================================================

Title:

Claims Payment Integrity Dashboard

Subtitle:

Monitor suspicious claims, provider behavior and investigation workload.

Top KPI cards:

Total Claims

558,211

Providers

5,410

Beneficiaries

138,556

High Risk Cases

Use mock value

Do not permanently hard-code production metrics.

These numbers are prototype values based on the current dataset.

Create charts:

1. Risk Distribution

- Critical

- High

- Medium

- Low

2. Claim Type Distribution

- Inpatient

- Outpatient

3. Top Risky Providers

Columns:

Provider

Risk Score

Claims

Reimbursement

4. Reimbursement by Risk Level

5. Recent Investigation Cases

Create realistic mock data.

==================================================

PAGE 3 — IMPORT DATA

==================================================

Title:

Import Claims Data

Subtitle:

Upload a CSV or JSON dataset for validation and risk analysis.

Large drag-and-drop upload area.

Support:

CSV

JSON

Show:

Drag & Drop your file here

OR

Browse Files

After upload show:

File name

File size

Upload status

Rows

Columns

Example:

All_Datasets_Combined.csv

Rows:

558,211

Columns:

117

Providers:

5,410

Beneficiaries:

138,556

Button:

Validate Dataset

For now implement frontend-only mock upload behavior.

DO NOT implement real backend processing yet.

==================================================

PAGE 4 — DATA QUALITY

==================================================

Title:

Data Quality

Show an overall dataset health indicator.

Create validation cards:

✓ File format

✓ Required fields

✓ Claim IDs

✓ Provider IDs

✓ Beneficiary IDs

✓ Duplicate Claim IDs

✓ Data types

✓ Missing values

Create a schema table:

Field

Type

Required

Status

Examples:

ClaimID

Provider

BeneID

ClaimType

InscClaimAmtReimbursed

PotentialFraud

Do not fake validation results as real backend results.

Use clearly defined mock values for the prototype.

==================================================

PAGE 5 — FRAUD ANALYSIS

==================================================

Title:

Fraud Risk Analysis

Show selected dataset.

Dataset:

All_Datasets_Combined.csv

Claims:

558,211

Providers:

5,410

Create:

RUN ANALYSIS

When clicked, show an analysis progress state:

Dataset loaded

Features prepared

Provider patterns calculated

ML model executed

Risk scores generated

Evidence generated

LLM explanations generated

Then show:

Analysis Complete

Create realistic mock results.

==================================================

PAGE 6 — INVESTIGATION QUEUE

==================================================

This is one of the most important pages.

Title:

Investigation Queue

Subtitle:

Prioritize potentially suspicious cases for investigator review.

Show:

Total Cases

Critical

High

Medium

Under Review

Create filter bar:

Search Claim ID / Provider

Risk:

All

Critical

High

Medium

Low

Claim Type:

All

Inpatient

Outpatient

Status:

All

New

Under Review

Escalated

Resolved

Create a professional table:

Claim ID

Provider

Claim Type

Risk Score

Risk Level

Reimbursement

Status

Action

Example:

CLM001

PRV55912

Inpatient

96%

Critical

$26,000

New

View

Clicking a case should navigate to Claim Details.

==================================================

PAGE 7 — CLAIM DETAILS

==================================================

Title:

Claim Details

Example:

Claim:

CLM001

Risk Score:

96%

Risk Level:

CRITICAL

Prediction:

Potential Fraud

IMPORTANT:

Use language such as "Potential Fraud" or "High Risk".

Do NOT say "Confirmed Fraud".

Claim information:

Claim ID

Provider

Beneficiary

Claim Type

Claim Start Date

Claim End Date

Reimbursement

Attending Physician

Diagnosis information

Create a risk score visualization.

==================================================

MODEL EVIDENCE

==================================================

Create a section:

Model Evidence

Show top risk factors.

Example:

Provider Claim Volume

Provider:

1,284 claims

Peer Average:

642 claims

Difference:

+100%

Another:

Average Reimbursement

Provider:

$9,650

Peer Average:

$5,210

Another:

Claim Reimbursement

Current Claim:

$26,000

Make evidence visually clear.

==================================================

EXPLAINABLE LLM SECTION

==================================================

Create a premium card titled:

WHY WAS THIS CLAIM FLAGGED?

Use an AI icon.

Subtitle:

AI-generated explanation based on model-derived evidence.

Example:

"This claim received a high-risk score because the provider's billing

patterns differ substantially from comparable providers. The provider

has significantly higher claim volume and reimbursement levels than

the peer group."

Below it show:

Key Factors

1. Provider claim volume

2. Average reimbursement

3. Claim reimbursement

Each factor should have:

Factor

Provider value

Peer value

Difference

Short explanation

IMPORTANT:

The LLM explanation must NEVER invent evidence.

The UI should display:

"Explanation generated from model-derived evidence"

Add a disclaimer:

"Risk assessment is not a determination of fraud. This explanation

summarizes model-derived signals and supporting evidence for investigator

review."

==================================================

PAGE 8 — PROVIDERS

==================================================

Title:

Provider Risk Intelligence

Create a searchable provider table.

Columns:

Provider ID

Risk Score

Risk Level

Claims

Beneficiaries

Total Reimbursement

Status

Filters:

Risk level

Claim volume

Claim type

Click provider → Provider Details.

==================================================

PAGE 9 — PROVIDER DETAILS

==================================================

Title:

Provider Profile

Example:

Provider:

PRV55912

Risk:

96%

Risk Level:

Critical

KPI cards:

Claims

1,284

Beneficiaries

846

Total Reimbursement

$12.4M

Average Reimbursement

$9,650

Create charts:

Claim volume over time

Reimbursement

Inpatient vs Outpatient

Risk factors

==================================================

PROVIDER VS PEER COMPARISON

==================================================

Create a strong comparison section:

Metric | Provider | Peer Average | Difference

Claim Volume

1,284

642

+100%

Average Reimbursement

$9,650

$5,210

+85%

Total Reimbursement

$12.4M

$4.8M

+158%

Create visual comparison bars.

Then:

AI Interpretation

Show a mock LLM explanation based on these metrics.

==================================================

PAGE 10 — INVESTIGATION CASE

==================================================

Create an investigation workflow.

Case ID:

INV-001

Claim:

CLM001

Provider:

PRV55912

Risk:

96%

Status:

New

Actions:

Start Investigation

Escalate

Resolve

Allow changing status in the frontend mock state.

Create an investigation timeline:

Case Created

Risk Detected

Reviewed

Escalated

Resolved

==================================================

PAGE 11 — ANALYTICS

==================================================

Create an analytics dashboard.

Charts:

Risk distribution

Fraud-risk providers

Inpatient vs outpatient

Reimbursement by risk

Top risk factors

Provider peer deviations

Use Recharts.

==================================================

PAGE 12 — SETTINGS

==================================================

Create a simple settings page.

Sections:

Profile

Notifications

Application Preferences

No complicated functionality needed.

==================================================

DATA MODEL

==================================================

Create TypeScript interfaces.

RiskResult:

claim_id

provider_id

risk_score

risk_level

prediction

top_risk_factors

evidence

explanation

Evidence:

factor

provider_value

peer_value

difference

unit

Explanation:

summary

reasons

disclaimer

Claim:

claim_id

provider_id

bene_id

claim_type

reimbursement

claim_start_date

claim_end_date

risk_score

risk_level

status

Provider:

provider_id

risk_score

risk_level

claim_count

beneficiary_count

total_reimbursement

average_reimbursement

Investigation:

case_id

claim_id

provider_id

risk_score

priority

status

created_at

assigned_to

==================================================

MOCK API ARCHITECTURE

==================================================

For now DO NOT depend on a real backend.

Create:

services/mockApi.ts

Create mock functions:

uploadDataset()

validateDataset()

runAnalysis()

getDashboardSummary()

getClaims()

getClaim()

getProviders()

getProvider()

getInvestigations()

getExplanation()

Later these will be replaced with Axios API calls.

Create:

services/api.ts

Prepare Axios configuration with:

baseURL:

http://localhost:5000/api

Do not call the real backend yet.

==================================================

FUTURE BACKEND API CONTRACT

==================================================

Prepare the frontend architecture for:

POST /api/data/upload

POST /api/data/validate

POST /api/fraud/analyze

GET /api/dashboard/summary

GET /api/claims

GET /api/claims/{claim_id}

GET /api/providers

GET /api/providers/{provider_id}

POST /api/explanation

GET /api/investigations

POST /api/investigations

PUT /api/investigations/{id}

==================================================

IMPORTANT ML + LLM ARCHITECTURE

==================================================

The frontend should represent this workflow:

CSV/JSON

    ↓

Data Processing

    ↓

ML Model

    ↓

Risk Score

    ↓

Top Model Factors

    ↓

Supporting Evidence

    ↓

Explainable LLM

    ↓

Human-readable Explanation

    ↓

Investigator

The LLM is NOT the fraud detector.

The ML model generates the risk signal.

The LLM explains the model-derived evidence.

The investigator makes the final decision.

==================================================

CURRENT DATASET CONTEXT

==================================================

The current team dataset contains:

558,211 combined claim rows

117 columns

5,410 unique providers

138,556 unique beneficiaries

40,474 inpatient claims

517,737 outpatient claims

Important fields include:

BeneID

ClaimID

Provider

ClaimStartDt

ClaimEndDt

InscClaimAmtReimbursed

AttendingPhysician

OperatingPhysician

OtherPhysician

Claim diagnosis fields

Claim procedure fields

ClaimType

PotentialFraud

The current modeling dataset has provider-level PotentialFraud labels.

The UI should therefore carefully distinguish:

Provider Risk

from

Claim Risk

Do not represent a provider-level fraud label as proof that an individual

claim is fraudulent.

==================================================

UX REQUIREMENTS

==================================================

Every major page needs:

Loading state

Empty state

Error state

Success state

Tables need:

Pagination

Search

Sorting

Filtering

Use reusable:

RiskBadge

StatusBadge

StatCard

DataTable

EvidenceCard

ExplanationCard

PeerComparison

LoadingState

EmptyState

ErrorState

Use consistent spacing and typography.

Use tooltips where useful.

Make the UI responsive.

Use accessible buttons and form controls.

==================================================

FINAL USER JOURNEY

==================================================

Login

 ↓

Dashboard

 ↓

Import CSV/JSON

 ↓

Validate Dataset

 ↓

Run Fraud Risk Analysis

 ↓

View Risk Results

 ↓

Investigation Queue

 ↓

Open Claim

 ↓

View Risk Score

 ↓

View Model Evidence

 ↓

View Peer Comparison

 ↓

Read Explainable LLM Reasoning

 ↓

Start Investigation

 ↓

Escalate / Resolve

==================================================

IMPORTANT IMPLEMENTATION RULES

==================================================

1. Build the frontend only.

2. Use mock data for now.

3. Do not build Flask.

4. Do not build ML training.

5. Do not build the LLM backend.

6. Do not pretend the mock values are live predictions.

7. Keep API integration ready for later.

8. Use reusable React components.

9. Use TypeScript types.

10. Make the UI look like a real enterprise payment-integrity product.

11. Prioritize the investigation workflow over decorative UI.

12. Do not call anything "confirmed fraud".

13. Clearly distinguish model risk from confirmed fraud.

14. Clearly label LLM content as AI-generated explanation.

15. Ground the explanation UI around evidence supplied by the ML/backend layer.

Start by creating the complete frontend shell, routing, sidebar, login,

dashboard, import page, data quality page, fraud analysis page,

investigation queue, claim details, providers, provider details,

analytics and settings.

Use realistic mock data throughout.


