# System Architecture

## Overview

The Inquiry Automation Pipeline is a microservices-based architecture designed for scalability, reliability, and maintainability.

## Architecture Diagram

```
                                    ┌──────────────┐
                                    │   Client     │
                                    │  Inquiries   │
                                    └──────┬───────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                        ▼                  ▼                  ▼
                  ┌──────────┐      ┌──────────┐      ┌──────────┐
                  │   API    │      │  Email   │      │   S3     │
                  │ Endpoint │      │  Server  │      │  Bucket  │
                  └────┬─────┘      └────┬─────┘      └────┬─────┘
                       │                 │                  │
                       └─────────────────┼──────────────────┘
                                         │
                                         ▼
                            ┌────────────────────────┐
                            │   FastAPI Application  │
                            │                        │
                            │  ┌──────────────────┐  │
                            │  │ Text Preprocessor│  │
                            │  └────────┬─────────┘  │
                            │           │            │
                            │  ┌────────▼─────────┐  │
                            │  │   NLP Models     │  │
                            │  │  • Classifier    │  │
                            │  │  • Sentiment     │  │
                            │  │  • Urgency       │  │
                            │  └────────┬─────────┘  │
                            │           │            │
                            │  ┌────────▼─────────┐  │
                            │  │ Routing Engine   │  │
                            │  └────────┬─────────┘  │
                            │           │            │
                            └───────────┼────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
            │  PostgreSQL  │    │   MLflow    │    │ Prometheus  │
            │              │    │             │    │             │
            │ • Inquiries  │    │ • Models    │    │ • Metrics   │
            │ • Predictions│    │ • Experiments│    │ • Alerts    │
            │ • Routing    │    │ • Versions  │    │             │
            └──────┬───────┘    └──────┬──────┘    └──────┬──────┘
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                          ┌────────────▼────────────┐
                          │   Apache Airflow        │
                          │                         │
                          │  DAGs:                  │
                          │  • Data Ingestion       │
                          │  • Batch Classification │
                          │  • Model Retraining     │
                          │  • Data Quality         │
                          └─────────────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                          ▼            ▼            ▼
                    ┌─────────┐  ┌─────────┐  ┌─────────┐
                    │ Grafana │  │Streamlit│  │  Email  │
                    │Dashboard│  │Dashboard│  │ Alerts  │
                    └─────────┘  └─────────┘  └─────────┘
```

## Components

### 1. API Layer (FastAPI)

**Purpose**: HTTP API for inquiry submission and management

**Responsibilities**:
- Receive incoming inquiries
- Validate input data
- Orchestrate ML pipeline
- Return classification results
- Expose metrics endpoint

**Technology**: FastAPI with Uvicorn

**Endpoints**:
- `POST /api/v1/inquiries/submit` - Submit inquiry
- `GET /api/v1/inquiries/{id}` - Get inquiry status
- `POST /api/v1/inquiries/classify` - Classify text
- `GET /api/v1/health` - Health check
- `GET /api/v1/metrics` - Prometheus metrics
- `GET /api/v1/stats` - Statistics

### 2. NLP Models

**Purpose**: Classify and analyze inquiry text

**Components**:

a) **Category Classifier**
   - **Current Implementation**: BERT-based zero-shot classifier (Facebook BART-large-MNLI)
   - **Approach**: Zero-shot classification using natural language inference
   - **Classes**: Technical Support, Billing, Sales, HR, Legal, Product Feedback
   - **Input**: Combined subject + body text
   - **Output**: Category + confidence score (70-97%)
   - **Accuracy**: ~85% on test cases
   - **Fallback**: Keyword-based classifier if BERT fails
   - **Model Size**: ~1.6GB, cached for performance

b) **Sentiment Analyzer**
   - **Current Implementation**: RoBERTa-based sentiment analysis (Cardiff NLP Twitter RoBERTa)
   - **Classes**: Positive, Neutral, Negative
   - **Purpose**: Detect customer satisfaction level
   - **Accuracy**: ~85% on test cases
   - **Fallback**: Keyword-based sentiment detection if RoBERTa fails

c) **Urgency Detector**
   - **Current Implementation**: Mock implementation with random urgency assignment
   - **Levels**: Low, Medium, High, Critical
   - **Future Enhancement**: Rule-based + keyword matching with "urgent", "asap", "critical", etc.

