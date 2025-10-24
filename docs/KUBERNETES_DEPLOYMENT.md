# Kubernetes Deployment Guide with CNCF Services

This guide provides multiple options for deploying the Automated Inquiries Processing system to Kubernetes with CNCF services, **without requiring any cloud provider**.

## 🎯 Deployment Options

### Option 1: Pure Terraform + Kubernetes (Recommended)
**Best for**: Production-like environments, infrastructure as code, team collaboration

**What you get**:
- ✅ Complete infrastructure as code with Terraform
- ✅ All CNCF services (Istio, ArgoCD, Prometheus, Grafana, Jaeger)
- ✅ Works with any Kubernetes cluster (local, on-prem, cloud)
- ✅ GitOps workflow with ArgoCD
- ✅ Service mesh with Istio
- ✅ Comprehensive monitoring stack

**Prerequisites**:
- Kubernetes cluster (minikube, kind, k3s, or any cloud K8s)
- Terraform
- kubectl
- Helm

**Quick Start**:
```bash
# 1. Setup your Kubernetes cluster (choose one)
minikube start --memory=8192 --cpus=4
# OR
kind create cluster --config=kind-config.yaml
# OR
k3s server &

# 2. Deploy with Terraform
./deployment/terraform-deploy.sh
```

### Option 2: Local Kubernetes Setup
**Best for**: Development, testing, learning

**What you get**:
- ✅ Local Kubernetes cluster setup
- ✅ All CNCF services installed
- ✅ Automated deployment scripts
- ✅ Perfect for development

**Prerequisites**:
- kubectl
- Helm
- Istio CLI
- Minikube OR Kind

**Quick Start**:
```bash
# Choose your Kubernetes type
export K8S_TYPE=minikube  # or kind
./deployment/local-k8s-setup.sh
```

### Option 3: Docker Compose + CNCF Simulation
**Best for**: Quick testing, demos, when you don't want to manage Kubernetes

**What you get**:
- ✅ All services running in Docker
- ✅ CNCF services simulation (Istio Gateway, ArgoCD UI mock)
- ✅ Monitoring stack (Prometheus, Grafana, Jaeger)
- ✅ Log aggregation (Fluentd, Elasticsearch, Kibana)

**Prerequisites**:
- Docker
- Docker Compose

**Quick Start**:
```bash
./deployment/docker-compose-cncf.sh
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CNCF Services Layer                      │
├─────────────────────────────────────────────────────────────┤
│  ArgoCD (GitOps)  │  Istio (Service Mesh)  │  Monitoring    │
│                   │                        │  Stack        │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  FastAPI API  │  Airflow  │  MLflow  │  Dashboard         │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Prometheus  │  Grafana         │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Detailed Setup Instructions

### Prerequisites Installation

#### 1. Install Kubernetes Tools
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Istio CLI
curl -L https://istio.io/downloadIstio | sh -
sudo mv istio-*/bin/istioctl /usr/local/bin/
```

#### 2. Install Terraform
```bash
# Using package manager
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

#### 3. Setup Local Kubernetes (Choose One)

**Minikube**:
```bash
# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --memory=8192 --cpus=4 --disk-size=20g
minikube addons enable ingress
minikube addons enable metrics-server
```

**Kind**:
```bash
# Install Kind
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --config=kind-config.yaml
```

**K3s**:
```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Configure kubectl
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
```

## 🚀 Deployment Steps

### Option 1: Terraform Deployment (Recommended)

1. **Prepare Configuration**:
```bash
cd deployment/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if needed
```

2. **Deploy**:
```bash
# From project root
./deployment/terraform-deploy.sh
```

3. **Access Services**:
- API: http://localhost:30080
- Grafana: http://localhost:30001 (admin/admin)
- Prometheus: http://localhost:30002
- ArgoCD: http://localhost:30000
- MLflow: http://localhost:30006
- Airflow: http://localhost:30007

### Option 2: Local Kubernetes Setup

1. **Deploy**:
```bash
# Set your preferred Kubernetes type
export K8S_TYPE=minikube  # or kind
./deployment/local-k8s-setup.sh
```

2. **Access Services**:
- Minikube: Use `minikube ip` to get the IP
- Kind: Use localhost with the configured ports

### Option 3: Docker Compose

1. **Deploy**:
```bash
./deployment/docker-compose-cncf.sh
```

2. **Access Services**:
- All services available on localhost with their respective ports

## 🔧 Configuration

### Environment Variables
```bash
# Project configuration
export PROJECT_NAME="inquiry-automation"
export ENVIRONMENT="dev"
export NAMESPACE="inquiries-system"

