# Intelligent Automation Pipeline with MLOps Governance

An end-to-end production-ready system for automated classification and routing of client inquiries using NLP, orchestrated with Apache Airflow, containerized with Docker, and monitored with Prometheus/Grafana.

## 🎯 Project Overview

This project demonstrates a comprehensive MLOps pipeline that:

- **Classifies** client inquiries using BERT-based NLP models (category, sentiment, urgency)
- **Routes** inquiries to appropriate departments and consultants based on intelligent business rules
- **Orchestrates** data pipelines and model retraining with Apache Airflow (fully functional DAGs)
- **Monitors** system performance and model metrics with real Prometheus metrics and Grafana dashboards
- **Deploys** as containerized microservices with Docker Compose (local) and Kubernetes (cloud)
- **Tracks** model versions and experiments with MLflow
- **Provides** real-time monitoring dashboard with Streamlit

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Inquiries                         │
│                  (Email, Tickets, API)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Text Processor│→│  BERT Models │→│ Routing Engine│      │
│  │              │  │  - Category  │  │              │      │
│  │              │  │  - Sentiment │  │              │      │
│  │              │  │  - Urgency   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │PostgreSQL│   │  MLflow  │   │Prometheus│
    │          │   │          │   │          │
    └──────────┘   └──────────┘   └──────────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
           ┌─────────────────────────┐
           │   Apache Airflow         │
           │  - Data Ingestion        │
           │  - Batch Classification  │
           │  - Model Retraining      │
           └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- 8GB+ RAM recommended
- `uv` for Python dependency management

### Local Development Setup

1. **Clone and setup environment:**

```bash
git clone <repository>
cd automated_inquiries_processing

# Copy environment template
cp env.example .env

# Edit .env with your configuration
nano .env
```

2. **Generate mock data:**

```bash
# Install uv if not already installed
pip install uv

# Sync dependencies
uv sync

# Generate sample data
python data/generate_mock_data.py
```

3. **Start services with Docker Compose:**

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

4. **Access the services:**

- **FastAPI Swagger Docs**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501
- **Airflow UI**: http://localhost:8081 (admin/admin)
- **MLflow UI**: http://localhost:5001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

5. **Test the complete workflow:**

```bash
# Submit an inquiry via API
curl -X POST http://localhost:8000/api/v1/inquiries/submit \
  -H "Content-Type: application/json" \
  -d '{"subject":"Technical login issue","body":"I need help with login problems","sender_email":"user@example.com"}'

# Check processing in Airflow UI
# View metrics in Prometheus: http://localhost:9090
# Monitor in Grafana: http://localhost:3000
```

### Running Without Docker (Development)

1. **Setup virtual environment:**

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies with uv
uv pip install -e .
```

2. **Start PostgreSQL (required):**

```bash
# Using Docker for PostgreSQL only
docker run -d \
  --name inquiry_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=inquiry_automation \
  -p 5432:5432 \
  postgres:15
```

3. **Run the API:**

```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

4. **Run the Streamlit dashboard:**

```bash
source .venv/bin/activate
streamlit run inquiry_monitoring_dashboard.py
```

## 📊 Usage Examples

### Submit an Inquiry via API

```bash
curl -X POST "http://localhost:8000/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "URGENT: Cannot login to my account",
    "body": "I have been trying to log in for the past hour but keep getting an error. This is blocking my work. Please help ASAP!",
    "sender_email": "user@example.com",
    "sender_name": "John Doe"
  }'
```

### Classify Text Without Saving

```bash
curl -X POST "http://localhost:8000/api/v1/inquiries/classify?include_all_scores=true" \
  -H "Content-Type: application/json" \
  -d '"Cannot access my dashboard, getting 500 error"'
```

### Get Inquiry Status

```bash
curl "http://localhost:8000/api/v1/inquiries/{inquiry_id}"
```

### View Statistics

```bash
curl "http://localhost:8000/api/v1/stats"
```

## 🛠️ Technology Stack

### **Machine Learning & NLP**
- **BERT Models**: Facebook BART-large-MNLI for zero-shot classification
- **RoBERTa**: Cardiff NLP Twitter RoBERTa for sentiment analysis
- **Transformers**: HuggingFace transformers library
- **PyTorch**: Deep learning framework for model inference

### **Backend & API**
- **FastAPI**: Modern Python web framework for APIs
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PostgreSQL**: Primary database for inquiries and predictions
- **Redis**: Caching and session storage

