#!/bin/bash

# 🚀 Automated Inquiries Processing - Complete Kubernetes Deployment
# This script starts all services and provides access URLs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Automated Inquiries Processing Pipeline${NC}"
echo "=================================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Check if minikube is running
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Kubernetes cluster not running. Starting Minikube...${NC}"
    minikube start --memory=6144mb
fi

echo -e "${GREEN}✅ Kubernetes cluster is running${NC}"

# Create namespaces
echo -e "${BLUE}📦 Creating namespaces...${NC}"
kubectl create namespace inquiries-system --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -

# Deploy core infrastructure
echo -e "${BLUE}🏗️  Deploying core infrastructure...${NC}"

# Deploy PostgreSQL and Redis
echo "  📊 Deploying PostgreSQL and Redis..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm upgrade --install postgresql bitnami/postgresql \
  --namespace inquiries-system \
  --set auth.postgresPassword=postgres \
  --set auth.database=inquiry_automation \
  --set primary.persistence.enabled=true \
  --set primary.persistence.size=20Gi

helm upgrade --install redis bitnami/redis \
  --namespace inquiries-system \
  --set auth.enabled=false \
  --set master.persistence.enabled=true \
  --set master.persistence.size=8Gi

# Deploy monitoring stack
echo "  📈 Deploying monitoring stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin

# Deploy Istio
echo "  🌐 Deploying Istio service mesh..."
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

helm upgrade --install istio-base istio/base \
  --namespace istio-system \
  --create-namespace

helm upgrade --install istiod istio/istiod \
  --namespace istio-system \
  --wait

helm upgrade --install istio-ingressgateway istio/gateway \
  --namespace istio-system \
  --set service.type=NodePort \
  --set service.ports[0].name=http2 \
  --set service.ports[0].port=80 \
  --set service.ports[0].nodePort=30080

# Deploy ArgoCD
echo "  🔄 Deploying ArgoCD..."
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=NodePort \
  --set server.service.ports.server.nodePort=30009

# Wait for core services
echo -e "${YELLOW}⏳ Waiting for core services to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n inquiries-system --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n inquiries-system --timeout=300s

# Initialize database
echo -e "${BLUE}🗄️  Initializing database...${NC}"
kubectl apply -f k8s/database/init-database-job.yaml
kubectl wait --for=condition=complete job/init-database -n inquiries-system --timeout=300s

# Create Airflow database
echo -e "${BLUE}🔄 Setting up Airflow...${NC}"
kubectl exec -n inquiries-system postgresql-0 -- env PGPASSWORD=postgres psql -U postgres -c "CREATE DATABASE airflow;" || true

# Deploy Airflow
kubectl apply -f k8s/airflow/airflow-setup.yaml
kubectl apply -f k8s/airflow/airflow-init-job.yaml
kubectl wait --for=condition=complete job/airflow-init -n airflow --timeout=300s

kubectl apply -f k8s/airflow/airflow-create-user.yaml
kubectl wait --for=condition=complete job/airflow-create-user -n airflow --timeout=300s

kubectl apply -f k8s/airflow/airflow-simple.yaml

# Deploy applications
echo -e "${BLUE}🚀 Deploying applications...${NC}"
kubectl apply -f k8s/services/streamlit-dashboard.yaml
kubectl apply -f k8s/services/fastapi-simple.yaml

# Wait for applications
echo -e "${YELLOW}⏳ Waiting for applications to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=streamlit-dashboard -n inquiries-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=airflow-webserver -n airflow --timeout=300s

# Start port-forwards
echo -e "${BLUE}🌐 Starting port-forwards...${NC}"
kubectl port-forward -n inquiries-system svc/streamlit-dashboard 8501:8501 &
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 &
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080 &

sleep 5

# Display access information
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo "========================"
echo -e "\n${YELLOW}📊 Access Your Services:${NC}"
echo "  • Streamlit Dashboard: http://localhost:8501"
echo "  • Grafana Monitoring:  http://localhost:3000 (admin/admin)"
echo "  • Airflow DAGs:        http://localhost:8080 (admin/admin)"
echo ""
echo -e "${YELLOW}🔄 Available DAGs in Airflow:${NC}"
echo "  • batch_classify    - Classify pending inquiries (hourly)"
echo "  • daily_ingestion  - Daily data processing (6 AM daily)"
echo "  • model_retrain     - Retrain ML models (weekly)"
echo ""
echo -e "${YELLOW}🛑 To stop all services:${NC}"
echo "  ./stop-services.sh"
echo ""
echo -e "${GREEN}✨ Your inquiry automation pipeline is ready!${NC}"
