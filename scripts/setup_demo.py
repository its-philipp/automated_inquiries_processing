#!/usr/bin/env python3
"""
Complete setup script for the inquiry automation demo.
This script sets up all services and data for the demo.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_service_health():
    """Check if all services are running."""
    services = [
        ("Streamlit Dashboard", "http://localhost:8501"),
        ("FastAPI", "http://localhost:8000"),
        ("Airflow", "http://localhost:8081"),
        ("MLflow", "http://localhost:5001"),
        ("Grafana", "http://localhost:3000"),
        ("Prometheus", "http://localhost:9090"),
    ]
    
    print("\n🏥 Checking service health...")
    for name, url in services:
        try:
            import requests
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 302, 401]:  # 401 is OK for login pages
                print(f"✅ {name}: Running")
            else:
                print(f"⚠️  {name}: Responding but status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Not accessible - {e}")

def main():
    """Main setup function."""
    print("🚀 Setting up Inquiry Automation Demo")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("docker-compose.yml").exists():
        print("❌ docker-compose.yml not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Step 1: Start Docker services
    print("\n📦 Starting Docker services...")
    if not run_command("docker-compose up -d", "Starting Docker services"):
        print("❌ Failed to start Docker services")
        sys.exit(1)
    
    # Wait for services to start
    print("\n⏳ Waiting for services to start...")
    time.sleep(30)
    
    # Step 2: Initialize database
    print("\n🗄️  Initializing database...")
    if not run_command("docker exec inquiry_api python scripts/init_db.py", "Initializing database tables"):
        print("⚠️  Database initialization failed, but continuing...")
    
    # Step 3: Generate mock data
    print("\n📊 Generating mock data...")
    if not run_command("docker exec inquiry_api python scripts/load_mock_data.py", "Loading mock data"):
        print("⚠️  Mock data generation failed, but continuing...")
    
    # Step 4: Set up MLflow experiments
    print("\n🧪 Setting up MLflow experiments...")
    if not run_command("source .venv/bin/activate && python scripts/setup_mlflow_simple.py", "Setting up MLflow"):
        print("⚠️  MLflow setup failed, but continuing...")
    
    # Step 5: Set up Grafana dashboards
    print("\n📈 Setting up Grafana dashboards...")
    if not run_command("source .venv/bin/activate && python scripts/setup_grafana.py", "Setting up Grafana"):
        print("⚠️  Grafana setup failed, but continuing...")
    
    # Step 6: Create Airflow admin user
    print("\n👤 Creating Airflow admin user...")
    if not run_command("docker exec inquiry_airflow_webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin", "Creating Airflow admin user"):
        print("⚠️  Airflow user creation failed, but continuing...")
    
    # Step 7: Train a real model (optional)
    print("\n🤖 Training demo model...")
    if not run_command("source .venv/bin/activate && python src/models/real_classifier.py", "Training demo model"):
        print("⚠️  Model training failed, but continuing...")
    
    # Final health check
    time.sleep(10)
    check_service_health()
    
    print("\n🎉 Demo setup complete!")
    print("\n📋 Access your services:")
    print("  🌐 Streamlit Dashboard: http://localhost:8501")
    print("  🔧 FastAPI: http://localhost:8000")
    print("  🔄 Airflow: http://localhost:8081 (admin/admin)")
    print("  🧪 MLflow: http://localhost:5001")
    print("  📊 Grafana: http://localhost:3000 (admin/admin)")
    print("  📈 Prometheus: http://localhost:9090")
    print("\n🎯 Demo features:")
    print("  • View 1000 mock inquiries in Streamlit dashboard")
    print("  • Trigger daily_data_ingestion DAG to generate new mock data")
    print("  • Monitor system metrics in Grafana")
    print("  • Track ML experiments in MLflow")
    print("  • Process inquiries via FastAPI")
    print("\n💡 Pro tip: Trigger the 'daily_data_ingestion' DAG in Airflow to generate new mock data!")

if __name__ == "__main__":
    main()
