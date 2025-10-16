#!/bin/bash
# Deploy Automated Inquiries Processing to Kubernetes with CNCF tools

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="inquiries-system"
CHART_PATH="./k8s/helm"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-your-registry}"

echo -e "${GREEN}🚀 Deploying Automated Inquiries Processing to Kubernetes${NC}"
echo "=================================================="
echo "Namespace: $NAMESPACE"
echo "Image Tag: $IMAGE_TAG"
echo "Registry: $REGISTRY"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm is not installed${NC}"
    exit 1
fi

if ! command -v istioctl &> /dev/null; then
    echo -e "${RED}❌ Istio CLI is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Check cluster connectivity
echo -e "${YELLOW}Checking cluster connectivity...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Connected to cluster${NC}"

# Create namespace
echo -e "${YELLOW}Creating namespace...${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Label namespace for Istio injection
kubectl label namespace $NAMESPACE istio-injection=enabled --overwrite

echo -e "${GREEN}✓ Namespace created and labeled${NC}"

# Install Istio (if not already installed)
echo -e "${YELLOW}Checking Istio installation...${NC}"
if ! kubectl get namespace istio-system &> /dev/null; then
    echo "Installing Istio..."
    istioctl install --set values.defaultRevision=default -y
    kubectl label namespace default istio-injection=enabled
    echo -e "${GREEN}✓ Istio installed${NC}"
else
    echo -e "${GREEN}✓ Istio already installed${NC}"
fi

# Install ArgoCD (if not already installed)
echo -e "${YELLOW}Checking ArgoCD installation...${NC}"
if ! kubectl get namespace argocd &> /dev/null; then
    echo "Installing ArgoCD..."
    kubectl create namespace argocd
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for ArgoCD to be ready
    echo "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
    
    echo -e "${GREEN}✓ ArgoCD installed${NC}"
else
    echo -e "${GREEN}✓ ArgoCD already installed${NC}"
fi

# Create secrets
echo -e "${YELLOW}Creating secrets...${NC}"
kubectl create secret generic app-secrets \
  --from-literal=database-url="postgresql://postgres:postgres@postgresql:5432/inquiry_automation" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Secrets created${NC}"

# Deploy with Helm
echo -e "${YELLOW}Deploying with Helm...${NC}"
helm upgrade --install automated-inquiries-processing $CHART_PATH \
  --namespace $NAMESPACE \
  --set image.repository=$REGISTRY/automated-inquiries-processing \
  --set image.tag=$IMAGE_TAG \
  --set postgresql.enabled=true \
  --set redis.enabled=true \
  --set mlflow.enabled=true \
  --set prometheus.enabled=true \
  --set grafana.enabled=true \
  --set istio.enabled=true \
  --wait

echo -e "${GREEN}✓ Helm deployment completed${NC}"

# Apply Istio configurations
echo -e "${YELLOW}Applying Istio configurations...${NC}"
kubectl apply -f k8s/istio/gateway.yaml
kubectl apply -f k8s/istio/virtualservice.yaml
kubectl apply -f k8s/istio/destinationrule.yaml
kubectl apply -f k8s/istio/authorizationpolicy.yaml

echo -e "${GREEN}✓ Istio configurations applied${NC}"

# Apply ArgoCD application
echo -e "${YELLOW}Applying ArgoCD application...${NC}"
kubectl apply -f k8s/argocd/project.yaml
kubectl apply -f k8s/argocd/application.yaml

echo -e "${GREEN}✓ ArgoCD application created${NC}"

# Wait for deployment to be ready
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/automated-inquiries-processing -n $NAMESPACE

echo -e "${GREEN}✓ Deployment is ready${NC}"

# Get service URLs
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo ""

# Get Istio Gateway IP
GATEWAY_IP=$(kubectl get service istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$GATEWAY_IP" ]; then
    GATEWAY_IP=$(kubectl get service istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

echo "🌐 Application URLs:"
echo "  • API: http://inquiries-api.example.com (Gateway IP: $GATEWAY_IP)"
echo "  • API Docs: http://inquiries-api.example.com/docs"
echo "  • Health Check: http://inquiries-api.example.com/api/v1/health"
echo ""

echo "📊 Monitoring URLs:"
echo "  • Grafana: kubectl port-forward -n $NAMESPACE svc/grafana 3000:80"
echo "  • Prometheus: kubectl port-forward -n $NAMESPACE svc/prometheus-server 9090:80"
echo "  • MLflow: kubectl port-forward -n $NAMESPACE svc/mlflow 5000:5000"
echo ""

echo "🔄 GitOps:"
echo "  • ArgoCD UI: kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "  • ArgoCD Admin Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo ""

echo "🔧 Management Commands:"
echo "  • View pods: kubectl get pods -n $NAMESPACE"
echo "  • View services: kubectl get svc -n $NAMESPACE"
echo "  • View Istio configs: kubectl get gateway,virtualservice,destinationrule -n $NAMESPACE"
echo "  • View ArgoCD apps: kubectl get applications -n argocd"
echo ""

echo "📚 Next Steps:"
echo "  1. Configure DNS to point inquiries-api.example.com to $GATEWAY_IP"
echo "  2. Set up SSL certificates for HTTPS"
echo "  3. Configure monitoring alerts"
echo "  4. Set up CI/CD pipeline with ArgoCD"
echo ""
