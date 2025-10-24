# 🤖 Automated Inquiries Processing Pipeline

A complete MLOps pipeline for automated inquiry processing using Kubernetes, CNCF services, and modern ML practices.

## 🏗️ Architecture

- **Frontend**: Streamlit dashboard for monitoring and analytics
- **API**: FastAPI for REST endpoints
- **ML Pipeline**: Airflow for workflow orchestration
- **Database**: PostgreSQL for data storage
- **Cache**: Redis for session management
- **Monitoring**: Prometheus + Grafana
- **Service Mesh**: Istio for traffic management
- **GitOps**: ArgoCD for continuous deployment

## 🚀 Quick Start

### Prerequisites
- Docker
- Minikube or Kind
- kubectl
- Helm 3

### One-Command Deployment
```bash
./start-services.sh
```

This will:
1. Start Minikube cluster
2. Deploy all CNCF services
3. Initialize database with sample data
4. Start all applications
5. Set up port-forwards

### Access Services
- **Streamlit Dashboard**: http://localhost:8501
- **Grafana Monitoring**: http://localhost:3000 (admin/admin)
- **Airflow DAGs**: http://localhost:8080 (admin/admin)

### Stop Services
```bash
./stop-services.sh
```

## 📁 Project Structure

```
├── k8s/                          # Kubernetes manifests
│   ├── airflow/                  # Airflow deployment files
│   ├── database/                 # Database initialization
│   ├── monitoring/               # Grafana dashboards
│   └── services/                 # Application services
├── src/                          # Source code
│   ├── api/                      # FastAPI application
│   ├── database/                 # Database models
│   ├── models/                   # ML models
│   └── monitoring/               # Monitoring utilities
├── airflow/dags/                 # Airflow DAGs
├── monitoring/                   # Monitoring configurations
├── deployment/                   # Deployment scripts
└── docs/                         # Documentation
```

## 🔄 Available DAGs

1. **batch_classify** - Classify pending inquiries (runs hourly)
2. **daily_ingestion** - Daily data processing (runs at 6 AM)
3. **model_retrain** - Retrain ML models (runs weekly)

## 📊 Sample Data

The system comes with 5 sample inquiries:
- Urgent server issue (high priority)
- Pricing question (sales inquiry)
- Bug report (technical support)
- Feature request (product)
- Billing inquiry (billing)

## 🛠️ Development

### Local Development
```bash
# Start with Docker Compose
docker-compose up -d

# Or use the Kubernetes setup
./start-services.sh
```

### Testing
```bash
# Test all services
./test-services.sh

# Test specific service
kubectl port-forward -n inquiries-system svc/streamlit-dashboard 8501:8501
```

## 📈 Monitoring

- **System Metrics**: Prometheus collects metrics from all services
- **Application Metrics**: Custom dashboards in Grafana
- **Logs**: Available via `kubectl logs`
- **Health Checks**: Built into all services

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`: Airflow database connection

### Helm Values
All services use Helm charts with customizable values in `deployment/terraform/terraform.tfvars`.

## 🚀 Production Deployment

### Using Terraform
```bash
cd deployment/terraform
terraform init
terraform plan
terraform apply
```

### Using ArgoCD
```bash
kubectl apply -f k8s/argocd/application.yaml
```

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Monitoring Guide](docs/MONITORING.md)
- [Quick Start Guide](docs/QUICK_START.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Port conflicts**: Stop existing port-forwards with `pkill -f "kubectl port-forward"`
2. **Image pull errors**: Ensure Docker is running and has internet access
3. **Database connection issues**: Check if PostgreSQL pod is running
4. **Airflow DAGs not showing**: Wait for scheduler to start and check logs

### Getting Help

- Check service logs: `kubectl logs -n <namespace> <pod-name>`
- Verify pod status: `kubectl get pods --all-namespaces`
- Check service endpoints: `kubectl get svc --all-namespaces`

## 🎯 Next Steps

- [ ] Add more ML models
- [ ] Implement real-time streaming
- [ ] Add more monitoring dashboards
- [ ] Implement CI/CD pipeline
- [ ] Add more test coverage