### **Orchestration & Workflow**
- **Apache Airflow**: Workflow orchestration and scheduling
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration

### **Monitoring & Observability**
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards
- **MLflow**: Model versioning and experiment tracking
- **Streamlit**: Real-time monitoring dashboard

### **Cloud & Infrastructure**
- **Kubernetes**: Container orchestration
- **Helm**: Kubernetes package manager
- **Istio**: Service mesh for traffic management
- **ArgoCD**: GitOps continuous deployment

## 🔄 Airflow DAGs

The system includes three main DAGs:

### 1. Daily Data Ingestion (`daily_ingestion`)

**Schedule**: Daily @ midnight  
**Purpose**: Fetch and validate new inquiries from data sources

**Tasks**:
- Fetch inquiries from source (S3, API, file system)
- Validate data quality
- Store in PostgreSQL
- Log statistics

### 2. Batch Classification (`batch_classify_inquiries`)

**Schedule**: Hourly  
**Purpose**: Process unclassified inquiries in batches

**Tasks**:
- Load unprocessed inquiries
- Run NLP models (classification, sentiment, urgency)
- Execute routing logic
- Save predictions and routing decisions

### 3. Model Retraining (`model_retraining`)

**Schedule**: Weekly  
**Purpose**: Monitor model performance and retrain if needed

**Tasks**:
- Check model performance metrics
- Collect labeled training data
- Train new model version
- Evaluate against validation set
- Promote to production if better

## 📈 Monitoring & Observability

### Prometheus Metrics

Key metrics tracked:

- **API Metrics**: Request rate, latency, error rate
- **Model Metrics**: Inference time, confidence scores, prediction distribution
- **Pipeline Metrics**: Processing duration, success rate
- **Routing Metrics**: Department distribution, priority scores, escalation rate

### Grafana Dashboards

Pre-configured dashboards with real-time data:

1. **Inquiry Processing Pipeline Overview**: 
   - Inquiry submissions count and processing duration
   - Routing decisions by department (technical_support, finance, sales, hr, legal, product_management)
   - Model inference statistics and real-time processing graphs

2. **Model Performance Dashboard**:
   - BERT model inferences by type (classifier/sentiment/urgency)
   - Sentiment analysis results (positive/neutral/negative distribution)
   - Urgency detection breakdown (critical/high/medium/low)
   - Category classification results and inference rate over time

3. **System Health Dashboard**:
   - API and Prometheus health status monitoring
   - HTTP response code distribution (200/201/4xx/5xx)
   - Service uptime and request rate over time

### Alerts

Configured alerts in `monitoring/prometheus/alerts.yml`:

- High error rate (>5% in 5min)
- High inference latency (>2s p95)
- Low model confidence (<60%)
- High escalation rate (>20%)
- Service down

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_classifier.py

# Run integration tests
pytest tests/integration/
```

## 🔧 Configuration

### Environment Variables

Key configurations in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Model Settings
DEFAULT_CLASSIFIER_MODEL=distilbert-base-uncased
CONFIDENCE_THRESHOLD=0.7

# Airflow
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
```

### Routing Rules

Customize routing logic in `config/routing_rules.yaml`:

```yaml
# Department mapping
category_to_department:
  technical_support: technical_support
  billing: finance
  sales: sales

# Escalation rules
escalation_rules:
  - name: critical_negative
    conditions:
      urgency: [critical]
      sentiment: [negative]
    action:
      department: escalation
      priority_boost: 20
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Infrastructure as Code

Terraform scripts in `deployment/terraform/`:

```bash
cd deployment/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Deploy to AWS
terraform apply
```

**Resources created**:
- ECS Cluster for containerized services
- RDS PostgreSQL instance
- S3 buckets for data and artifacts
- ECR repositories for Docker images
- Application Load Balancer
- CloudWatch for logging
- IAM roles and security groups

#### Deploy to AWS

```bash
# Build and push Docker images
./deployment/scripts/build_push.sh

# Deploy infrastructure
./deployment/scripts/deploy.sh
```

### Kubernetes Deployment (CNCF Stack)

#### Prerequisites

- Kubernetes cluster (1.24+)
- Helm 3.x
- Istio 1.17+
- ArgoCD 2.5+

#### Quick Deploy to Kubernetes

```bash
# Deploy with CNCF tools (Istio, ArgoCD, Helm)
./k8s/deploy-k8s.sh
```

#### Manual Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace inquiries-system

# Install with Helm
helm upgrade --install automated-inquiries-processing ./k8s/helm \
  --namespace inquiries-system \
  --set image.repository=your-registry/automated-inquiries-processing \
  --set image.tag=latest

# Apply Istio configurations
kubectl apply -f k8s/istio/

# Setup ArgoCD for GitOps
kubectl apply -f k8s/argocd/
```

