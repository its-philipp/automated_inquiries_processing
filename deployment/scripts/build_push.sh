#!/bin/bash
# Build and push Docker images to ECR

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="inquiry-automation"

echo -e "${GREEN}🐳 Building and Pushing Docker Images to ECR${NC}"
echo "=============================================="
echo "Region: $AWS_REGION"
echo "Project: $PROJECT_NAME"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo -e "${YELLOW}Account ID: $ACCOUNT_ID${NC}"
echo -e "${YELLOW}ECR Registry: $ECR_REGISTRY${NC}"
echo ""

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Create ECR repositories if they don't exist
echo -e "${YELLOW}Creating ECR repositories...${NC}"

for repo in api airflow mlflow dashboard; do
    echo "Creating repository: $PROJECT_NAME/$repo"
    aws ecr describe-repositories --repository-names "$PROJECT_NAME/$repo" --region $AWS_REGION 2>/dev/null || \
        aws ecr create-repository --repository-name "$PROJECT_NAME/$repo" --region $AWS_REGION
done

echo -e "${GREEN}✓ ECR repositories created/verified${NC}"

# Build and push images
echo -e "${YELLOW}Building and pushing Docker images...${NC}"

# API Image
echo "Building API image..."
docker build -f docker/api.Dockerfile -t $PROJECT_NAME/api:latest .
docker tag $PROJECT_NAME/api:latest $ECR_REGISTRY/$PROJECT_NAME/api:latest
docker push $ECR_REGISTRY/$PROJECT_NAME/api:latest
echo -e "${GREEN}✓ API image pushed${NC}"

# Airflow Image
echo "Building Airflow image..."
docker build -f docker/airflow.Dockerfile -t $PROJECT_NAME/airflow:latest .
docker tag $PROJECT_NAME/airflow:latest $ECR_REGISTRY/$PROJECT_NAME/airflow:latest
docker push $ECR_REGISTRY/$PROJECT_NAME/airflow:latest
echo -e "${GREEN}✓ Airflow image pushed${NC}"

# MLflow Image
echo "Building MLflow image..."
docker build -f docker/mlflow.Dockerfile -t $PROJECT_NAME/mlflow:latest .
docker tag $PROJECT_NAME/mlflow:latest $ECR_REGISTRY/$PROJECT_NAME/mlflow:latest
docker push $ECR_REGISTRY/$PROJECT_NAME/mlflow:latest
echo -e "${GREEN}✓ MLflow image pushed${NC}"

# Dashboard Image
echo "Building Dashboard image..."
docker build -f docker/dashboard.Dockerfile -t $PROJECT_NAME/dashboard:latest .
docker tag $PROJECT_NAME/dashboard:latest $ECR_REGISTRY/$PROJECT_NAME/dashboard:latest
docker push $ECR_REGISTRY/$PROJECT_NAME/dashboard:latest
echo -e "${GREEN}✓ Dashboard image pushed${NC}"

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 All images pushed successfully!${NC}"
echo "=============================================="
echo ""
echo "📦 Pushed Images:"
echo "   • API: $ECR_REGISTRY/$PROJECT_NAME/api:latest"
echo "   • Airflow: $ECR_REGISTRY/$PROJECT_NAME/airflow:latest"
echo "   • MLflow: $ECR_REGISTRY/$PROJECT_NAME/mlflow:latest"
echo "   • Dashboard: $ECR_REGISTRY/$PROJECT_NAME/dashboard:latest"
echo ""
echo "🔧 Next Steps:"
echo "   1. Run deployment script: ./deployment/scripts/deploy.sh"
echo "   2. Update ECS task definitions with new image URIs"
echo "   3. Deploy to ECS services"
echo ""
