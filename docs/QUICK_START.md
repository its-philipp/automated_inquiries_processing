# Quick Start Guide

Get the Inquiry Automation Pipeline up and running in minutes!

## Prerequisites

### For Local Development (Docker)
- Docker & Docker Compose installed
- Python 3.10+ installed
- 8GB+ RAM available
- 10GB+ free disk space

### For Kubernetes Deployment
- Kubernetes cluster (minikube, kind, k3s, or cloud provider)
- kubectl installed
- Helm 3.x installed
- Istio 1.17+ installed (optional, for service mesh)
- 16GB+ RAM available
- 20GB+ free disk space

## 5-Minute Setup

### Option 1: Local Development with Docker

#### Step 1: Run Setup Script

```bash
# Clone the repository (if not already done)
cd automated_inquiries_processing

# Run the automated setup
./scripts/setup.sh
```

This script will:
- Check prerequisites
- Create `.env` file
- Install dependencies
- Generate mock data
- Pull and build Docker images

#### Step 2: Start Services

```bash
docker-compose up -d
```

Wait about 30-60 seconds for all services to initialize.

#### Step 3: Verify Services

Check that all services are running:

```bash
docker-compose ps
```

You should see all services in "Up" state.

#### Step 4: Test the Complete Workflow

```bash
# Submit a test inquiry via API
curl -X POST http://localhost:8000/api/v1/inquiries/submit \
  -H "Content-Type: application/json" \
  -d '{"subject":"Technical login issue","body":"I need help with login problems","sender_email":"user@example.com"}'

# Expected response: Intelligent classification to technical_support category
# Check the response shows correct category and routing

# Test different inquiry types
curl -X POST http://localhost:8000/api/v1/inquiries/submit \
  -H "Content-Type: application/json" \
  -d '{"subject":"Billing question","body":"I have a question about my monthly bill","sender_email":"billing@example.com"}'

# This should route to billing category and finance department
```

### Option 2: Kubernetes with CNCF Tools

#### Step 1: Setup Kubernetes Cluster

```bash
# Option A: Using minikube
minikube start --memory=8192 --cpus=4

# Option B: Using kind
kind create cluster --config kind-config.yaml

# Option C: Using k3s
curl -sfL https://get.k3s.io | sh -
```

#### Step 2: Deploy with CNCF Stack

```bash
# One-command deployment
./k8s/deploy-k8s.sh
```

This script will:
- Install Istio service mesh
- Install ArgoCD for GitOps
- Deploy application with Helm
- Configure service mesh routing
- Set up monitoring

#### Step 3: Verify Kubernetes Deployment

```bash
# Check pods are running
kubectl get pods -n inquiries-system

# Check services
kubectl get svc -n inquiries-system

# Check Istio gateway
kubectl get gateway -n inquiries-system
```

## Step 4: Test the Complete Workflow

### Test BERT Models Locally

```bash
# Test BERT models directly
source .venv/bin/activate
python scripts/test_bert_models.py
```

This will test:
- BERT-based category classification (85%+ accuracy)
- RoBERTa sentiment analysis (85%+ accuracy)
- Model caching and performance
- Fallback mechanisms

### Test API with BERT Models

#### For Docker Deployment

```bash
# Test technical support inquiry
curl -X POST "http://localhost:8000/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Technical issue with login",
    "body": "I cannot log into my account and keep getting error messages. Please help me troubleshoot this issue.",
    "sender_email": "tech@example.com",
    "sender_name": "Tech User"
  }'

# Test billing inquiry
curl -X POST "http://localhost:8000/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Billing question",
    "body": "I was charged twice for my monthly subscription. Can I get a refund?",
    "sender_email": "billing@example.com",
    "sender_name": "Billing User"
  }'

# Test positive sentiment
curl -X POST "http://localhost:8000/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Thank you for excellent service!",
    "body": "I just wanted to say thank you for the amazing customer service. The team was incredibly helpful!",
    "sender_email": "happy@example.com",
    "sender_name": "Happy Customer"
  }'
```

Expected results:
- **Technical inquiry** → `technical_support` category, `negative` sentiment
- **Billing inquiry** → `billing` category, `negative` sentiment  
- **Thank you message** → `technical_support` category, `positive` sentiment

### For Kubernetes Deployment