**CNCF Tools Included**:
- **Kubernetes**: Container orchestration
- **Helm**: Package management and templating
- **Istio**: Service mesh for traffic management, security, and observability
- **ArgoCD**: GitOps continuous deployment
- **Prometheus/Grafana**: Monitoring stack (already included)

#### Access Kubernetes Deployment

```bash
# Get service URLs
kubectl get svc -n inquiries-system

# Port forward for local access
kubectl port-forward -n inquiries-system svc/automated-inquiries-processing 8000:80

# Access ArgoCD UI
kubectl port-forward -n argocd svc/argocd-server 8080:443
```

## 🧠 Model Details

### Category Classifier

- **Model**: DistilBERT (zero-shot) → Fine-tuned DistilBERT
- **Categories**: Technical Support, Billing, Sales, HR, Legal, Product Feedback
- **Input**: Combined subject + body text
- **Output**: Category + confidence score

### Sentiment Analyzer

- **Model**: RoBERTa-base (CardiffNLP)
- **Sentiments**: Positive, Neutral, Negative
- **Use Case**: Detect customer satisfaction/frustration

### Urgency Detector

- **Approach**: Rule-based + keyword matching
- **Levels**: Low, Medium, High, Critical
- **Keywords**: "urgent", "asap", "critical", "immediately", etc.
- **Future**: Can be replaced with fine-tuned model

## 📁 Project Structure

```
.
├── src/
│   ├── api/              # FastAPI application
│   ├── models/           # NLP models
│   ├── preprocessing/    # Text processing
│   ├── routing/          # Routing engine
│   ├── database/         # SQLAlchemy models
│   ├── monitoring/       # Prometheus metrics
│   └── training/         # Model training code
├── airflow/
│   ├── dags/             # Airflow DAGs
│   └── plugins/          # Custom operators
├── data/
│   ├── raw/              # Raw data
│   ├── processed/        # Processed data
│   └── labeled/          # Labeled training data
├── k8s/                  # Kubernetes & CNCF tools
│   ├── helm/             # Helm charts
│   ├── istio/            # Istio service mesh config
│   ├── argocd/           # ArgoCD GitOps config
│   └── deploy-k8s.sh     # Kubernetes deployment script
├── monitoring/
│   ├── prometheus/       # Prometheus config
│   └── grafana/          # Grafana dashboards
├── docker/               # Dockerfiles
├── deployment/
│   ├── terraform/        # AWS infrastructure
│   └── scripts/          # Deployment scripts
├── tests/                # Test suite
├── config/               # Configuration files
├── docs/                 # Documentation
├── docker-compose.yml    # Local orchestration
├── pyproject.toml        # Dependencies
└── README.md             # This file
```

## 🔒 Security

- JWT authentication for API (can be enabled)
- Rate limiting on API endpoints
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- Secrets management with environment variables
- HTTPS/TLS in production
- Network isolation with Docker networks

## 🛠️ Troubleshooting

### Common Issues

**1. Docker containers won't start:**
```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose down
docker-compose up -d
```

**2. Database connection errors:**
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U postgres -d inquiry_automation
```

**3. Model download issues:**
```bash
# Models are downloaded on first run
# Ensure sufficient disk space and internet connection
```

**4. Airflow DAGs not appearing:**
```bash
# Restart scheduler
docker-compose restart airflow-scheduler

# Check DAG parse errors in Airflow UI
```

## 📚 Documentation

Additional documentation in `/docs`:

- **ARCHITECTURE.md**: Detailed system architecture
- **API.md**: Complete API reference
- **DEPLOYMENT.md**: Cloud deployment guide
- **MONITORING.md**: Monitoring and alerting guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

Created as a demonstration of MLOps and intelligent automation capabilities.

## 🙏 Acknowledgments

- **HuggingFace Transformers** for BERT and RoBERTa pre-trained models
- **Facebook AI** for BART-large-MNLI zero-shot classification model
- **Cardiff NLP** for Twitter RoBERTa sentiment analysis model
- **Apache Airflow** for workflow orchestration
- **FastAPI** for the API framework
- **Streamlit** for the monitoring dashboard

