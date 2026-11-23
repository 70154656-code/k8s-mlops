FROM python:3.11-slim

ARG MLFLOW_VERSION=2.17.2

ENV PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=15 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --retries 15 --timeout 600 \
    "mlflow==${MLFLOW_VERSION}" \
    "sqlalchemy==2.0.36" \
    alembic \
    flask \
    gunicorn \
    scikit-learn==1.5.2 \
    joblib

RUN useradd -m -u 10001 mlflow && \
    mkdir -p /mlflow/data/artifacts && \
    chown -R 10001:10001 /mlflow

USER 10001:10001
WORKDIR /mlflow