### 2.1. Model Management & Caching

**Purpose**: Efficient loading and caching of BERT models

**Components**:
- **Model Cache**: Singleton pattern for model management
- **Lazy Loading**: Models loaded on first use
- **Memory Management**: ~1.6GB total memory usage
- **Fallback System**: Graceful degradation to keyword-based methods
- **Cache Directories**: Persistent model storage in Docker volumes

**Performance Optimizations**:
- **Model Caching**: Models loaded once and reused
- **Environment Variables**: `TRANSFORMERS_CACHE`, `HF_HOME` for cache paths
- **Device Detection**: Automatic CPU/GPU detection
- **Error Handling**: Robust fallback mechanisms

### 3. Routing Engine

**Purpose**: Route inquiries to appropriate departments

**Logic**:
1. Calculate priority score (urgency + sentiment + category weights)
2. Check escalation rules
3. Map category to department
4. Assign consultant (round-robin, skill-based, or load-balanced)
5. Create routing decision

**Configuration**: `config/routing_rules.yaml`

### 4. Data Layer (PostgreSQL)

**Purpose**: Persistent storage for all data

**Tables**:
- `inquiries` - Raw inquiry data
- `predictions` - Model predictions
- `routing_decisions` - Routing information
- `model_versions` - Model version tracking
- `performance_metrics` - System metrics

**Indexes**: Optimized for common queries (timestamp, category, status)

### 5. MLflow

**Purpose**: Model lifecycle management

**Features**:
- Experiment tracking
- Model registry
- Version control
- Metrics logging
- Artifact storage

**Integration**: All models log to MLflow on training

### 6. Airflow

**Purpose**: Workflow orchestration

**DAGs**:

a) **Daily Data Ingestion** (`@daily`)
   - Fetch new inquiries from sources
   - Validate data quality
   - Store in database
   - Log statistics

b) **Batch Classification** (`@hourly`)
   - Load unprocessed inquiries
   - Run ML pipeline
   - Save predictions and routing
   - Update inquiry status

c) **Model Retraining** (`@weekly`)
   - Check model performance
   - Collect training data
   - Train new model
   - Evaluate and compare
   - Promote if better

### 7. Monitoring Stack

**Prometheus**:
- Scrapes metrics from API
- Stores time-series data
- Evaluates alert rules

**Grafana**:
- Visualizes metrics
- Pre-configured dashboards
- Alert notifications

**Metrics Tracked**:
- API: Request rate, latency, errors
- Models: Inference time, confidence, predictions
- Pipeline: Processing rate, success rate
- Business: Category distribution, escalation rate

### 8. Streamlit Dashboard

**Purpose**: Real-time monitoring UI

**Features**:
- Live inquiry stream
- Classification results
- Routing decisions
- Model performance metrics
- Department distribution
- Priority score analysis

## Data Flow

### Synchronous Flow (API Request)

1. Client sends inquiry to API
2. API validates request
3. Text preprocessor cleans text
4. NLP models run inference (parallel)
5. Routing engine makes decision
6. Results saved to database
7. Metrics recorded to Prometheus
8. Response returned to client

**Latency**: ~500ms-2s depending on text length

### Asynchronous Flow (Batch Processing)

1. Airflow scheduler triggers DAG
2. DAG loads unprocessed inquiries
3. Batch inference on all inquiries
4. Bulk save to database
5. Update processing status

**Throughput**: ~1000 inquiries/hour

### Model Retraining Flow

1. Weekly check of model metrics
2. If performance drops, collect labeled data
3. Train new model version
4. Log to MLflow
5. Evaluate on validation set
6. Compare with production model
7. If better, promote to production
8. Update model_versions table
9. Notify team

## Scaling Considerations

### Horizontal Scaling

- **API**: Scale FastAPI instances behind load balancer
- **Airflow**: Add more workers for parallel task execution
- **Database**: PostgreSQL read replicas for read-heavy workloads

### Vertical Scaling

- **Models**: Use GPU instances for faster inference
- **Database**: Increase instance size for more connections
- **Redis**: Increase memory for larger queues

### Caching

