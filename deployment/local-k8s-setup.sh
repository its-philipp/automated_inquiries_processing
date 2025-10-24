#!/bin/bash
# Local Kubernetes setup with CNCF services using Minikube or Kind
# This script sets up everything locally without requiring AWS

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
K8S_TYPE="${K8S_TYPE:-minikube}"  # minikube or kind
NAMESPACE="inquiries-system"

echo -e "${GREEN}🚀 Setting up Local Kubernetes with CNCF Services${NC}"
echo "=================================================="
echo "Kubernetes Type: $K8S_TYPE"
echo "Namespace: $NAMESPACE"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

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

if ! command -v istioctl &> /dev/null; then
    echo -e "${RED}❌ Istio CLI is not installed${NC}"
    echo "Install Istio CLI: https://istio.io/latest/docs/setup/getting-started/#download"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Setup Kubernetes cluster
echo -e "${YELLOW}Setting up Kubernetes cluster...${NC}"

if [ "$K8S_TYPE" = "minikube" ]; then
    if ! command -v minikube &> /dev/null; then
        echo -e "${RED}❌ Minikube is not installed${NC}"
        echo "Install Minikube: https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi
    
    echo "Starting Minikube..."
    minikube start --memory=8192 --cpus=4 --disk-size=20g
    minikube addons enable ingress
    minikube addons enable metrics-server
    
elif [ "$K8S_TYPE" = "kind" ]; then
    if ! command -v kind &> /dev/null; then
        echo -e "${RED}❌ Kind is not installed${NC}"
        echo "Install Kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
        exit 1
    fi
    
    echo "Creating Kind cluster..."
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
fi

echo -e "${GREEN}✓ Kubernetes cluster ready${NC}"

# Create namespaces
echo -e "${YELLOW}Creating namespaces...${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -

# Label namespaces for Istio injection
kubectl label namespace $NAMESPACE istio-injection=enabled --overwrite
kubectl label namespace default istio-injection=enabled --overwrite

echo -e "${GREEN}✓ Namespaces created and labeled${NC}"

# Install Istio
echo -e "${YELLOW}Installing Istio...${NC}"
istioctl install --set values.defaultRevision=default -y
kubectl wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=300s

echo -e "${GREEN}✓ Istio installed${NC}"

# Install ArgoCD
echo -e "${YELLOW}Installing ArgoCD...${NC}"
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

echo -e "${GREEN}✓ ArgoCD installed${NC}"

# Install Prometheus Stack
echo -e "${YELLOW}Installing Prometheus Stack...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace $NAMESPACE \
  --set grafana.adminPassword=admin \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=30000 \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
  --wait

echo -e "${GREEN}✓ Prometheus Stack installed${NC}"

# Create secrets
echo -e "${YELLOW}Creating secrets...${NC}"
kubectl create secret generic app-secrets \
  --from-literal=database-url="postgresql://postgres:postgres@postgresql:5432/inquiry_automation" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Secrets created${NC}"

# Deploy application with Helm
echo -e "${YELLOW}Deploying application...${NC}"
helm upgrade --install automated-inquiries-processing ./k8s/helm \
  --namespace $NAMESPACE \
  --set image.repository=localhost:5000/automated-inquiries-processing \
  --set image.tag=latest \
  --set postgresql.enabled=true \
  --set redis.enabled=true \
  --set mlflow.enabled=true \
  --set prometheus.enabled=false \
  --set grafana.enabled=false \
  --set istio.enabled=true \
  --wait

echo -e "${GREEN}✓ Application deployed${NC}"

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
echo -e "${GREEN}🎉 Local Kubernetes Setup Complete!${NC}"
echo "=================================================="
echo ""

if [ "$K8S_TYPE" = "minikube" ]; then
    MINIKUBE_IP=$(minikube ip)
    echo "🌐 Application URLs (Minikube):"
    echo "  • API: http://$MINIKUBE_IP:8000"
    echo "  • API Docs: http://$MINIKUBE_IP:8000/docs"
    echo "  • Health Check: http://$MINIKUBE_IP:8000/api/v1/health"
    echo ""
    
    echo "📊 Monitoring URLs:"
    echo "  • Grafana: http://$MINIKUBE_IP:30000 (admin/admin)"
    echo "  • Prometheus: kubectl port-forward -n $NAMESPACE svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo "  • MLflow: kubectl port-forward -n $NAMESPACE svc/mlflow 5000:5000"
    echo ""
    
    echo "🔄 GitOps:"
    echo "  • ArgoCD UI: kubectl port-forward -n argocd svc/argocd-server 8080:443"
    echo "  • ArgoCD Admin Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
    echo ""
    
elif [ "$K8S_TYPE" = "kind" ]; then
    echo "🌐 Application URLs (Kind):"
    echo "  • API: http://localhost:8000"
    echo "  • API Docs: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/api/v1/health"
    echo ""
    
    echo "📊 Monitoring URLs:"
    echo "  • Grafana: http://localhost:30000 (admin/admin)"
    echo "  • Prometheus: kubectl port-forward -n $NAMESPACE svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo "  • MLflow: kubectl port-forward -n $NAMESPACE svc/mlflow 5000:5000"
    echo ""
    
    echo "🔄 GitOps:"
    echo "  • ArgoCD UI: kubectl port-forward -n argocd svc/argocd-server 8080:443"
    echo "  • ArgoCD Admin Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
    echo ""
fi

echo "🔧 Management Commands:"
echo "  • View pods: kubectl get pods -n $NAMESPACE"
echo "  • View services: kubectl get svc -n $NAMESPACE"
echo "  • View Istio configs: kubectl get gateway,virtualservice,destinationrule -n $NAMESPACE"
echo "  • View ArgoCD apps: kubectl get applications -n argocd"
echo ""

echo "📚 Next Steps:"
echo "  1. Build and push your Docker images to local registry"
echo "  2. Configure monitoring alerts in Grafana"
echo "  3. Set up CI/CD pipeline with ArgoCD"
echo "  4. Test the application endpoints"
echo ""

echo "🛑 To stop the cluster:"
if [ "$K8S_TYPE" = "minikube" ]; then
    echo "  minikube stop"
elif [ "$K8S_TYPE" = "kind" ]; then
    echo "  kind delete cluster"
fi
echo ""
