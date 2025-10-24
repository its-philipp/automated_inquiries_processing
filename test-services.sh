#!/bin/bash

echo "🚀 Testing Kubernetes Services Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test service
test_service() {
    local service_name=$1
    local namespace=$2
    local port=$3
    local description=$4
    
    echo -e "\n${BLUE}Testing $description...${NC}"
    
    # Start port-forward in background
    kubectl port-forward -n $namespace svc/$service_name $port:$port > /dev/null 2>&1 &
    local pf_pid=$!
    
    # Wait for port-forward to start
    sleep 3
    
    # Test the service
    if curl -s -f http://localhost:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $description is working!${NC}"
        echo -e "   Access: http://localhost:$port"
    else
        echo -e "${RED}❌ $description is not responding${NC}"
    fi
    
    # Kill port-forward
    kill $pf_pid 2>/dev/null
    wait $pf_pid 2>/dev/null
}

# Test Python App
test_service "python-app" "inquiries-system" "8000" "Python Application"

# Test Grafana
test_service "prometheus-grafana" "monitoring" "80" "Grafana Dashboard"

# Test Prometheus
test_service "prometheus-kube-prometheus-prometheus" "monitoring" "9090" "Prometheus Server"

# Test AlertManager
test_service "prometheus-kube-prometheus-alertmanager" "monitoring" "9093" "AlertManager"

echo -e "\n${YELLOW}📊 Service Status Summary:${NC}"
kubectl get pods --all-namespaces | grep -E "(Running|Error|CrashLoopBackOff)"

echo -e "\n${YELLOW}🌐 All NodePort Services:${NC}"
kubectl get svc --all-namespaces | grep NodePort

echo -e "\n${GREEN}🎉 Testing Complete!${NC}"
echo -e "To access services manually, use:"
echo -e "kubectl port-forward -n <namespace> svc/<service-name> <local-port>:<service-port>"
