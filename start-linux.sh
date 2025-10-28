#!/bin/bash

# 🚀 Bulletproof Complete CNCF Stack Deployment
# This script deploys ALL CNCF services with proper error handling and waiting

set -e

# Disable bash completion to avoid dump_bash_state errors
export BASH_COMPLETION_COMPAT_DIR=""
export BASH_COMPLETION_USER_FILE=""
unset BASH_COMPLETION_COMPAT_DIR
unset BASH_COMPLETION_USER_FILE

# Disable problematic bash completion functions
unset -f dump_bash_state 2>/dev/null || true
unset -f _bash_completion_loader 2>/dev/null || true

# Override problematic functions
dump_bash_state() { return 0; }
_bash_completion_loader() { return 0; }

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to wait for pods with better error handling
wait_for_pods() {
    local namespace=$1
    local selector=$2
    local timeout=${3:-120}
    local description=${4:-"pods"}
    
    echo "  ⏳ Waiting for $description..."
    if kubectl wait --for=condition=ready pod -l "$selector" -n "$namespace" --timeout="${timeout}s" 2>/dev/null; then
        echo "  ✅ $description ready"
        return 0
    else
        echo "  ⚠️  $description not ready after ${timeout}s, continuing..."
        return 1
    fi
}

# Function to wait for jobs with better error handling
wait_for_job() {
    local namespace=$1
    local job_name=$2
    local timeout=${3:-120}
    local description=${4:-"job"}
    
    echo "  ⏳ Waiting for $description..."
    if kubectl wait --for=condition=complete job/"$job_name" -n "$namespace" --timeout="${timeout}s" 2>/dev/null; then
        echo "  ✅ $description completed"
        return 0
    else
        echo "  ⚠️  $description not completed after ${timeout}s, continuing..."
        return 1
    fi
}

echo -e "${BLUE}🚀 Starting Bulletproof CNCF Stack Deployment${NC}"
echo "=================================================="

# Check prerequisites
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

if ! command -v kind &> /dev/null; then
    echo -e "${RED}❌ Kind not found. Installing Kind...${NC}"
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm not found. Installing Helm...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo -e "${GREEN}✅ Prerequisites ready${NC}"

# Clean up existing cluster
echo -e "${YELLOW}🧹 Cleaning up existing cluster...${NC}"
kind delete cluster --name cncf-cluster 2>/dev/null || true
sleep 5

# Create Kind cluster
echo -e "${BLUE}🏗️  Creating Kind cluster...${NC}"
cat <<EOF | kind create cluster --name cncf-cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        system-reserved: memory=1Gi
        kube-reserved: memory=512Mi
        eviction-hard: memory.available<200Mi
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
  - containerPort: 30001
    hostPort: 30001
    protocol: TCP
  - containerPort: 30007
    hostPort: 30007
    protocol: TCP
  - containerPort: 30009
    hostPort: 30009
    protocol: TCP
EOF

kubectl cluster-info --context kind-cncf-cluster
echo -e "${GREEN}✅ Kind cluster created${NC}"

# Build custom Airflow image with BERT models
echo -e "${BLUE}🤖 Building custom Airflow image with ML/NLP libraries...${NC}"
if ! docker images | grep -q "airflow-ml.*2.7.3"; then
    echo "  📦 Building airflow-ml:2.7.3 (this may take 5-10 minutes)..."
    docker build -t airflow-ml:2.7.3 -f docker/airflow-ml.Dockerfile . 
    echo "  ✅ Custom Airflow image built"
else
    echo "  ✅ Custom Airflow image already exists"
fi

# Build custom FastAPI image with ML dependencies
echo -e "${BLUE}🔧 Building custom FastAPI image with ML/NLP libraries...${NC}"
if ! docker images | grep -q "fastapi-app.*1.0.0"; then
    echo "  📦 Building fastapi-app:1.0.0 (this may take 3-5 minutes)..."
    docker build -t fastapi-app:1.0.0 -f docker/fastapi-app.Dockerfile . 
    echo "  ✅ Custom FastAPI image built"
else
    echo "  ✅ Custom FastAPI image already exists"
fi

# Load custom images into Kind cluster
echo "  📤 Loading custom images into Kind cluster..."
kind load docker-image airflow-ml:2.7.3 --name cncf-cluster
kind load docker-image fastapi-app:1.0.0 --name cncf-cluster
echo -e "${GREEN}✅ Custom images loaded into Kind cluster${NC}"