```bash
# Port forward to access the API
kubectl port-forward -n inquiries-system svc/automated-inquiries-processing 8000:80

# Submit a test inquiry
curl -X POST "http://localhost:8000/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Cannot login to account",
    "body": "I have been trying to log in for the past hour but keep getting an error. This is blocking my work. Please help!",
    "sender_email": "test@example.com",
    "sender_name": "Test User"
  }'
```

You should get a JSON response with classification and routing information.

## Step 5: Access Dashboards

### For Docker Deployment

Open your browser and visit:

- **API Documentation**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501
- **Airflow UI**: http://localhost:8080 (login: admin/admin)
- **MLflow UI**: http://localhost:5000
- **Grafana**: http://localhost:3000 (login: admin/admin)
  - Inquiry Processing Pipeline Overview
  - Model Performance Dashboard  
  - System Health Dashboard
- **Prometheus**: http://localhost:9090

### For Kubernetes Deployment

```bash
# Port forward to access services
kubectl port-forward -n inquiries-system svc/automated-inquiries-processing 8000:80 &
kubectl port-forward -n inquiries-system svc/grafana 3000:80 &
kubectl port-forward -n inquiries-system svc/prometheus-server 9090:80 &
kubectl port-forward -n inquiries-system svc/mlflow 5000:5000 &
kubectl port-forward -n argocd svc/argocd-server 8080:443 &
```

Then visit:

- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (login: admin/admin)
- **Prometheus**: http://localhost:9090
- **MLflow UI**: http://localhost:5000
- **ArgoCD UI**: http://localhost:8080

## Next Steps

### Load Sample Data into Database

```bash
# The setup script already generated data, now ingest it:
docker-compose exec airflow-scheduler airflow dags trigger daily_data_ingestion

# Or manually run the data generator to add more:
python data/generate_mock_data.py
```

### Run Classification Pipeline

```bash
# Trigger the batch classification DAG
docker-compose exec airflow-scheduler airflow dags trigger batch_classify_inquiries
```

### Monitor the System

1. Go to **Streamlit Dashboard** (http://localhost:8501)
2. You should see inquiries, classifications, and routing decisions
3. Refresh the page to see updated statistics

### View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f airflow-scheduler
```

## Common Issues

### Services Won't Start

```bash
# Stop all services
docker-compose down

# Remove volumes (will delete data!)
docker-compose down -v

# Restart
docker-compose up -d
```

### Port Already in Use

If you get "port already allocated" errors:

1. Check what's using the port:
   ```bash
   lsof -i :8000  # or whatever port
   ```

2. Either stop that service or change the port in `docker-compose.yml`

### Models Downloading Slowly

The first run downloads BERT models (~500MB). This is normal and happens only once.

To speed up:
- Ensure good internet connection
- Models are cached in `./models` directory

### Database Connection Errors

#### For Docker Deployment
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

#### For Kubernetes Deployment
```bash
# Check PostgreSQL pod status
kubectl get pods -n inquiries-system | grep postgres

# View PostgreSQL logs
kubectl logs -n inquiries-system deployment/postgresql

# Check PostgreSQL service
kubectl get svc -n inquiries-system | grep postgres
```

### Kubernetes-Specific Issues

#### Pods Not Starting
```bash
# Check pod status and events
kubectl describe pods -n inquiries-system

# Check resource usage
kubectl top pods -n inquiries-system

# Check node resources
kubectl top nodes
```

#### Service Mesh Issues
```bash
# Check Istio sidecar injection
kubectl get pods -n inquiries-system -o jsonpath='{.items[*].spec.containers[*].name}'

# Check Istio configuration
istioctl analyze -n inquiries-system

# Check gateway status
kubectl get gateway -n inquiries-system
```

## Stopping Services

### For Docker Deployment

```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

### For Kubernetes Deployment

```bash
# Delete the application
helm uninstall automated-inquiries-processing -n inquiries-system

# Delete the namespace (removes all resources)
kubectl delete namespace inquiries-system

# Optional: Uninstall ArgoCD
kubectl delete namespace argocd

# Optional: Uninstall Istio
istioctl uninstall --purge
```

## Getting Help

- Check the main [README.md](../README.md)
- View logs: `docker-compose logs -f`
- Check Airflow logs in UI: http://localhost:8080

