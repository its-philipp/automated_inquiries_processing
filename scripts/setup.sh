#!/bin/bash
# Quick setup script for the Inquiry Automation Pipeline

set -e

echo "🚀 Inquiry Automation Pipeline - Setup Script"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Install uv if not installed
if ! command -v uv &> /dev/null; then
    echo -e "\n${YELLOW}Installing uv package manager...${NC}"
    pip install uv
    echo -e "${GREEN}✓ uv installed${NC}"
fi

# Generate mock data
echo -e "\n${YELLOW}Generating mock inquiry data...${NC}"
if [ ! -f data/raw/sample_inquiries.json ]; then
    python data/generate_mock_data.py
    echo -e "${GREEN}✓ Mock data generated${NC}"
else
    echo -e "${GREEN}✓ Mock data already exists${NC}"
fi

# Pull Docker images
echo -e "\n${YELLOW}Pulling Docker images (this may take a while)...${NC}"
docker-compose pull

# Build custom images
echo -e "\n${YELLOW}Building custom Docker images...${NC}"
docker-compose build

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the services, run:"
echo "  docker-compose up -d"
echo ""
echo "To view logs, run:"
echo "  docker-compose logs -f"
echo ""
echo "Services will be available at:"
echo "  • API:        http://localhost:8000/docs"
echo "  • Dashboard:  http://localhost:8501"
echo "  • Airflow:    http://localhost:8080 (admin/admin)"
echo "  • MLflow:     http://localhost:5000"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana:    http://localhost:3000 (admin/admin)"

