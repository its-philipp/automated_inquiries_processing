FROM apache/airflow:2.7.3-python3.11

USER airflow

# Install ML and NLP dependencies with CPU-only PyTorch (much smaller!)
# First install PyTorch CPU-only from the specialized index
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.1.0
# Then install other packages from PyPI
RUN pip install --no-cache-dir \
    transformers==4.35.0 \
    sentencepiece==0.1.99 \
    psycopg2-binary==2.9.9 \
    faker==20.0.0

# Pre-download models to avoid runtime delays
# This will take a few minutes but speeds up first DAG run
RUN python -c "from transformers import pipeline; print('Downloading zero-shot model...'); pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"
RUN python -c "from transformers import pipeline; print('Downloading sentiment model...'); pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')"

USER airflow

