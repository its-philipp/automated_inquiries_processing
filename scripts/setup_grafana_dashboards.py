#!/usr/bin/env python3
"""
Script to import Grafana dashboards from JSON files on first startup.
"""
import os
import json
import requests
import time
import sys

def wait_for_grafana(base_url="http://grafana:3000", timeout=60):
    """Wait for Grafana to be ready."""
    print("Waiting for Grafana to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Grafana is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print("❌ Grafana did not become ready within timeout")
    return False

def create_datasource(base_url="http://grafana:3000", username="admin", password="admin"):
    """Create Prometheus datasource if it doesn't exist."""
    print("Setting up Prometheus datasource...")
    
    # Check if datasource already exists
    try:
        response = requests.get(
            f"{base_url}/api/datasources",
            auth=(username, password),
            timeout=10
        )
        if response.status_code == 200:
            datasources = response.json()
            for ds in datasources:
                if ds.get('name') == 'Prometheus':
                    print("✅ Prometheus datasource already exists")
                    return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Error checking datasources: {e}")
    
    # Create Prometheus datasource
    datasource_config = {
        "name": "Prometheus",
        "type": "prometheus",
        "access": "proxy",
        "url": "http://prometheus:9090",
        "isDefault": True,
        "editable": True,
        "jsonData": {
            "timeInterval": "15s",
            "httpMethod": "POST"
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/datasources",
            auth=(username, password),
            json=datasource_config,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Prometheus datasource created successfully")
            return True
        else:
            print(f"⚠️  Failed to create datasource: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating datasource: {e}")
        return False

def import_dashboard(dashboard_file, base_url="http://grafana:3000", username="admin", password="admin"):
    """Import a dashboard from JSON file."""
    print(f"Importing dashboard: {dashboard_file}")
    
    try:
        with open(dashboard_file, 'r') as f:
            dashboard_data = json.load(f)
        
        # Prepare dashboard for import
        dashboard_payload = {
            "dashboard": dashboard_data,
            "overwrite": True,  # Overwrite if dashboard already exists
            "inputs": []  # No inputs needed for our dashboards
        }
        
        response = requests.post(
            f"{base_url}/api/dashboards/import",
            auth=(username, password),
            json=dashboard_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            dashboard_title = dashboard_data.get('title', 'Unknown')
            print(f"✅ Successfully imported dashboard: {dashboard_title}")
            return True
        else:
            print(f"❌ Failed to import dashboard: {response.status_code} - {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in dashboard file: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error importing dashboard: {e}")
        return False

def main():
    """Main function to set up Grafana dashboards."""
    print("🚀 Starting Grafana dashboard setup...")
    
    # Wait for Grafana to be ready
    if not wait_for_grafana():
        print("❌ Grafana setup failed - service not ready")
        sys.exit(1)
    
    # Create datasource
    if not create_datasource():
        print("⚠️  Datasource creation failed, but continuing with dashboard import...")
    
    # Import dashboards
    dashboard_dir = "/app/monitoring/grafana/dashboards"
    dashboard_files = [
        "inquiry-pipeline-overview.json",
        "model-performance.json", 
        "system-health.json"
    ]
    
    success_count = 0
    total_count = len(dashboard_files)
    
    for dashboard_file in dashboard_files:
        dashboard_path = os.path.join(dashboard_dir, dashboard_file)
        if import_dashboard(dashboard_path):
            success_count += 1
    
    print(f"\n📊 Dashboard import summary: {success_count}/{total_count} dashboards imported successfully")
    
    if success_count == total_count:
        print("🎉 All Grafana dashboards imported successfully!")
        print("📈 You can now view the dashboards at: http://localhost:3000")
        print("🔍 Available dashboards:")
        print("  - Inquiry Processing Pipeline Overview")
        print("  - Model Performance Dashboard") 
        print("  - System Health Dashboard")
    else:
        print("⚠️  Some dashboards failed to import. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
