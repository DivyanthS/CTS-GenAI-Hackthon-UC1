import os
from pathlib import Path

from dotenv import load_dotenv

# Backend root directory:
# CTS-2/backend
BASE_DIR = Path(__file__).resolve().parents[1]

# Load .env from the backend root.
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv(
    "APP_NAME",
    "Fraud Detection Analyst Hub Backend",
)

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
)

HOST = os.getenv(
    "HOST",
    "0.0.0.0",
)

PORT = int(
    os.getenv(
        "PORT",
        "8000",
    )
)

# ---------------------------------------------------------
# Database settings (PostgreSQL / SQLite source of truth)
# ---------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'fraud_detection.db'}",
)

# ---------------------------------------------------------
# Risk Engine settings
# ---------------------------------------------------------
RISK_ENGINE = os.getenv(
    "RISK_ENGINE",
    "dummy",  # "dummy" or "real" / "xgboost"
).lower()

RISK_MODEL_VERSION = os.getenv(
    "RISK_MODEL_VERSION",
    "1.0",
)

# Configurable Thresholds
DEFAULT_LOW_THRESHOLD = float(os.getenv("DEFAULT_LOW_THRESHOLD", "0.23"))
DEFAULT_HIGH_THRESHOLD = float(os.getenv("DEFAULT_HIGH_THRESHOLD", "0.60"))
DEFAULT_CRITICAL_THRESHOLD = float(os.getenv("DEFAULT_CRITICAL_THRESHOLD", "0.80"))

# ---------------------------------------------------------
# Storage & Directories
# ---------------------------------------------------------
UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        "data/uploads",
    )
)
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR / UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = Path(
    os.getenv(
        "EXPORT_DIR",
        "data/exports",
    )
)
if not EXPORT_DIR.is_absolute():
    EXPORT_DIR = BASE_DIR / EXPORT_DIR
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_DIR = Path(
    os.getenv(
        "REPORT_DIR",
        "reports",
    )
)
if not REPORT_DIR.is_absolute():
    REPORT_DIR = BASE_DIR / REPORT_DIR
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Kaggle Integration & Automated Retraining
# ---------------------------------------------------------
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")
KAGGLE_DATASET_SLUG = os.getenv("KAGGLE_DATASET_SLUG", "healthcare-provider-fraud-dataset")
KAGGLE_KERNEL_SLUG = os.getenv("KAGGLE_KERNEL_SLUG", "fraud-detection-xgboost-training")

AUTO_RETRAIN_AFTER_TRAINING_EXPORT = (
    os.getenv("AUTO_RETRAIN_AFTER_TRAINING_EXPORT", "false").strip().lower() in ("true", "1", "yes")
)

# ---------------------------------------------------------
# CORS & Security
# ---------------------------------------------------------
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
)

MAX_CONTENT_LENGTH = int(
    os.getenv(
        "MAX_CONTENT_LENGTH",
        100 * 1024 * 1024,  # 100 MB max upload
    )
)

# ---------------------------------------------------------
# ML Model Artifacts
# ---------------------------------------------------------
MODEL_DIR = Path(
    os.getenv(
        "MODEL_DIR",
        "models/fraud_model",
    )
)
if not MODEL_DIR.is_absolute():
    MODEL_DIR = BASE_DIR / MODEL_DIR
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = os.getenv(
    "MODEL_FILE",
    "xgboost_fraud_model.pkl",
)
FEATURES_FILE = os.getenv(
    "FEATURES_FILE",
    "features.json",
)
CONFIG_FILE = os.getenv(
    "CONFIG_FILE",
    "config.json",
)

MODEL_PATH = MODEL_DIR / MODEL_FILE
FEATURES_PATH = MODEL_DIR / FEATURES_FILE
MODEL_CONFIG_PATH = MODEL_DIR / CONFIG_FILE

COMBINED_DATA_FILE = Path(
    os.getenv(
        "COMBINED_DATA_FILE",
        "data/All_Datasets_Combined1.csv",
    )
)
if not COMBINED_DATA_FILE.is_absolute():
    COMBINED_DATA_FILE = BASE_DIR / COMBINED_DATA_FILE
