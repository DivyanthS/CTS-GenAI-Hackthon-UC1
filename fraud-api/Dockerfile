# ── Healthcare Fraud-Risk Detection API ─────────────────────────────────────
# Single-stage Python 3.11 slim image.
# Compatible with Hugging Face Spaces (port 7860) and generic Docker hosts.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Keeps Python from generating .pyc files and disables stdout buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps required by XGBoost / shap
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-caching optimisation)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and model artefacts
COPY . .

# Default environment
ENV ACTIVE_MODEL_VERSION=v1 \
    FRAUD_THRESHOLD=0.23 \
    RISK_LOW_MAX=0.23 \
    RISK_MEDIUM_MAX=0.60 \
    MAX_UPLOAD_MB=50 \
    PORT=7860 \
    FLASK_DEBUG=0 \
    CORS_ORIGINS=*

EXPOSE 7860

# Use gunicorn for production; PORT env var allows override
CMD gunicorn \
        --bind "0.0.0.0:${PORT:-7860}" \
        --workers 2 \
        --timeout 120 \
        --log-level info \
        app:app
