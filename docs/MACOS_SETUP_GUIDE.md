# 🍎 macOS Setup Guide - Automated Inquiries Processing

## 🎉 What We Fixed

### Original Issues:
1. ❌ Linux-specific scripts (wouldn't run on macOS)
2. ❌ Port-forwards kept dying
3. ❌ Airflow DAGs had import errors
4. ❌ OOMKilled errors due to BERT models

### Solutions Implemented:
1. ✅ Created `start-macos.sh` for macOS
2. ✅ Built custom Airflow image with BERT models (`airflow-ml:2.7.3`)
3. ✅ Increased memory limits to 2GB (was 1GB)
4. ✅ Fixed DAG symlink issues with init containers
5. ✅ Added robust port-forwarding with logging

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** with **8GB+ RAM allocated**
- **macOS 11.0+** (Big Sur or later)
- **10GB free disk space**

### One-Command Deployment
```bash
cd /Users/philipptrinh/workspace/playground/automated_inquiries_processing
./start-macos.sh
```

This will:
1. ✅ Check and install prerequisites (Kind, Helm, kubectl)
2. ✅ Build custom Airflow image with BERT models (takes 5-10 min first time)
3. ✅ Create Kind cluster with optimized settings
4. ✅ Deploy all CNCF services (Istio, ArgoCD, Prometheus/Grafana)
5. ✅ Deploy core infrastructure (PostgreSQL, Redis)
6. ✅ Deploy Airflow with 3 BERT-powered DAGs
7. ✅ Deploy Streamlit dashboard and FastAPI
8. ✅ Set up port-forwarding with logging

---

## 🌐 Access Your Services

Once deployed:

- **Airflow (3 BERT DAGs)**: http://localhost:8080/home
  - Username: `admin`
  - Password: `admin`
  
- **Streamlit Dashboard**: http://localhost:8501
  
- **Grafana Monitoring**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
  
- **ArgoCD GitOps**: https://localhost:30009
  - Username: `admin`
  - Password: Get with `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

---

## 🤖 Airflow DAGs with BERT Models

All 3 DAGs are now working with **real BERT models**:

### 1. **batch_classify_inquiries** (Runs hourly)
   - **BERT Model**: `facebook/bart-large-mnli` (1.6GB)
   - **Sentiment Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest` (500MB)
   - Loads unprocessed inquiries
   - Classifies using BERT (with rule-based fallback)
   - Routes to departments
   - Saves predictions to PostgreSQL

### 2. **daily_data_ingestion** (Runs daily at 6 AM)
   - Fetches new inquiries (generates mock data for demo)
   - Validates data quality
   - Stores in database
   - Logs statistics

### 3. **model_retraining** (Runs weekly)
   - Checks model performance metrics
   - Collects training data
   - Triggers retraining if needed
   - Evaluates and promotes models

---

## ⚠️ Important: Docker Desktop Memory

### Why Port-Forwards Were Dying:

The issue was **OOMKilled** (Out of Memory):
- BERT models need ~2GB RAM
- With all CNCF services, the cluster was using 4.6GB/7.6GB
- Airflow pods had only 1GB limit → **OOMKilled**
- When pods restart, port-forwards die

### Solution:

**Increased Airflow memory limits to 2GB** and allocated more Docker resources.

### Check Your Docker Desktop Settings:

1. Open **Docker Desktop**
2. Go to **Settings → Resources**
3. Set **Memory** to at least **8GB** (10GB recommended)
4. Set **CPUs** to at least **4**
5. Click **Apply & Restart**

---

## 🔧 Troubleshooting

### Port-Forwards Keep Dying

**Solution 1**: Use the keep-alive script
```bash
./keep-port-forwards-alive.sh
```
This monitors port-forwards and restarts them automatically.

**Solution 2**: Manual restart
```bash
# Kill all port-forwards
pkill -f "kubectl port-forward"

# Restart them
kubectl port-forward -n inquiries-system svc/streamlit-dashboard 8501:8501 &
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 &
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080 &
kubectl port-forward -n argocd svc/argocd-server 30009:443 &
```

**Check logs**:
```bash
tail -f /tmp/pf-airflow.log
tail -f /tmp/pf-streamlit.log
```

### Airflow Shows "Invalid Login"

The admin user needs to be created. Run:
```bash
kubectl exec -n airflow deployment/airflow-webserver -- airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin
```

### No DAGs Showing in Airflow

1. Wait 30 seconds for DAGs to load
2. Check import errors:
```bash
kubectl exec -n airflow deployment/airflow-scheduler -- airflow dags list-import-errors
```
3. Verify ConfigMap:
```bash
kubectl get configmap airflow-dags -n airflow
```

### OOMKilled Errors

Increase Docker Desktop memory:
1. Docker Desktop → Settings → Resources
2. Memory → 10GB or more
3. Apply & Restart

Or reduce running services:
```bash
# Stop ArgoCD if not needed
helm uninstall argocd -n argocd
```

---

## 🛑 Stop Everything

```bash
./stop.sh
```

Or manually:
```bash
# Delete the entire cluster
kind delete cluster --name cncf-cluster

# Kill port-forwards
pkill -f "kubectl port-forward"
```

---

## 📊 Resource Usage

Expected resource usage with all services:
- **Memory**: 4-6GB
- **CPU**: 2-4 cores
- **Disk**: 8-10GB

Services and their memory footprint:
- Airflow (2 pods): 2GB each = **4GB**
- Prometheus/Grafana: **~1.5GB**
- Istio: **~500MB**
- PostgreSQL/Redis: **~400MB**
- Streamlit/FastAPI: **~300MB**
- ArgoCD: **~500MB**

**Total: ~7GB required**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      macOS (Docker Desktop)             │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Kind Cluster (cncf-cluster)      │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │  CNCF Services              │ │ │
│  │  │  • Istio Service Mesh       │ │ │
│  │  │  • ArgoCD GitOps            │ │ │
│  │  │  • Prometheus + Grafana     │ │ │
│  │  └─────────────────────────────┘ │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │  Core Services              │ │ │
│  │  │  • PostgreSQL               │ │ │
│  │  │  • Redis                    │ │ │
│  │  │  • Airflow (w/ BERT)        │ │ │
│  │  └─────────────────────────────┘ │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │  Applications               │ │ │
│  │  │  • Streamlit Dashboard      │ │ │
│  │  │  • FastAPI Backend          │ │ │
│  │  └─────────────────────────────┘ │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
           ↓ Port Forwarding
    http://localhost:8501 (Streamlit)
    http://localhost:8080 (Airflow)
    http://localhost:3000 (Grafana)
```

---

## 📝 Files Created for macOS

1. **start-macos.sh** - Main startup script
2. **docker/airflow-ml.Dockerfile** - Custom Airflow with BERT
3. **k8s/airflow/airflow-with-dags-fix.yaml** - Optimized Airflow deployment
4. **keep-port-forwards-alive.sh** - Port-forward monitoring
5. **airflow/dags/batch_classify.py** - Updated to use BERT with fallback

---

## 🎯 Next Steps

After successful deployment:

1. **Test Airflow DAGs**:
   - Go to http://localhost:8080/home
   - Click on `batch_classify_inquiries`
   - Click the Play button (▶️) to trigger a manual run
   - Watch the Graph or Grid view

2. **Check Streamlit Dashboard**:
   - Go to http://localhost:8501
   - View inquiry statistics and visualizations

3. **Explore Grafana**:
   - Go to http://localhost:3000
   - Explore pre-configured dashboards

4. **Monitor with ArgoCD**:
   - Go to https://localhost:30009
   - View GitOps deployments

---

## 💡 Tips

### Speed Up Future Startups

The custom Airflow image persists, so subsequent runs are faster:
- **First run**: ~15-20 minutes (builds image)
- **Subsequent runs**: ~5-10 minutes (uses cached image)

### Keep Port-Forwards Running

If you're working for extended periods:
```bash
# Run in a separate terminal
./keep-port-forwards-alive.sh
```

This will monitor and auto-restart port-forwards if they die.

### View Logs

```bash
# Airflow scheduler
kubectl logs -f deployment/airflow-scheduler -n airflow

# Airflow webserver
kubectl logs -f deployment/airflow-webserver -n airflow

# Streamlit
kubectl logs -f deployment/streamlit-dashboard -n inquiries-system

# Port-forward logs
tail -f /tmp/pf-airflow.log
```

---

## ✅ Verification Checklist

After running the script, verify:

- [ ] All pods are running: `kubectl get pods --all-namespaces`
- [ ] 4 port-forwards active: `ps aux | grep "kubectl port-forward" | grep -v grep | wc -l`
- [ ] Airflow accessible: `curl -I http://localhost:8080/`
- [ ] 3 DAGs visible in Airflow UI
- [ ] Streamlit dashboard loads: `curl -I http://localhost:8501/`
- [ ] No OOMKilled pods: `kubectl get events --all-namespaces | grep OOM`

---

## 🆘 Getting Help

If something goes wrong:

1. **Check pod status**: `kubectl get pods --all-namespaces`
2. **View logs**: `kubectl logs -n <namespace> <pod-name>`
3. **Check resources**: `docker stats`
4. **View events**: `kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -20`
5. **Restart everything**: `kind delete cluster --name cncf-cluster && ./start-macos.sh`

---

**Enjoy your BERT-powered inquiry automation pipeline! 🚀**