# Kubernetes configuration
export K8S_TYPE="minikube"  # minikube, kind, k3s
export IMAGE_TAG="latest"
export REGISTRY="localhost:5000"
```

### Customizing Helm Values
Edit `k8s/helm/values.yaml` to customize:
- Resource limits and requests
- Replica counts
- Service configurations
- Environment variables

### Monitoring Configuration
- **Grafana Dashboards**: Pre-configured in `monitoring/grafana/dashboards/`
- **Prometheus Alerts**: Configured in `monitoring/prometheus/alerts.yml`
- **Service Discovery**: Automatic with Prometheus Operator

## 🔍 Troubleshooting

### Common Issues

1. **Cluster Not Ready**:
```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

2. **Istio Installation Issues**:
```bash
istioctl verify-install
kubectl get pods -n istio-system
```

3. **ArgoCD Sync Issues**:
```bash
kubectl get applications -n argocd
kubectl describe application automated-inquiries-processing -n argocd
```

4. **Resource Constraints**:
```bash
kubectl top nodes
kubectl top pods --all-namespaces
```

### Logs and Debugging

```bash
# Application logs
kubectl logs -f deployment/automated-inquiries-processing -n inquiries-system

# Istio logs
kubectl logs -f deployment/istiod -n istio-system

# ArgoCD logs
kubectl logs -f deployment/argocd-server -n argocd

# Prometheus logs
kubectl logs -f deployment/prometheus-server -n monitoring
```

## 📊 Monitoring and Observability

### Available Dashboards
- **Inquiry Data Overview**: System metrics and inquiry processing stats
- **Pipeline Overview**: Airflow DAG execution and performance
- **Model Performance**: ML model metrics and accuracy
- **System Health**: Infrastructure and service health

### Tracing
- **Jaeger**: Distributed tracing for request flows
- **OpenTelemetry**: Metrics and traces collection

### Logging
- **Fluentd**: Log aggregation and forwarding
- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log visualization and analysis

## 🔄 GitOps Workflow

### ArgoCD Configuration
1. **Application Sync**: Automatic sync from Git repository
2. **Health Monitoring**: Continuous health checks
3. **Rollback**: Easy rollback to previous versions
4. **Multi-Environment**: Support for dev/staging/production

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Deploy to Kubernetes
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy with Terraform
        run: ./deployment/terraform-deploy.sh
```

## 🛑 Cleanup

### Terraform Cleanup
```bash
cd deployment/terraform
terraform destroy
```

### Manual Cleanup
```bash
# Delete namespaces
kubectl delete namespace inquiries-system argocd istio-system monitoring

# Delete Helm releases
helm uninstall automated-inquiries-processing -n inquiries-system
helm uninstall argocd -n argocd
helm uninstall istio-base istiod istio-ingressgateway -n istio-system
helm uninstall prometheus -n monitoring
```

## 📚 Next Steps

1. **Production Setup**:
   - Configure SSL certificates
   - Set up external load balancer
   - Configure backup strategies
   - Set up monitoring alerts

2. **CI/CD Pipeline**:
   - Integrate with GitHub Actions/GitLab CI
   - Set up automated testing
   - Configure deployment strategies

3. **Security**:
   - Enable Istio mTLS
   - Configure RBAC
   - Set up network policies
   - Implement secrets management

4. **Scaling**:
   - Configure HPA (Horizontal Pod Autoscaler)
   - Set up cluster autoscaling
   - Optimize resource requests/limits

## 🆘 Support

- **Documentation**: Check `docs/` directory for detailed documentation
- **Issues**: Create GitHub issues for bugs or feature requests
- **Community**: Join our community discussions

---

**Happy Deploying! 🚀**