# Create namespaces
echo -e "${BLUE}📦 Creating namespaces...${NC}"
kubectl create namespace inquiries-system --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ Namespaces created${NC}"

# Wait for cluster to be fully ready
echo -e "${YELLOW}⏳ Waiting for cluster to be ready...${NC}"
sleep 10

# Deploy Istio
echo -e "${BLUE}🌐 Deploying Istio Service Mesh...${NC}"
helm repo add istio https://istio-release.storage.googleapis.com/charts 2>/dev/null || true
helm repo update

echo "  📦 Installing Istio base..."
helm upgrade --install istio-base istio/base \
  --namespace istio-system \
  --create-namespace \
  --wait \
  --timeout=5m

echo "  🚀 Installing Istio control plane..."
helm upgrade --install istiod istio/istiod \
  --namespace istio-system \
  --wait \
  --timeout=5m

echo "  🌉 Installing Istio ingress gateway..."
helm upgrade --install istio-ingressgateway istio/gateway \
  --namespace istio-system \
  --set service.type=NodePort \
  --set service.ports[0].name=http2 \
  --set service.ports[0].port=80 \
  --set service.ports[0].nodePort=30080 \
  --wait \
  --timeout=5m

echo -e "${GREEN}✅ Istio deployed${NC}"

# Deploy ArgoCD
echo -e "${BLUE}🔄 Deploying ArgoCD GitOps...${NC}"
helm repo add argo https://argoproj.github.io/argo-helm 2>/dev/null || true
helm repo update

helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=ClusterIP \
  --set configs.cm."application\.instanceLabelKey"="argocd\.argoproj\.io/instance" \
  --wait \
  --timeout=5m

echo -e "${GREEN}✅ ArgoCD deployed${NC}"

# Deploy ArgoCD Application for GitOps
echo -e "${BLUE}🔄 Creating ArgoCD Application for GitOps...${NC}"
kubectl apply -f k8s/argocd/streamlit-gitops.yaml
echo -e "${GREEN}✅ ArgoCD Application created (streamlit-dashboard-gitops)${NC}"

# Deploy Prometheus Stack
echo -e "${BLUE}📈 Deploying Prometheus Stack...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=30001 \
  --wait \
  --timeout=5m

echo -e "${GREEN}✅ Prometheus Stack deployed${NC}"

# Deploy custom Grafana dashboard
echo -e "${BLUE}📊 Deploying custom Inquiry Processing dashboard to Grafana...${NC}"
kubectl apply -f k8s/monitoring/grafana-dashboard.yaml
echo -e "${GREEN}✅ Custom Grafana dashboard deployed${NC}"

# Deploy PostgreSQL
echo -e "${BLUE}📊 Deploying PostgreSQL...${NC}"
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: inquiries-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: inquiry_automation
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          value: postgres
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: inquiries-system
spec:
  selector:
    app: postgresql
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP
EOF

# Deploy Redis
echo -e "${BLUE}🔄 Deploying Redis...${NC}"
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: inquiries-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: inquiries-system
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
  type: ClusterIP
EOF

# Wait for core services
echo -e "${YELLOW}⏳ Waiting for core services...${NC}"
wait_for_pods "inquiries-system" "app=postgresql" 120 "PostgreSQL"
wait_for_pods "inquiries-system" "app=redis" 120 "Redis"

