#!/bin/bash
# Teardown AWS infrastructure for the Inquiry Automation Pipeline

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

echo -e "${RED}🗑️  Tearing Down Inquiry Automation Pipeline${NC}"
echo "=============================================="
echo "Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_NAME"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will destroy all AWS resources!${NC}"
echo "This action cannot be undone."
echo ""

# Confirmation
read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${YELLOW}Proceeding with teardown...${NC}"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed${NC}"
    exit 1
fi

# Destroy Terraform infrastructure
echo -e "${YELLOW}Destroying Terraform infrastructure...${NC}"

cd deployment/terraform

if [ -f terraform.tfvars ]; then
    terraform destroy -var-file="terraform.tfvars" -auto-approve
else
    echo -e "${YELLOW}⚠️  No terraform.tfvars found, using defaults${NC}"
    terraform destroy -auto-approve
fi

echo -e "${GREEN}✓ Infrastructure destroyed${NC}"

# Delete ECR images (optional)
echo ""
read -p "Do you want to delete ECR images? (yes/no): " delete_images
if [ "$delete_images" = "yes" ]; then
    echo -e "${YELLOW}Deleting ECR images...${NC}"
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    for repo in api airflow mlflow dashboard; do
        echo "Deleting images from $PROJECT_NAME/$repo..."
        aws ecr list-images --repository-name "$PROJECT_NAME/$repo" --region $AWS_REGION --query 'imageIds[*]' --output json | \
            aws ecr batch-delete-image --repository-name "$PROJECT_NAME/$repo" --region $AWS_REGION --image-ids file:///dev/stdin 2>/dev/null || true
    done
    
    echo -e "${GREEN}✓ ECR images deleted${NC}"
fi

# Delete ECR repositories (optional)
echo ""
read -p "Do you want to delete ECR repositories? (yes/no): " delete_repos
if [ "$delete_repos" = "yes" ]; then
    echo -e "${YELLOW}Deleting ECR repositories...${NC}"
    
    for repo in api airflow mlflow dashboard; do
        echo "Deleting repository $PROJECT_NAME/$repo..."
        aws ecr delete-repository --repository-name "$PROJECT_NAME/$repo" --region $AWS_REGION --force 2>/dev/null || true
    done
    
    echo -e "${GREEN}✓ ECR repositories deleted${NC}"
fi

cd ../..

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Teardown Complete!${NC}"
echo "=============================================="
echo ""
echo "✅ Destroyed Resources:"
echo "   • ECS Cluster and Services"
echo "   • RDS PostgreSQL Instance"
echo "   • Application Load Balancer"
echo "   • S3 Buckets"
echo "   • VPC and Networking"
echo "   • Security Groups"
echo "   • CloudWatch Log Groups"
if [ "$delete_images" = "yes" ]; then
    echo "   • ECR Images"
fi
if [ "$delete_repos" = "yes" ]; then
    echo "   • ECR Repositories"
fi
echo ""
echo "💡 Note: Some resources may take a few minutes to fully delete."
echo ""
