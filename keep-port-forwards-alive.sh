#!/bin/bash

# Keep Port-Forwards Alive Script
# Monitors and restarts port-forwards if they die

SERVICES=(
    "inquiries-system:streamlit-dashboard:8501:8501"
    "inquiries-system:fastapi:8000:8000"
    "monitoring:prometheus-grafana:3000:80"
    "airflow:airflow-webserver:8080:8080"
    "argocd:argocd-server:30009:443"
)

echo "🔌 Starting port-forward monitoring..."

while true; do
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r namespace svc local_port remote_port <<< "$service"
        
        # Check if port-forward is running
        if ! ps aux | grep -v grep | grep -q "kubectl port-forward -n $namespace svc/$svc $local_port:$remote_port"; then
            echo "⚠️  Port-forward died for $svc, restarting..."
            nohup kubectl port-forward -n $namespace svc/$svc $local_port:$remote_port > /tmp/pf-$svc.log 2>&1 &
            sleep 2
        fi
    done
    
    sleep 10
done

