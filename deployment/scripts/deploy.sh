#!/bin/bash
# AWS deployment script for the Inquiry Automation Pipeline

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="inquiry-automation"

echo -e "${GREEN}🚀 Deploying Inquiry Automation Pipeline to AWS${NC}"
echo "=================================================="
echo "Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_NAME"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials valid (Account: $ACCOUNT_ID)${NC}"

# Build and push Docker images
echo -e "${YELLOW}Building and pushing Docker images...${NC}"

ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
ECR_REPOSITORY="$PROJECT_NAME"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Create ECR repositories if they don't exist
aws ecr describe-repositories --repository-names "$ECR_REPOSITORY/api" --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name "$ECR_REPOSITORY/api" --region $AWS_REGION

aws ecr describe-repositories --repository-names "$ECR_REPOSITORY/airflow" --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name "$ECR_REPOSITORY/airflow" --region $AWS_REGION

# Build and push API image
echo "Building API image..."
docker build -f docker/api.Dockerfile -t $PROJECT_NAME/api:latest .
docker tag $PROJECT_NAME/api:latest $ECR_REGISTRY/$ECR_REPOSITORY/api:latest
docker push $ECR_REGISTRY/$ECR_REPOSITORY/api:latest

# Build and push Airflow image
echo "Building Airflow image..."
docker build -f docker/airflow.Dockerfile -t $PROJECT_NAME/airflow:latest .
docker tag $PROJECT_NAME/airflow:latest $ECR_REGISTRY/$ECR_REPOSITORY/airflow:latest
docker push $ECR_REGISTRY/$ECR_REPOSITORY/airflow:latest

echo -e "${GREEN}✓ Docker images pushed to ECR${NC}"

# Deploy infrastructure with Terraform
echo -e "${YELLOW}Deploying infrastructure with Terraform...${NC}"

cd deployment/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars if it doesn't exist
if [ ! -f terraform.tfvars ]; then
    echo "Creating terraform.tfvars..."
    cat > terraform.tfvars << EOF
aws_region = "$AWS_REGION"
environment = "$ENVIRONMENT"
project_name = "$PROJECT_NAME"
db_password = "$(openssl rand -base64 32)"
EOF
    echo -e "${YELLOW}⚠️  Please review and update terraform.tfvars with your settings${NC}"
fi

# Plan deployment
echo "Planning Terraform deployment..."
terraform plan -var-file="terraform.tfvars" -out=tfplan

# Apply deployment
echo "Applying Terraform deployment..."
terraform apply tfplan

# Get outputs
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
ALB_DNS=$(terraform output -raw alb_dns_name)
S3_BUCKET=$(terraform output -raw s3_data_bucket)

echo -e "${GREEN}✓ Infrastructure deployed successfully${NC}"

# Update ECS service with new images
echo -e "${YELLOW}Updating ECS services...${NC}"

CLUSTER_NAME="$PROJECT_NAME-cluster"
API_SERVICE_NAME="$PROJECT_NAME-api"

# Force new deployment
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $API_SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION

echo -e "${GREEN}✓ ECS services updated${NC}"

# Wait for deployment to complete
echo -e "${YELLOW}Waiting for deployment to complete...${NC}"
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $API_SERVICE_NAME \
    --region $AWS_REGION

echo -e "${GREEN}✓ Deployment completed successfully!${NC}"

# Display deployment information
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "🌐 Application Load Balancer:"
echo "   URL: http://$ALB_DNS"
echo ""
echo "🗄️  Database:"
echo "   Endpoint: $RDS_ENDPOINT"
echo ""
echo "📦 Storage:"
echo "   S3 Bucket: $S3_BUCKET"
echo ""
echo "🐳 Container Images:"
echo "   API: $ECR_REGISTRY/$ECR_REPOSITORY/api:latest"
echo "   Airflow: $ECR_REGISTRY/$ECR_REPOSITORY/airflow:latest"
echo ""
echo "📊 Monitoring:"
echo "   CloudWatch Logs: /aws/ecs/$CLUSTER_NAME"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update your DNS to point to the ALB"
echo "   2. Configure SSL certificate in ALB"
echo "   3. Set up monitoring alerts in CloudWatch"
echo "   4. Test the API endpoints"
echo ""
echo "📚 Documentation:"
echo "   • API Docs: http://$ALB_DNS/docs"
echo "   • Health Check: http://$ALB_DNS/api/v1/health"
echo ""

cd ../..
