# Deployment Guide

Complete guide for deploying the Inquiry Automation Pipeline to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Kubernetes Deployment](#kubernetes-deployment)
- [AWS Deployment](#aws-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

#### For Local Development
- **Docker** (20.10+) and Docker Compose (2.0+)
- **Python** 3.10+
- **Git**

#### For Kubernetes Deployment
- **Kubernetes** cluster (1.24+)
- **kubectl** (1.24+)
- **Helm** 3.x
- **Istio** 1.17+
- **ArgoCD** 2.5+ (optional, for GitOps)

#### For AWS Deployment
- **AWS CLI** (for cloud deployment)
- **Terraform** (1.0+) (for infrastructure)

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space
- **CPU**: 4 cores minimum

## Local Development

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd automated_inquiries_processing
   ./scripts/setup.sh
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment:**
   ```bash
   docker-compose ps
   ./scripts/test_api.sh
   ```

### Manual Setup

1. **Environment configuration:**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

2. **Generate sample data:**
   ```bash
   python data/generate_mock_data.py
   ```

3. **Start individual services:**
   ```bash
   # Database only
   docker-compose up -d postgres redis
   
   # API only
   docker-compose up -d api
   
   # All services
   docker-compose up -d
   ```

### Service URLs

- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **Airflow**: http://localhost:8080 (admin/admin)
- **MLflow**: http://localhost:5000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes Cluster Setup:**
   ```bash
   # For local development, you can use:
   # - minikube
   # - kind (Kubernetes in Docker)
   # - k3s
   # - Docker Desktop with Kubernetes enabled
   
   # Example with minikube:
   minikube start --memory=8192 --cpus=4
   ```

2. **Install Required Tools:**
   ```bash
   # Install Helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   
   # Install Istio
   curl -L https://istio.io/downloadIstio | sh -
   export PATH=$PWD/istio-1.17.0/bin:$PATH
   ```

### Quick Deploy with CNCF Tools

```bash
# One-command deployment with all CNCF tools
./k8s/deploy-k8s.sh
```

This script will:
- Install Istio service mesh
- Install ArgoCD for GitOps
- Deploy the application with Helm
- Configure service mesh routing
- Set up monitoring and observability

### Manual Kubernetes Deployment

#### 1. Create Namespace and Install Istio

```bash
# Create namespace
kubectl create namespace inquiries-system

# Install Istio
istioctl install --set values.defaultRevision=default -y
kubectl label namespace inquiries-system istio-injection=enabled
```

#### 2. Deploy with Helm

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Deploy the application
helm upgrade --install automated-inquiries-processing ./k8s/helm \
  --namespace inquiries-system \
  --set image.repository=your-registry/automated-inquiries-processing \
  --set image.tag=latest \
  --set postgresql.enabled=true \
  --set redis.enabled=true \
  --set mlflow.enabled=true \
  --set prometheus.enabled=true \
  --set grafana.enabled=true \
  --set istio.enabled=true \
  --wait
```

#### 3. Apply Istio Configurations

```bash
# Apply service mesh configurations
kubectl apply -f k8s/istio/gateway.yaml
kubectl apply -f k8s/istio/virtualservice.yaml
kubectl apply -f k8s/istio/destinationrule.yaml
kubectl apply -f k8s/istio/authorizationpolicy.yaml
```

#### 4. Setup ArgoCD (Optional)

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Apply ArgoCD application
kubectl apply -f k8s/argocd/project.yaml
kubectl apply -f k8s/argocd/application.yaml
```

### Access Kubernetes Deployment

#### Get Service URLs

```bash
# Get Istio Gateway IP
kubectl get service istio-ingressgateway -n istio-system

# Port forward for local access
kubectl port-forward -n inquiries-system svc/automated-inquiries-processing 8000:80

# Access ArgoCD UI
kubectl port-forward -n argocd svc/argocd-server 8080:443
```

#### Service Endpoints

- **API**: http://inquiries-api.example.com (configure DNS)
- **API Docs**: http://inquiries-api.example.com/docs
- **Health Check**: http://inquiries-api.example.com/api/v1/health
- **Grafana**: `kubectl port-forward -n inquiries-system svc/grafana 3000:80`
- **Prometheus**: `kubectl port-forward -n inquiries-system svc/prometheus-server 9090:80`
- **MLflow**: `kubectl port-forward -n inquiries-system svc/mlflow 5000:5000`
- **ArgoCD**: `kubectl port-forward -n argocd svc/argocd-server 8080:443`

### Kubernetes Configuration

#### Helm Chart Structure

```
k8s/helm/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values
└── templates/
    ├── deployment.yaml     # Application deployment
    ├── service.yaml        # Service definitions
    └── hpa.yaml           # Horizontal Pod Autoscaler
```

#### Key Configuration Options

```yaml
# values.yaml
image:
  repository: your-registry/automated-inquiries-processing
  tag: latest

replicaCount: 3

resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

postgresql:
  enabled: true
  auth:
    postgresPassword: "postgres"
    database: "inquiry_automation"

istio:
  enabled: true
  gateway:
    hosts:
      - inquiries-api.example.com
```

### Service Mesh Features

#### Traffic Management

```yaml
# k8s/istio/virtualservice.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: inquiries-api
spec:
  hosts:
  - inquiries-api.example.com
  gateways:
  - inquiries-gateway
  http:
  - match:
    - uri:
        prefix: /api/v1
    route:
    - destination:
        host: automated-inquiries-processing
        port:
          number: 80
```

#### Security Policies

```yaml
# k8s/istio/authorizationpolicy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: inquiries-api-policy
spec:
  selector:
    matchLabels:
      app: automated-inquiries-processing
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"]
```

### Monitoring and Observability

#### Prometheus Configuration

```yaml
# Prometheus scraping configuration
prometheus:
  enabled: true
  server:
    persistentVolume:
      enabled: true
      size: 10Gi
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
```

#### Grafana Dashboards

```yaml
# Grafana configuration
grafana:
  enabled: true
  adminPassword: "admin"
  persistence:
    enabled: true
    size: 5Gi
  dashboards:
    default:
      kubernetes-cluster-monitoring:
        gnetId: 7249
        revision: 1
        datasource: Prometheus
```

### GitOps with ArgoCD

#### ArgoCD Application

```yaml
# k8s/argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: inquiries-automation
  namespace: argocd
spec:
  project: inquiries-project
  source:
    repoURL: https://github.com/your-org/automated-inquiries-processing
    targetRevision: HEAD
    path: k8s/helm
  destination:
    server: https://kubernetes.default.svc
    namespace: inquiries-system
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Troubleshooting Kubernetes Deployment

#### Common Issues

1. **Pods Not Starting:**
   ```bash
   # Check pod status
   kubectl get pods -n inquiries-system
   
   # Check pod logs
   kubectl logs -n inquiries-system deployment/automated-inquiries-processing
   ```

2. **Service Mesh Issues:**
   ```bash
   # Check Istio sidecar injection
   kubectl get pods -n inquiries-system -o jsonpath='{.items[*].spec.containers[*].name}'
   
   # Check Istio configuration
   istioctl analyze -n inquiries-system
   ```

3. **ArgoCD Sync Issues:**
   ```bash
   # Check ArgoCD application status
   kubectl get applications -n argocd
   
   # Check ArgoCD logs
   kubectl logs -n argocd deployment/argocd-application-controller
   ```

## AWS Deployment

### Prerequisites

1. **AWS Account Setup:**
   ```bash
   aws configure
   # Enter your Access Key ID, Secret Key, and Region
   ```

2. **Required AWS Services:**
   - ECS (Elastic Container Service)
   - RDS (PostgreSQL)
   - ECR (Elastic Container Registry)
   - S3 (Storage)
   - ALB (Application Load Balancer)
   - CloudWatch (Logging)

3. **IAM Permissions:**
   Your AWS user needs permissions for:
   - ECS, RDS, ECR, S3, ALB, CloudWatch
   - VPC, Security Groups, IAM roles

### Automated Deployment

1. **Build and push images:**
   ```bash
   ./deployment/scripts/build_push.sh
   ```

2. **Deploy infrastructure:**
   ```bash
   ./deployment/scripts/deploy.sh
   ```

3. **Verify deployment:**
   ```bash
   # Get ALB DNS name from Terraform output
   terraform output -raw alb_dns_name
   
   # Test the API
   curl http://<ALB_DNS>/api/v1/health
   ```

### Manual Deployment Steps

#### 1. Infrastructure Setup

```bash
cd deployment/terraform

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region = "us-east-1"
environment = "prod"
project_name = "inquiry-automation"
db_password = "your-secure-password"
EOF

# Deploy infrastructure
terraform init
terraform plan
terraform apply
```

#### 2. Container Images

```bash
# Build and push images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -f docker/api.Dockerfile -t inquiry-automation/api .
docker tag inquiry-automation/api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/inquiry-automation/api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/inquiry-automation/api:latest
```

#### 3. ECS Service Configuration

Create ECS task definition and service:

```json
{
  "family": "inquiry-automation-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/inquiry-automation/api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:password@<rds-endpoint>:5432/inquiry_automation"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/inquiry-automation",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Environment Configuration

#### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:password@rds-endpoint:5432/inquiry_automation

# MLflow
MLFLOW_TRACKING_URI=http://mlflow-service:5000

# AWS
AWS_REGION=us-east-1
S3_BUCKET_NAME=inquiry-automation-data

# Model Configuration
DEFAULT_CLASSIFIER_MODEL=distilbert-base-uncased
CONFIDENCE_THRESHOLD=0.7
```

#### Secrets Management

For production, use AWS Secrets Manager:

```bash
# Store database password
aws secretsmanager create-secret \
  --name "inquiry-automation/db-password" \
  --description "Database password" \
  --secret-string "your-secure-password"

# Store in ECS task definition
"secrets": [
  {
    "name": "DATABASE_URL",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:account:secret:inquiry-automation/db-password"
  }
]
```

## Production Considerations

### Security

1. **Network Security:**
   - Use private subnets for databases
   - Configure security groups restrictively
   - Enable VPC Flow Logs

2. **Data Encryption:**
   - Enable RDS encryption at rest
   - Use HTTPS/TLS for all communications
   - Encrypt S3 buckets

3. **Access Control:**
   - Implement IAM roles with least privilege
   - Use AWS Cognito for user authentication
   - Enable MFA for administrative access

### Performance

1. **Auto Scaling:**
   ```bash
   # ECS Auto Scaling
   aws application-autoscaling register-scalable-target \
     --service-namespace ecs \
     --resource-id service/inquiry-automation-cluster/inquiry-automation-api \
     --scalable-dimension ecs:service:DesiredCount \
     --min-capacity 2 \
     --max-capacity 10
   ```

2. **Caching:**
   - Use ElastiCache Redis for session storage
   - Implement API response caching
   - Use CloudFront for static assets

3. **Database Optimization:**
   - Enable RDS Performance Insights
   - Use read replicas for read-heavy workloads
   - Implement connection pooling

### Monitoring

1. **CloudWatch Alarms:**
   ```bash
   # High CPU utilization
   aws cloudwatch put-metric-alarm \
     --alarm-name "High CPU Usage" \
     --alarm-description "Alert when CPU exceeds 80%" \
     --metric-name CPUUtilization \
     --namespace AWS/ECS \
     --statistic Average \
     --period 300 \
     --threshold 80 \
     --comparison-operator GreaterThanThreshold
   ```

2. **Log Aggregation:**
   - Use CloudWatch Logs
   - Implement structured logging
   - Set up log retention policies

3. **Health Checks:**
   - Configure ALB health checks
   - Implement application health endpoints
   - Set up automated recovery

## Monitoring Setup

### Prometheus & Grafana

1. **Install Prometheus:**
   ```bash
   # Using Helm
   helm install prometheus prometheus-community/kube-prometheus-stack
   ```

2. **Configure Grafana:**
   - Import pre-configured dashboards
   - Set up data sources
   - Configure alerting rules

### Application Monitoring

1. **Custom Metrics:**
   - Model inference latency
   - Classification accuracy
   - Pipeline throughput

2. **Business Metrics:**
   - Inquiry processing rate
   - Escalation rate
   - Department distribution

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check Docker logs
docker-compose logs -f api

# Check resource usage
docker stats

# Restart services
docker-compose restart
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
docker-compose exec api python -c "
from src.database.connection import get_db_manager
db = get_db_manager()
print('Database connection test')
"
```

#### 3. Model Loading Errors

```bash
# Check model downloads
docker-compose exec api ls -la models/

# Clear model cache
docker-compose exec api rm -rf models/*
```

#### 4. Airflow DAG Issues

```bash
# Check DAG syntax
docker-compose exec airflow-webserver python -c "
from airflow.models import DagBag
dag_bag = DagBag()
print('DAGs loaded:', len(dag_bag.dags))
"
```

### Performance Issues

#### 1. Slow Model Inference

- Increase ECS task CPU/memory
- Use GPU-enabled instances
- Implement model caching

#### 2. Database Performance

- Enable RDS Performance Insights
- Add database indexes
- Use connection pooling

#### 3. High Memory Usage

- Monitor container memory usage
- Implement model unloading
- Use memory-efficient models

### Logging and Debugging

#### 1. Application Logs

```bash
# View API logs
docker-compose logs -f api

# View Airflow logs
docker-compose logs -f airflow-scheduler
```

#### 2. Database Logs

```bash
# PostgreSQL logs
docker-compose logs -f postgres

# Connect to database
docker-compose exec postgres psql -U postgres -d inquiry_automation
```

#### 3. CloudWatch Logs

```bash
# View ECS logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/inquiry-automation"

# Stream logs
aws logs tail /ecs/inquiry-automation --follow
```

## Rollback Procedures

### Application Rollback

1. **ECS Service Rollback:**
   ```bash
   # Update service to previous task definition
   aws ecs update-service \
     --cluster inquiry-automation-cluster \
     --service inquiry-automation-api \
     --task-definition inquiry-automation-api:PREVIOUS_REVISION
   ```

2. **Database Rollback:**
   ```bash
   # Restore from snapshot
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier inquiry-automation-postgres-rolled-back \
     --db-snapshot-identifier inquiry-automation-snapshot-before-deployment
   ```

### Infrastructure Rollback

```bash
# Terraform rollback
cd deployment/terraform
terraform plan -var-file="terraform.tfvars.backup"
terraform apply -var-file="terraform.tfvars.backup"
```

## Backup and Recovery

### Database Backups

```bash
# Automated backups (RDS)
# Enable automated backups in Terraform:
resource "aws_db_instance" "postgres" {
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
}
```

### Data Backups

```bash
# S3 bucket versioning
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

## Support and Maintenance

### Regular Maintenance

1. **Weekly:**
   - Review system metrics
   - Check model performance
   - Update dependencies

2. **Monthly:**
   - Security patches
   - Database optimization
   - Capacity planning

3. **Quarterly:**
   - Disaster recovery testing
   - Security audits
   - Performance reviews

### Contact Information

- **Development Team**: dev-team@company.com
- **DevOps Team**: devops@company.com
- **Emergency**: +1-XXX-XXX-XXXX

## Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform Documentation](https://www.terraform.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
