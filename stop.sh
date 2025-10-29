#!/bin/bash

# 🛑 Stop Complete CNCF Stack
# This script stops the complete CNCF Kind cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Complete CNCF Stack${NC}"
echo "=================================================="

# Stop port-forwards
echo -e "${YELLOW}🔌 Stopping port-forwards...${NC}"
pkill -f "kubectl port-forward" || true

# Delete Kind cluster
echo -e "${YELLOW}🗑️  Deleting CNCF Kind cluster...${NC}"
kind delete cluster --name cncf-cluster

echo -e "${GREEN}✅ Complete CNCF stack stopped${NC}"
echo ""
echo -e "${YELLOW}💡 To restart complete CNCF stack later, run:${NC}"
echo "  ./start-linux.sh or ./start-macos.sh"
echo ""
echo -e "${BLUE}📊 All CNCF services stopped - CPU usage should be minimal now${NC}"
