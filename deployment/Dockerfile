FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY model ./model
COPY scripts ./scripts

ENV PYTHONPATH=/app

CMD ["python", "-c", "from scripts.model_predictor import MODEL, FEATURES, THRESHOLD; print('Model loaded successfully'); print('Features:', len(FEATURES)); print('Threshold:', THRESHOLD)"]
