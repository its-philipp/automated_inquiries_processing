FROM python:3.10-slim

WORKDIR /mlflow

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install MLflow and dependencies
RUN pip install --no-cache-dir \
    mlflow==2.8.0 \
    psycopg2-binary==2.9.9 \
    boto3==1.29.0

# Create artifact directory
RUN mkdir -p /mlflow/artifacts

# Expose port
EXPOSE 5000

# Run MLflow server
CMD ["mlflow", "server", \
     "--backend-store-uri", "postgresql://postgres:postgres@postgres:5432/mlflow", \
     "--default-artifact-root", "/mlflow/artifacts", \
     "--host", "0.0.0.0", \
     "--port", "5000"]

