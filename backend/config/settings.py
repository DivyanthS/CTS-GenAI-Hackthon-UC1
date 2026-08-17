import os
from pathlib import Path

from dotenv import load_dotenv


# Backend root directory:
# CTS-GenAI-Hackthon-UC1/backend
BASE_DIR = Path(__file__).resolve().parents[1]

# Load .env from the backend root.
load_dotenv(BASE_DIR / ".env")


APP_NAME = os.getenv(
    "APP_NAME",
    "CTS GenAI Hackathon UC1 Backend",
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
# Model artifacts
# ---------------------------------------------------------

MODEL_DIR = Path(
    os.getenv(
        "MODEL_DIR",
        "models/fraud_model",
    )
)

if not MODEL_DIR.is_absolute():
    MODEL_DIR = BASE_DIR / MODEL_DIR


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


# ---------------------------------------------------------
# Data
# ---------------------------------------------------------

COMBINED_DATA_FILE = Path(
    os.getenv(
        "COMBINED_DATA_FILE",
        "data/All_Datasets_Combined1.csv",
    )
)

if not COMBINED_DATA_FILE.is_absolute():
    COMBINED_DATA_FILE = BASE_DIR / COMBINED_DATA_FILE
