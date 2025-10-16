FROM apache/airflow:2.7.0-python3.10

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy and install requirements
COPY pyproject.toml /tmp/

# Install Python dependencies
RUN pip install --no-cache-dir \
    transformers==4.35.0 \
    torch==2.1.0 \
    sentencepiece==0.1.99 \
    scikit-learn==1.3.0 \
    pandas==2.1.0 \
    pyyaml==6.0.1 \
    beautifulsoup4==4.12.0 \
    lxml==4.9.3 \
    faker==19.6.2

# Set working directory
WORKDIR /opt/airflow

# Initialize Airflow database will be done in docker-compose command

