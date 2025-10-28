FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
# First install non-PyTorch packages
RUN pip install --no-cache-dir \
    fastapi==0.120.1 \
    uvicorn==0.38.0 \
    sqlalchemy==2.0.44 \
    psycopg2-binary==2.9.11 \
    redis==7.0.1 \
    prometheus-client==0.23.1 \
    pydantic==2.12.3 \
    pydantic[email] \
    scikit-learn==1.7.2 \
    beautifulsoup4==4.13.1 \
    mlflow==2.19.0 \
    pyyaml==6.0.3
# Then install CPU-only PyTorch from specialized index
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.9.0
# Finally install transformers (which depends on torch)
RUN pip install --no-cache-dir transformers==4.57.1

# Copy application code
COPY src/ /app/src/
COPY inquiry_monitoring_dashboard.py /app/
COPY k8s/database/init-database-simple.py /app/k8s/database/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

