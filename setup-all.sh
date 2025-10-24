#!/bin/bash
# Complete Setup Script for Kubernetes + CNCF Services
# This script installs all prerequisites and sets up your environment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Automated Inquiries Processing - Complete Setup${NC}"
echo "=================================================="
echo "This script will install all prerequisites and set up your environment"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   echo "Please run as a regular user (sudo will be used when needed)"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install packages
install_package() {
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y "$@"
    elif command_exists yum; then
        sudo yum install -y "$@"
    elif command_exists dnf; then
        sudo dnf install -y "$@"
    elif command_exists pacman; then
        sudo pacman -S --noconfirm "$@"
    else
        echo -e "${RED}❌ Unsupported package manager${NC}"
        exit 1
    fi
}

# Check current installations
echo -e "${YELLOW}Checking current installations...${NC}"

TOOLS_TO_INSTALL=()

if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl not found${NC}"
    TOOLS_TO_INSTALL+=("kubectl")
else
    echo -e "${GREEN}✓ kubectl found${NC}"
fi

if ! command_exists helm; then
    echo -e "${RED}❌ helm not found${NC}"
    TOOLS_TO_INSTALL+=("helm")
else
    echo -e "${GREEN}✓ helm found${NC}"
fi

if ! command_exists terraform; then
    echo -e "${RED}❌ terraform not found${NC}"
    TOOLS_TO_INSTALL+=("terraform")
else
    echo -e "${GREEN}✓ terraform found${NC}"
fi

if ! command_exists istioctl; then
    echo -e "${RED}❌ istioctl not found${NC}"
    TOOLS_TO_INSTALL+=("istioctl")
else
    echo -e "${GREEN}✓ istioctl found${NC}"
fi

if ! command_exists minikube; then
    echo -e "${RED}❌ minikube not found${NC}"
    TOOLS_TO_INSTALL+=("minikube")
else
    echo -e "${GREEN}✓ minikube found${NC}"
fi

if ! command_exists kind; then
    echo -e "${RED}❌ kind not found${NC}"
    TOOLS_TO_INSTALL+=("kind")
else
    echo -e "${GREEN}✓ kind found${NC}"
fi

if ! command_exists jq; then
    echo -e "${RED}❌ jq not found${NC}"
    TOOLS_TO_INSTALL+=("jq")
else
    echo -e "${GREEN}✓ jq found${NC}"
fi

echo ""

