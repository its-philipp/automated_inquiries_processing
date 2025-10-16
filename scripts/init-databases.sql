-- Initialize additional databases for Airflow and MLflow
-- This script runs automatically when PostgreSQL container starts

-- Create airflow database for Apache Airflow
CREATE DATABASE airflow;

-- Create mlflow database for MLflow tracking
CREATE DATABASE mlflow;

-- Grant permissions to postgres user for both databases
GRANT ALL PRIVILEGES ON DATABASE airflow TO postgres;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO postgres;
