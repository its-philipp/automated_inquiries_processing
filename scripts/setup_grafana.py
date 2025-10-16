#!/usr/bin/env python3
"""
Script to set up Grafana dashboards and data sources.
"""
import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"

def setup_grafana():
    """Set up Grafana with data sources and dashboards."""
    
    # Create session
    session = requests.Session()
    
    # Login to Grafana
    login_data = {
        "user": GRAFANA_USER,
        "password": GRAFANA_PASSWORD
    }
    
    print("🔐 Logging into Grafana...")
    response = session.post(f"{GRAFANA_URL}/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to login to Grafana: {response.status_code}")
        print("Trying to get session cookie...")
        # Try to get session cookie directly
        session.get(f"{GRAFANA_URL}/login")
    
    # Set up Prometheus data source
    print("📊 Setting up Prometheus data source...")
    
    prometheus_datasource = {
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": True,
        "jsonData": {
            "timeInterval": "5s"
        }
    }
    
    try:
        response = session.post(
            f"{GRAFANA_URL}/api/datasources",
            json=prometheus_datasource,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 409]:  # 409 = already exists
            print("✅ Prometheus data source configured")
        else:
            print(f"⚠️  Prometheus data source setup returned: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"⚠️  Error setting up Prometheus: {e}")
    
    # Create inquiry automation dashboard
    print("📈 Creating inquiry automation dashboard...")
    
    dashboard_config = {
        "dashboard": {
            "id": None,
            "title": "Inquiry Automation Pipeline",
            "tags": ["inquiry", "automation", "ml"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Total Inquiries",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "inquiries_received_total",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {"displayMode": "basic"},
                            "mappings": [],
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 1000}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Processing Rate",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "rate(inquiries_processed_total[5m])",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "reqps",
                            "color": {"mode": "palette-classic"},
                            "custom": {"displayMode": "basic"}
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Category Distribution",
                    "type": "piechart",
                    "targets": [
                        {
                            "expr": "category_distribution",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Urgency Distribution",
                    "type": "piechart",
                    "targets": [
                        {
                            "expr": "urgency_distribution",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                },
                {
                    "id": 5,
                    "title": "Processing Duration",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(inquiry_processing_duration_seconds_bucket[5m]))",
                            "refId": "A",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(inquiry_processing_duration_seconds_bucket[5m]))",
                            "refId": "B",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 6,
                    "title": "Routing Decisions by Department",
                    "type": "bargauge",
                    "targets": [
                        {
                            "expr": "routing_decisions_total",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                },
                {
                    "id": 7,
                    "title": "System Health",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "system_health_status",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "custom": {"displayMode": "basic"},
                            "mappings": [
                                {"type": "value", "value": "1", "text": "Healthy"},
                                {"type": "value", "value": "0", "text": "Unhealthy"}
                            ],
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "green", "value": 1}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 16}
                },
                {
                    "id": 8,
                    "title": "Escalation Rate",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "rate(routing_decisions_total{escalated=\"true\"}[5m]) / rate(routing_decisions_total[5m]) * 100",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 5},
                                    {"color": "red", "value": 10}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 16}
                },
                {
                    "id": 9,
                    "title": "Model Inference Rate",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(model_inferences_total[5m])",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                }
            ],
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "refresh": "5s"
        },
        "overwrite": True
    }
    
    try:
        response = session.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=dashboard_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Inquiry automation dashboard created")
        else:
            print(f"⚠️  Dashboard creation returned: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"⚠️  Error creating dashboard: {e}")
    
    # Create system overview dashboard
    print("🖥️  Creating system overview dashboard...")
    
    system_dashboard_config = {
        "dashboard": {
            "id": None,
            "title": "System Overview",
            "tags": ["system", "infrastructure"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Container Status",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "up",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Memory Usage",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes * 100",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                {
                    "id": 3,
                    "title": "CPU Usage",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(container_cpu_usage_seconds_total[5m]) * 100",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Network I/O",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(container_network_receive_bytes_total[5m])",
                            "refId": "A",
                            "legendFormat": "Receive"
                        },
                        {
                            "expr": "rate(container_network_transmit_bytes_total[5m])",
                            "refId": "B",
                            "legendFormat": "Transmit"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                }
            ],
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "refresh": "5s"
        },
        "overwrite": True
    }
    
    try:
        response = session.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=system_dashboard_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ System overview dashboard created")
        else:
            print(f"⚠️  System dashboard creation returned: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"⚠️  Error creating system dashboard: {e}")
    
    print("\n🎉 Grafana setup complete!")
    print("📊 You can now view dashboards at: http://localhost:3000")
    print("🔑 Login credentials: admin / admin")
    print("📈 Available dashboards:")
    print("  - Inquiry Automation Pipeline")
    print("  - System Overview")

if __name__ == "__main__":
    setup_grafana()
