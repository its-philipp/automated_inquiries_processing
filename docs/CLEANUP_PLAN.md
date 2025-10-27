# 🧹 Directory Cleanup Plan

## Files to KEEP (Production-Ready)

### **Root Scripts (macOS Primary, Linux Backup)**
- ✅ `start-macos.sh` - PRIMARY macOS startup
- ✅ `start-linux.sh` - BACKUP for Linux
- ✅ `stop.sh` - Stop services
- ✅ `keep-port-forwards-alive.sh` - Port-forward manager

### **Documentation (Keep All)**
- ✅ `README.md`
- ✅ `MACOS_SETUP_GUIDE.md`
- ✅ `CNCF_SERVICES_GUIDE.md`
- ✅ `ARGOCD_DEMO.md`
- ✅ `FINAL_SETUP_SUMMARY.md`
- ✅ `PROJECT_SUMMARY.md`

### **Docker (Keep Only Used)**
- ✅ `docker/airflow-ml.Dockerfile` - Custom Airflow with BERT

### **K8s Manifests (Keep Only Used)**
- ✅ `k8s/airflow/airflow-with-dags-fix.yaml` - PRIMARY Airflow deployment
- ✅ `k8s/argocd/streamlit-gitops.yaml` - ArgoCD app (ACTIVE)
- ✅ `k8s/database/init-database-job.yaml` - DB initialization
- ✅ `k8s/istio/gateway-fix.yaml` - Istio gateway (ACTIVE)
- ✅ `k8s/services/streamlit-dashboard.yaml` - Streamlit deployment
- ✅ `k8s/services/fastapi-simple.yaml` - FastAPI deployment

### **Application Code (Keep All)**
- ✅ `src/` - All source code
- ✅ `airflow/dags/` - All DAGs
- ✅ `inquiry_monitoring_dashboard.py` - Dashboard
- ✅ `config/` - Configuration

---

## Files to DELETE (Obsolete/Duplicate)

### **Duplicate Shell Scripts**
- ❌ `access-services.sh` - Not needed (ports in documentation)
- ❌ `setup-all.sh` - Old setup script
- ❌ `start-services.sh` - Replaced by start-bulletproof
- ❌ `stop-services.sh` - Use stop.sh
- ❌ `test-services.sh` - Functionality in main scripts

### **Old Deployment Scripts**
- ❌ `deployment/` - Entire directory (old Terraform/Docker Compose)
- ❌ `k8s/deploy-k8s.sh` - Functionality in start-bulletproof

### **Duplicate Docker Files**
- ❌ `docker/airflow.Dockerfile` - Use airflow-ml.Dockerfile
- ❌ `docker/api.Dockerfile` - Not used
- ❌ `docker/dashboard.Dockerfile` - Not used
- ❌ `docker/mlflow.Dockerfile` - Not used

### **Obsolete K8s Files**
- ❌ `k8s/airflow/airflow-create-user.yaml` - Logic in startup script
- ❌ `k8s/airflow/airflow-init-job.yaml` - Logic in startup script
- ❌ `k8s/airflow/airflow-setup.yaml` - Old version
- ❌ `k8s/airflow/airflow-simple.yaml` - Old version
- ❌ `k8s/argocd/application.yaml` - Use streamlit-gitops.yaml
- ❌ `k8s/argocd/project.yaml` - Not needed
- ❌ `k8s/argocd/streamlit-app.yaml` - Duplicate
- ❌ `k8s/istio/authorizationpolicy.yaml` - Not used
- ❌ `k8s/istio/destinationrule.yaml` - Not used
- ❌ `k8s/istio/gateway.yaml` - Use gateway-fix.yaml
- ❌ `k8s/istio/virtualservice.yaml` - Replaced by gateway-fix
- ❌ `k8s/services/fastapi-app.yaml` - Use fastapi-simple.yaml
- ❌ `k8s/services/python-app.yaml` - Not used
- ❌ `k8s/helm/` - Charts managed by Helm repos, not local

### **Old Monitoring**
- ❌ `monitoring/` - Using Prometheus Helm chart instead

### **Other**
- ❌ `docker-compose.yml` - Using Kubernetes
- ❌ `scripts/setup.sh` - Old
- ❌ `scripts/test_api.sh` - Old

---

## New Directory Structure

```
automated_inquiries_processing/
├── README.md
├── MACOS_SETUP_GUIDE.md
├── CNCF_SERVICES_GUIDE.md
├── ARGOCD_DEMO.md
├── FINAL_SETUP_SUMMARY.md
├── PROJECT_SUMMARY.md
│
├── scripts/                          # All executable scripts
│   ├── start-macos.sh    # PRIMARY - macOS
│   ├── start-linux.sh          # BACKUP - Linux
│   ├── stop.sh
│   └── keep-port-forwards-alive.sh
│
├── docker/
│   └── airflow-ml.Dockerfile         # Only file we use
│
├── k8s/
│   ├── airflow/
│   │   └── airflow-with-dags-fix.yaml
│   ├── argocd/
│   │   └── streamlit-gitops.yaml
│   ├── database/
│   │   └── init-database-job.yaml
│   ├── istio/
│   │   └── gateway-fix.yaml
│   └── services/
│       ├── streamlit-dashboard.yaml
│       └── fastapi-simple.yaml
│
├── src/                              # Application code
├── airflow/
│   └── dags/
│       ├── batch_classify.py
│       ├── daily_ingestion.py
│       └── model_retrain.py
│
├── config/
│   └── routing_rules.yaml
│
└── inquiry_monitoring_dashboard.py
```