- Model predictions for identical texts (Redis)
- Frequently accessed routing rules
- Model artifacts (local cache)

## Security

### API Security

- Rate limiting (per IP, per user)
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- CORS configuration

### Data Security

- Encryption at rest (database)
- Encryption in transit (HTTPS/TLS)
- PII handling (email anonymization options)
- Audit logging

### Infrastructure Security

- Network isolation (Docker networks, VPC)
- Secrets management (environment variables, AWS Secrets Manager)
- IAM roles (least privilege)
- Security group restrictions

## Deployment

### Local Development

- Docker Compose orchestrates all services
- Volume mounts for live code reloading
- Shared network for inter-service communication

### Kubernetes Deployment (CNCF Stack)

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Istio Service Mesh                    │   │
│  │                                                     │   │
│  │  ┌──────────────┐    ┌──────────────┐              │   │
│  │  │   Gateway    │    │  Virtual     │              │   │
│  │  │              │    │  Services    │              │   │
│  │  └──────────────┘    └──────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Application Namespace                   │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│   │
│  │  │    API       │  │  PostgreSQL  │  │   MLflow    ││   │
│  │  │   Pods       │  │     Pod      │  │    Pod      ││   │
│  │  └──────────────┘  └──────────────┘  └─────────────┘│   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│   │
│  │  │   Airflow    │  │ Prometheus   │  │   Grafana   ││   │
│  │  │   Pods       │  │    Pod       │  │    Pod      ││   │
│  │  └──────────────┘  └──────────────┘  └─────────────┘│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                ArgoCD Namespace                      │   │
│  │                                                     │   │
│  │  ┌──────────────┐    ┌──────────────┐              │   │
│  │  │  ArgoCD      │    │  ArgoCD      │              │   │
│  │  │  Server      │    │  Controller  │              │   │
│  │  └──────────────┘    └──────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**CNCF Tools Integration:**
- **Kubernetes**: Container orchestration and management
- **Helm**: Package management and templating
- **Istio**: Service mesh for traffic management, security, observability
- **ArgoCD**: GitOps continuous deployment
- **Prometheus/Grafana**: Native Kubernetes monitoring

**Service Mesh Features:**
- Traffic routing and load balancing
- mTLS encryption between services
- Observability and distributed tracing
- Security policies and authorization
- Gateway configuration for external access

### Cloud Deployment (AWS)

- ECS for container orchestration
- RDS for PostgreSQL
- S3 for data storage
- ECR for Docker images
- ALB for load balancing
- CloudWatch for logging
- Terraform for infrastructure as code

## GitOps Workflow

### ArgoCD Integration

The system implements GitOps principles using ArgoCD:

1. **Git as Source of Truth**: All configurations stored in Git repository
2. **Automated Deployments**: Changes pushed to Git automatically trigger deployments
3. **Environment Promotion**: Code flows from dev → staging → production
4. **Rollback Capabilities**: Easy rollback to previous versions
5. **Multi-environment Support**: Separate configurations for different environments

### Deployment Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Developer │    │     Git      │    │   ArgoCD    │
│             │    │ Repository   │    │             │
│ 1. Code     │───▶│ 2. Push      │───▶│ 3. Detect   │
│    Changes  │    │   Changes    │    │   Changes   │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Kubernetes  │◀───│   Helm       │◀───│   ArgoCD    │
│ Cluster     │    │ Templates    │    │ Application │
│             │    │              │    │             │
│ 6. Deploy   │    │ 5. Render    │    │ 4. Sync     │
└─────────────┘    └──────────────┘    └─────────────┘
```

## Future Enhancements

1. **Fine-tuned Models**: Replace zero-shot with custom-trained classifiers
2. **A/B Testing**: Compare model versions in production
3. **Auto-scaling**: Dynamic scaling based on load (HPA already implemented)
4. **Multi-language**: Support non-English inquiries
5. **Advanced Routing**: ML-based consultant assignment
6. **Feedback Loop**: Collect corrections and retrain
7. **Real-time Stream Processing**: Kafka for high-volume ingestion
8. **Service Mesh Observability**: Enhanced tracing with Jaeger
9. **Multi-cluster Deployment**: Cross-cluster replication and failover
10. **Advanced Security**: OPA Gatekeeper policies and network policies