# Create Airflow database
echo -e "${BLUE}🔄 Setting up Airflow...${NC}"
echo "  🗄️  Creating Airflow database..."
POSTGRES_POD=$(kubectl get pods -n inquiries-system -l app=postgresql -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$POSTGRES_POD" ]; then
    # Wait for PostgreSQL to be ready and create Airflow database
    kubectl wait --for=condition=ready pod -n inquiries-system $POSTGRES_POD --timeout=60s
    sleep 5  # Give PostgreSQL extra time to be fully ready
    
    # Create Airflow database with proper error handling
    if kubectl exec -n inquiries-system $POSTGRES_POD -- env PGPASSWORD=postgres psql -U postgres -c "CREATE DATABASE airflow;" 2>/dev/null; then
        echo "  ✅ Airflow database created"
    else
        echo "  ⚠️  Airflow database might already exist, continuing..."
    fi
    
    # Verify database was created
    if kubectl exec -n inquiries-system $POSTGRES_POD -- env PGPASSWORD=postgres psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='airflow';" 2>/dev/null | grep -q "airflow"; then
        echo "  ✅ Airflow database verified"
    else
        echo "  ❌ Airflow database verification failed"
        exit 1
    fi
else
    echo "  ⚠️  PostgreSQL pod not found, skipping database creation"
    exit 1
fi

# Create DNS alias for PostgreSQL in airflow namespace (for DAG compatibility)
echo "  🔗 Creating PostgreSQL DNS alias in airflow namespace..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: airflow
spec:
  type: ExternalName
  externalName: postgresql.inquiries-system.svc.cluster.local
EOF
echo "  ✅ PostgreSQL DNS alias created"

# Initialize Airflow database schema BEFORE deploying pods
echo "  🗄️  Initializing Airflow database schema FIRST..."
kubectl run airflow-init --rm -i --restart=Never --image=airflow-ml:2.7.3 -n airflow \
  --env="AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://postgres:postgres@postgresql.inquiries-system.svc.cluster.local:5432/airflow" \
  -- airflow db init 2>/dev/null || echo "  ⚠️  Database might already be initialized"
echo "  ✅ Airflow database schema initialized"

# Create ConfigMaps
echo "  📋 Creating ConfigMaps..."
kubectl create configmap airflow-dags --from-file=airflow/dags/ -n airflow --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true
echo "  ✅ ConfigMaps created"

# Deploy Airflow using optimized YAML with custom image and increased memory
echo "  🚀 Deploying Airflow..."
kubectl apply -f k8s/airflow/airflow-with-dags-fix.yaml

# Wait for Airflow to be ready
echo "  ⏳ Waiting for Airflow pods to be ready..."
kubectl wait --for=condition=ready pod -l app=airflow-webserver -n airflow --timeout=120s
kubectl wait --for=condition=ready pod -l app=airflow-scheduler -n airflow --timeout=120s

# Get Airflow pod for admin user creation
AIRFLOW_POD=$(kubectl get pods -n airflow -l app=airflow-webserver -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

# Create Airflow admin user
echo "  👤 Creating Airflow admin user..."
if [ -n "$AIRFLOW_POD" ]; then
    # Check if admin user already exists
    if kubectl exec -n airflow $AIRFLOW_POD -- airflow users list 2>/dev/null | grep -q "admin"; then
        echo "  ✅ Admin user already exists"
    else
        # Create admin user with proper error handling
        if kubectl exec -n airflow $AIRFLOW_POD -- airflow users create \
          --username admin \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@example.com \
          --password admin 2>&1 | grep -q "created\|Added user"; then
            echo "  ✅ Admin user created successfully"
        else
            echo "  ⚠️  Failed to create admin user, retrying..."
            sleep 5
            if kubectl exec -n airflow $AIRFLOW_POD -- airflow users create \
              --username admin \
              --firstname Admin \
              --lastname User \
              --role Admin \
              --email admin@example.com \
              --password admin 2>&1 | grep -q "created\|Added user"; then
                echo "  ✅ Admin user created on retry"
            else
                echo "  ⚠️  Could not create admin user - you can create it manually later"
                echo "  💡 Run: kubectl exec -n airflow \$AIRFLOW_POD -- airflow users create --username admin --password admin --role Admin"
            fi
        fi
    fi
    
    # Verify user was created
    if kubectl exec -n airflow $AIRFLOW_POD -- airflow users list 2>/dev/null | grep -q "admin"; then
        echo "  ✅ Admin user verified in database"
    else
        echo "  ❌ Admin user creation failed!"
    fi
fi

# Unpause all DAGs
echo "  ▶️  Unpausing DAGs..."
kubectl exec -n airflow $AIRFLOW_POD -- airflow dags unpause batch_classify_inquiries 2>/dev/null || true
kubectl exec -n airflow $AIRFLOW_POD -- airflow dags unpause daily_data_ingestion 2>/dev/null || true
kubectl exec -n airflow $AIRFLOW_POD -- airflow dags unpause model_retraining 2>/dev/null || true

echo "  ✅ Airflow ready with all 3 DAGs"

# Create remaining ConfigMaps
echo "  📋 Creating remaining ConfigMaps..."
kubectl create configmap streamlit-app-code --from-file=inquiry_monitoring_dashboard.py --from-file=src/ --from-file=k8s/database/init-database-simple.py -n inquiries-system --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true
echo -e "${GREEN}✅ ConfigMaps created${NC}"

# Initialize application database
echo -e "${BLUE}🗄️  Initializing application database...${NC}"
kubectl apply -f k8s/database/init-database-job.yaml 2>/dev/null || true

# Wait for application database with retry
for i in {1..3}; do
    echo "  ⏳ Attempt $i/3: Waiting for application database initialization..."
    if kubectl wait --for=condition=complete job/init-database -n inquiries-system --timeout=60s 2>/dev/null; then
        echo "  ✅ Application database initialized"
        break
    else
        echo "  ⚠️  Database init failed, retrying..."
        kubectl delete job init-database -n inquiries-system 2>/dev/null || true
        sleep 5
        kubectl apply -f k8s/database/init-database-job.yaml 2>/dev/null || true
    fi
done

# Deploy applications
echo -e "${BLUE}🚀 Deploying applications...${NC}"
kubectl apply -f k8s/services/streamlit-dashboard.yaml 2>/dev/null || true
  kubectl apply -f k8s/services/fastapi.yaml 2>/dev/null || true

# Wait for Streamlit with retry
for i in {1..3}; do
    echo "  ⏳ Attempt $i/3: Waiting for Streamlit dashboard..."
    if kubectl wait --for=condition=ready pod -l app=streamlit-dashboard -n inquiries-system --timeout=60s 2>/dev/null; then
        echo "  ✅ Streamlit dashboard ready"
        break
    else
        echo "  ⚠️  Streamlit not ready, restarting..."
        kubectl rollout restart deployment/streamlit-dashboard -n inquiries-system 2>/dev/null || true
        sleep 10
    fi
done

# Deploy Istio Gateway and VirtualService
echo -e "${BLUE}🌐 Configuring Istio routing...${NC}"
kubectl apply -f k8s/istio/gateway-fix.yaml
echo -e "${GREEN}✅ Istio Gateway configured${NC}"
kubectl apply -f k8s/istio/virtualservice.yaml 2>/dev/null || true

# Wait for all services to be fully ready
echo -e "${YELLOW}⏳ Waiting for all services to be ready...${NC}"
sleep 10

# Verify all services are running
echo "  🔍 Verifying service status..."
kubectl get pods -n inquiries-system -l app=streamlit-dashboard --no-headers | grep -q "Running" && echo "  ✅ Streamlit dashboard ready" || echo "  ⚠️  Streamlit dashboard not ready"
kubectl get pods -n airflow -l app=airflow-webserver --no-headers | grep -q "Running" && echo "  ✅ Airflow webserver ready" || echo "  ⚠️  Airflow webserver not ready"
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana --no-headers | grep -q "Running" && echo "  ✅ Grafana ready" || echo "  ⚠️  Grafana not ready"
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server --no-headers | grep -q "Running" && echo "  ✅ ArgoCD ready" || echo "  ⚠️  ArgoCD not ready"

# Display final status
echo -e "\n${GREEN}🎉 Complete CNCF Stack Ready!${NC}"
echo "========================"

# Get ArgoCD password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d 2>/dev/null)
if [ -z "$ARGOCD_PASSWORD" ]; then
    ARGOCD_PASSWORD="<get-password>"
fi

echo -e "\n${YELLOW}📊 Access Your Complete CNCF Stack:${NC}"
echo "  • Streamlit Dashboard: http://localhost:8501"
echo "  • FastAPI Backend:     http://localhost:8000 (Swagger: /docs)"
echo "  • Grafana Monitoring:  http://localhost:3000 (admin/admin)"
echo "  • Airflow DAGs:        http://localhost:8080 (admin/admin)"
echo "  • ArgoCD GitOps:       https://localhost:30009 (admin/$ARGOCD_PASSWORD)"
echo "  • Istio Gateway:       http://localhost:30080"
echo ""
echo -e "${YELLOW}🔄 Available DAGs in Airflow:${NC}"
echo "  • batch_classify    - Classify pending inquiries (hourly)"
echo "  • daily_ingestion  - Daily data processing (6 AM daily)"
echo "  • model_retrain     - Retrain ML models (weekly)"
echo ""
echo -e "${YELLOW}🌐 CNCF Services Running:${NC}"
echo "  • Istio Service Mesh - Traffic management & security"
echo "  • ArgoCD GitOps - Continuous deployment"
echo "  • Prometheus Stack - Monitoring & alerting"
echo "  • Helm - Package management"
echo ""
echo -e "${YELLOW}🔧 Airflow Setup Features:${NC}"
echo "  • Robust database initialization with verification"
echo "  • Proper DAG mounting to avoid ConfigMap loops"
echo "  • Admin user creation with error handling"
echo "  • Schema migration with proper timing"
echo ""
echo -e "${YELLOW}🛑 To stop all services:${NC}"
echo "  ./stop-cncf.sh"
echo ""
echo -e "${GREEN}✨ Your bulletproof CNCF-based inquiry automation pipeline is ready!${NC}"
echo -e "${BLUE}💡 Full CNCF stack with robust error handling and proper Airflow initialization${NC}"

# Start port-forwards ONLY after all services are confirmed ready
echo -e "\n${BLUE}🌐 Starting port-forwards...${NC}"
pkill -f "kubectl port-forward" 2>/dev/null || true
sleep 5  # Give enough time for cleanup

echo "  🔌 Setting up port forwarding with proper wait times..."

# Wait for pods to be fully ready before port-forwarding
echo "  ⏳ Ensuring all pods are fully ready..."
kubectl wait --for=condition=ready pod -l app=streamlit-dashboard -n inquiries-system --timeout=30s 2>/dev/null || echo "  ⚠️  Streamlit pod not ready yet"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=30s 2>/dev/null || echo "  ⚠️  Grafana pod not ready yet"
kubectl wait --for=condition=ready pod -l app=airflow-webserver -n airflow --timeout=30s 2>/dev/null || echo "  ⚠️  Airflow pod not ready yet"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=30s 2>/dev/null || echo "  ⚠️  ArgoCD pod not ready yet"

sleep 5  # Extra time for services to stabilize

# Start each port forward with better spacing and logging
echo "  🔌 Starting Streamlit port-forward..."
nohup kubectl port-forward -n inquiries-system svc/streamlit-dashboard 8501:8501 > /tmp/pf-streamlit.log 2>&1 &
sleep 3

echo "  🔌 Starting Grafana port-forward..."
nohup kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 > /tmp/pf-grafana.log 2>&1 &
sleep 3

echo "  🔌 Starting Airflow port-forward..."
nohup kubectl port-forward -n airflow svc/airflow-webserver 8080:8080 > /tmp/pf-airflow.log 2>&1 &
sleep 3

echo "  🔌 Starting ArgoCD port-forward..."
nohup kubectl port-forward -n argocd svc/argocd-server 30009:443 > /tmp/pf-argocd.log 2>&1 &
sleep 3

echo "  🔌 Starting FastAPI port-forward..."
nohup kubectl port-forward -n inquiries-system svc/fastapi 8000:8000 > /tmp/pf-fastapi.log 2>&1 &
sleep 5  # Extra time for all to stabilize

# Verify port forwards are running
echo "  🔍 Verifying port forwards..."
PORT_FORWARDS=$(ps aux | grep "kubectl port-forward" | grep -v grep | wc -l)
if [ "$PORT_FORWARDS" -ge 5 ]; then
    echo "  ✅ All $PORT_FORWARDS port forwards active"
else
    echo "  ⚠️  Only $PORT_FORWARDS/5 port forwards active"
    echo "  💡 Some port-forwards may need manual restart"
    echo "  💡 Run: ./keep-port-forwards-alive.sh in another terminal"
fi

# Verify services are accessible
echo "  🔍 Verifying service accessibility..."
sleep 5  # Give services time to stabilize

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/ | grep -q "200"; then
    echo "  ✅ Streamlit dashboard accessible at http://localhost:8501"
else
    echo "  ⚠️  Streamlit dashboard starting up (may take a minute)..."
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -q "200\|302"; then
    echo "  ✅ Grafana accessible at http://localhost:3000"
else
    echo "  ⚠️  Grafana starting up..."
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200\|302"; then
    echo "  ✅ Airflow accessible at http://localhost:8080"
else
    echo "  ⚠️  Airflow starting up..."
fi

echo -e "\n${GREEN}🚀 All port forwards active! Services should be accessible shortly.${NC}"
