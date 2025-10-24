#!/bin/bash
# Deploy to Kubernetes using Terraform (No Cloud Provider Required)
# This script uses Terraform to deploy CNCF services and the application to any Kubernetes cluster

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="./deployment/terraform"
TFVARS_FILE="${TERRAFORM_DIR}/terraform.tfvars"

echo -e "${GREEN}🚀 Deploying to Kubernetes with Terraform + CNCF Services${NC}"
echo "=================================================="
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed${NC}"
    echo "Install Terraform: https://developer.hashicorp.com/terraform/downloads"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    echo "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm is not installed${NC}"
    echo "Install Helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Check Kubernetes cluster connectivity
echo -e "${YELLOW}Checking Kubernetes cluster connectivity...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    echo "Make sure your kubeconfig is properly configured"
    echo "For local clusters:"
    echo "  • Minikube: minikube start"
    echo "  • Kind: kind create cluster"
    echo "  • K3s: k3s server &"
    exit 1
fi

CLUSTER_INFO=$(kubectl cluster-info)
echo -e "${GREEN}✓ Connected to cluster:${NC}"
echo "$CLUSTER_INFO"
echo ""

# Setup Terraform configuration
echo -e "${YELLOW}Setting up Terraform configuration...${NC}"

# Create terraform.tfvars if it doesn't exist
if [ ! -f "$TFVARS_FILE" ]; then
    echo "Creating terraform.tfvars from example..."
    cp "${TFVARS_FILE}.example" "$TFVARS_FILE"
    echo -e "${YELLOW}⚠️  Please review and customize ${TFVARS_FILE} if needed${NC}"
fi

# Initialize Terraform
echo "Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init

echo -e "${GREEN}✓ Terraform initialized${NC}"

# Plan the deployment
echo -e "${YELLOW}Planning Terraform deployment...${NC}"
terraform plan -out=tfplan

echo -e "${GREEN}✓ Terraform plan created${NC}"

# Ask for confirmation
echo ""
echo -e "${YELLOW}Do you want to proceed with the deployment? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Apply the deployment
echo -e "${YELLOW}Applying Terraform deployment...${NC}"
terraform apply tfplan

echo -e "${GREEN}✓ Terraform deployment completed${NC}"

# Wait for deployments to be ready
echo -e "${YELLOW}Waiting for deployments to be ready...${NC}"

# Wait for Istio
echo "Waiting for Istio..."
kubectl wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=300s

# Wait for ArgoCD
echo "Waiting for ArgoCD..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Wait for Prometheus Stack
echo "Waiting for Prometheus Stack..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-grafana -n monitoring

# Wait for Application
echo "Waiting for Application..."
kubectl wait --for=condition=available --timeout=300s deployment/automated-inquiries-processing -n inquiries-system

echo -e "${GREEN}✓ All deployments are ready${NC}"

# Get service URLs
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Terraform + Kubernetes Deployment Complete!${NC}"
echo "=================================================="
echo ""

# Get Terraform outputs
echo "🌐 Application URLs:"
terraform output -raw service_urls | jq -r 'to_entries[] | "  • \(.key): \(.value)"'

echo ""
echo "📊 Monitoring URLs:"
terraform output -raw monitoring_urls | jq -r 'to_entries[] | "  • \(.key): \(.value)"'

echo ""
echo "🔄 GitOps URLs:"
terraform output -raw gitops_urls | jq -r 'to_entries[] | "  • \(.key): \(.value)"'

echo ""
echo "📁 Created Namespaces:"
terraform output -raw namespaces | jq -r '.[] | "  • \(.)"'

echo ""
echo "🔧 Management Commands:"
echo "  • View all pods: kubectl get pods --all-namespaces"
echo "  • View services: kubectl get svc --all-namespaces"
echo "  • View Istio configs: kubectl get gateway,virtualservice,destinationrule --all-namespaces"
echo "  • View ArgoCD apps: kubectl get applications -n argocd"
echo "  • View Helm releases: helm list --all-namespaces"
echo ""

echo "📚 Next Steps:"
echo "  1. Test the application endpoints"
echo "  2. Access ArgoCD UI and sync applications"
echo "  3. Explore monitoring dashboards"
echo "  4. Configure alerts and notifications"
echo "  5. Set up CI/CD pipeline"
echo ""

echo "🛑 To destroy the deployment:"
echo "  cd $TERRAFORM_DIR && terraform destroy"
echo ""

# Return to original directory
cd - > /dev/null
