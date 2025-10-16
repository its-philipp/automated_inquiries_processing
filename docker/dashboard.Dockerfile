FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    streamlit==1.28.0 \
    plotly==5.18.0 \
    pandas==2.1.0 \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.0

# Copy application files
COPY inquiry_monitoring_dashboard.py ./
COPY src ./src

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "inquiry_monitoring_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