# Install missing tools
if [ ${#TOOLS_TO_INSTALL[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 All tools are already installed!${NC}"
else
    echo -e "${YELLOW}Installing missing tools: ${TOOLS_TO_INSTALL[*]}${NC}"
    echo ""
    
    # Install basic packages first
    install_package curl wget unzip jq
    
    # Install kubectl
    if [[ " ${TOOLS_TO_INSTALL[*]} " =~ " kubectl " ]]; then
        echo -e "${BLUE}Installing kubectl...${NC}"
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        sudo mv kubectl /usr/local/bin/
        echo -e "${GREEN}✓ kubectl installed${NC}"
    fi
    
    # Install Helm
    if [[ " ${TOOLS_TO_INSTALL[*]} " =~ " helm " ]]; then
        echo -e "${BLUE}Installing Helm...${NC}"
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
        echo -e "${GREEN}✓ Helm installed${NC}"
    fi
    
    # Install Terraform
    if [[ " ${TOOLS_TO_INSTALL[*]} " =~ " terraform " ]]; then
        echo -e "${BLUE}Installing Terraform...${NC}"
        # Add HashiCorp GPG key
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update
        sudo apt-get install -y terraform
        echo -e "${GREEN}✓ Terraform installed${NC}"
    fi
    
    # Install Istio CLI
    if [[ " ${TOOLS_TO_INSTALL[*]} " =~ " istioctl " ]]; then
        echo -e "${BLUE}Installing Istio CLI...${NC}"
        curl -L https://istio.io/downloadIstio | sh -
        sudo mv istio-*/bin/istioctl /usr/local/bin/
        rm -rf istio-*
        echo -e "${GREEN}✓ Istio CLI installed${NC}"
    fi
    
    # Install Minikube
    if [[ " ${TOOLS_TO_INSTALL[*]} " =~ " minikube " ]]; then
        echo -e "${BLUE}Installing Minikube...${NC}"
        curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
        chmod +x minikube-linux-amd64
        sudo mv minikube-linux-amd64 /usr/local/bin/minikube
        echo -e "${GREEN}✓ Minikube installed${NC}"
    fi
    
    # Install Kind
    if [[ " ${TOOLS_TO_INSTALL[*]} " =~ " kind " ]]; then
        echo -e "${BLUE}Installing Kind...${NC}"
        [ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
        chmod +x ./kind
        sudo mv ./kind /usr/local/bin/kind
        echo -e "${GREEN}✓ Kind installed${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 All tools installed successfully!${NC}"
echo ""

# Verify installations
echo -e "${YELLOW}Verifying installations...${NC}"
kubectl version --client --short
helm version --short
terraform version
istioctl version --short
minikube version
kind version
echo ""

# Setup options
echo "=================================================="
echo -e "${GREEN}🚀 Setup Complete! Choose your deployment option:${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}Option 1: Docker Compose (Easiest - No Kubernetes needed)${NC}"
echo "  • Perfect for quick testing and demos"
echo "  • All services in Docker containers"
echo "  • CNCF services simulation"
echo "  • Run: ./deployment/docker-compose-cncf.sh"
echo ""
echo -e "${BLUE}Option 2: Local Kubernetes + Terraform (Recommended)${NC}"
echo "  • Production-like environment"
echo "  • Full CNCF services stack"
echo "  • Infrastructure as code"
echo "  • Run: ./deployment/terraform-deploy.sh"
echo ""
echo -e "${BLUE}Option 3: Local Kubernetes Setup (Manual)${NC}"
echo "  • Step-by-step Kubernetes setup"
echo "  • Good for learning"
echo "  • Run: ./deployment/local-k8s-setup.sh"
echo ""

# Ask user for choice
echo -e "${YELLOW}Which option would you like to use? (1/2/3)${NC}"
read -r choice

case $choice in
    1)
        echo -e "${GREEN}Starting Docker Compose deployment...${NC}"
        ./deployment/docker-compose-cncf.sh
        ;;
    2)
        echo -e "${GREEN}Starting Terraform + Kubernetes deployment...${NC}"
        echo -e "${YELLOW}First, let's set up a local Kubernetes cluster...${NC}"
        echo ""
        echo "Choose your Kubernetes cluster type:"
        echo "1) Minikube (recommended for development)"
        echo "2) Kind (lightweight, good for CI/CD)"
        echo "3) Use existing cluster"
        echo ""
        read -p "Enter your choice (1/2/3): " k8s_choice
        
        case $k8s_choice in
            1)
                echo -e "${BLUE}Starting Minikube...${NC}"
                minikube start --memory=8192 --cpus=4 --disk-size=20g
                minikube addons enable ingress
                minikube addons enable metrics-server
                echo -e "${GREEN}✓ Minikube cluster ready${NC}"
                ;;
            2)
                echo -e "${BLUE}Creating Kind cluster...${NC}"
                cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF
                echo -e "${GREEN}✓ Kind cluster ready${NC}"
                ;;
            3)
                echo -e "${YELLOW}Using existing cluster...${NC}"
                kubectl cluster-info
                ;;
        esac
        
        echo ""
        echo -e "${GREEN}Now deploying with Terraform...${NC}"
        ./deployment/terraform-deploy.sh
        ;;
    3)
        echo -e "${GREEN}Starting local Kubernetes setup...${NC}"
        ./deployment/local-k8s-setup.sh
        ;;
    *)
        echo -e "${RED}Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Test your application endpoints"
echo "2. Explore the monitoring dashboards"
echo "3. Check the GitOps workflow in ArgoCD"
echo "4. Review the documentation in docs/"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "• View pods: kubectl get pods --all-namespaces"
echo "• View services: kubectl get svc --all-namespaces"
echo "• View logs: kubectl logs -f deployment/automated-inquiries-processing -n inquiries-system"
echo "• Port forward: kubectl port-forward svc/grafana 3000:80 -n monitoring"
echo ""
echo -e "${GREEN}Happy Deploying! 🚀${NC}"
