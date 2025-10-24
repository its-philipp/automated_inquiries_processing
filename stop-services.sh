#!/bin/bash

# 🛑 Stop Automated Inquiries Processing Services
# This script stops all services and cleans up port-forwards

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Automated Inquiries Processing Services${NC}"
echo "=================================================="

# Stop port-forwards
echo -e "${YELLOW}🔌 Stopping port-forwards...${NC}"
pkill -f "kubectl port-forward" || true

# Stop Minikube (optional - uncomment if you want to stop the entire cluster)
# echo -e "${YELLOW}⏹️  Stopping Minikube cluster...${NC}"
# minikube stop

echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo -e "${YELLOW}💡 To restart services later, run:${NC}"
echo "  ./start-services.sh"
echo ""
echo -e "${BLUE}📊 Services are still running in Kubernetes${NC}"
echo "  • To view services: kubectl get pods --all-namespaces"
echo "  • To restart port-forwards: ./start-services.sh"
echo "  • To stop cluster: minikube stop"
