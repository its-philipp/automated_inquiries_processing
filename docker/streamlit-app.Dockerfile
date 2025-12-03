FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    streamlit==1.45.1 \
    pandas==2.3.0 \
    plotly==6.1.2 \
    sqlalchemy==2.0.44 \
    psycopg2-binary==2.9.11

# Copy application code
COPY inquiry_monitoring_dashboard.py /app/

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "inquiry_monitoring_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
