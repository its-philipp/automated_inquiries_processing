# 🌐 CNCF Services Guide - How to Use Helm, ArgoCD & Istio

## Overview

Your automated inquiries processing system includes **3 powerful CNCF tools** that provide enterprise-grade capabilities. Here's how to use them!

---

## 🎯 **1. Helm - Kubernetes Package Manager**

### **What It Does:**
Helm is like **npm for Kubernetes** - it manages complex application deployments with versioning and rollbacks.

### **What You Deployed:**
- ✅ **Istio** (Service Mesh) - v1.27.3
- ✅ **ArgoCD** (GitOps) - v3.1.9  
- ✅ **Prometheus Stack** (Monitoring) - v0.86.1

### **Useful Commands:**

```bash
# List all installed charts
helm list --all-namespaces

# See chart details
helm status prometheus -n monitoring

# See configuration values
helm get values prometheus -n monitoring

# Upgrade a chart
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=newpassword \
  --reuse-values

# Rollback if something breaks
helm rollback prometheus -n monitoring
```

### **Real-World Use Case:**
Want to change Grafana settings? Use Helm to upgrade without manually editing YAMLs:
```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.service.nodePort=30002 \
  --reuse-values
```

---

## 🔄 **2. ArgoCD - GitOps Continuous Deployment**

### **What It Does:**
ArgoCD **automatically syncs** your Kubernetes cluster with Git repositories. Push code → ArgoCD deploys it automatically!

### **Access ArgoCD UI:**

**URL:** https://localhost:30009  
**Username:** `admin`  
**Password:** 
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Current password: `ZTfydHTqtQmRjPso`

### **Quick Start:**

#### **1. Open the UI:**
```bash
open https://localhost:30009
# Accept the self-signed certificate warning
```

#### **2. Create Your First App:**

In the ArgoCD UI:
1. Click **"+ NEW APP"**
2. Fill in:
   - **Application Name**: `my-app`
   - **Project**: `default`
   - **Sync Policy**: `Automatic`
   - **Repository URL**: `https://github.com/yourusername/your-repo`
   - **Path**: `k8s/` (path to manifests)
   - **Cluster**: `https://kubernetes.default.svc`
   - **Namespace**: `default`
3. Click **CREATE**

Or via CLI:
```bash
kubectl apply -f k8s/argocd/application.yaml
```

### **What Happens:**
- ArgoCD clones your Git repo
- Applies all YAML files from specified path
- Monitors for Git changes every 3 minutes
- Auto-deploys when you push updates
- Shows visual graph of your app's resources

### **Practical Example - GitOps Workflow:**

```bash
# 1. Make a change to your app
vim k8s/services/streamlit-dashboard.yaml
# Change replicas: 1 → 2

# 2. Commit and push
git add .
git commit -m "Scale Streamlit to 2 replicas"
git push

# 3. ArgoCD detects change (within 3 min)
# 4. Automatically applies the change
# 5. You see the new pod in ArgoCD UI

# Want to rollback? Just revert the Git commit!
git revert HEAD
git push
# ArgoCD automatically reverts the cluster
```

### **Benefits:**
- ✅ **Git as single source of truth**
- ✅ **Full audit trail** (all changes in Git history)
- ✅ **Easy disaster recovery** (redeploy entire cluster from Git)
- ✅ **Declarative deployments** (no imperative kubectl commands)
- ✅ **Multi-cluster management** (deploy to dev/staging/prod from one UI)

---

## 🌐 **3. Istio - Service Mesh**

### **What It Does:**
Istio manages **communication between microservices** with:
- **Traffic Management**: Intelligent routing, load balancing
- **Security**: Automatic TLS between services
- **Observability**: Metrics for every request
- **Resilience**: Retries, circuit breakers, timeouts

### **What's Deployed:**

```
✅ Istio Control Plane (istiod)
✅ Istio Ingress Gateway (port 30080)
✅ Gateway + VirtualService for your apps
```

### **How to Use:**

#### **1. View Istio Resources:**
```bash
# See Istio components
kubectl get pods -n istio-system

# See gateways
kubectl get gateway -n inquiries-system

# See virtual services (routing rules)
kubectl get virtualservice -n inquiries-system
```

#### **2. Access Through Istio Gateway:**

Your apps are accessible through Istio at:
```bash
# Istio Gateway
http://localhost:30080

# Or via NodePort
kubectl get svc istio-ingressgateway -n istio-system
```

#### **3. Practical Example - Traffic Splitting (A/B Testing):**

Deploy two versions and split traffic 50/50:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: streamlit-ab-test
  namespace: inquiries-system
spec:
  hosts:
  - streamlit-dashboard
  http:
  - match:
    - headers:
        user-type:
          exact: beta
    route:
    - destination:
        host: streamlit-dashboard
        subset: v2
  - route:
    - destination:
        host: streamlit-dashboard
        subset: v1
      weight: 50
    - destination:
        host: streamlit-dashboard
        subset: v2
      weight: 50
```

#### **4. Example - Canary Deployment:**

Gradually shift traffic from old to new version:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: streamlit-canary
spec:
  hosts:
  - streamlit-dashboard
  http:
  - route:
    - destination:
        host: streamlit-dashboard
        subset: stable
      weight: 90    # 90% to old version
    - destination:
        host: streamlit-dashboard
        subset: canary
      weight: 10    # 10% to new version
```

#### **5. View Istio Metrics:**

```bash
# See traffic metrics
kubectl exec -n istio-system deployment/istiod -- \
  pilot-discovery request GET /debug/edsz

# View proxy configuration
istioctl proxy-config routes -n inquiries-system streamlit-dashboard-xxx
```

#### **6. Test Istio Gateway:**

Your gateway is configured - you can access services through it:

```bash
# Current configuration
kubectl get virtualservice automated-inquiries-processing -n inquiries-system -o yaml

# Test accessing through gateway
curl -H "Host: inquiries-api.example.com" http://localhost:30080
```

### **Real-World Use Cases:**

#### **Use Case 1: Canary Deployment**
```bash
# Deploy new version as canary
kubectl apply -f streamlit-v2-deployment.yaml

# Route 10% traffic to v2, 90% to v1
# Monitor errors in Grafana
# If OK, gradually increase to 100%
# If errors, rollback immediately
```

#### **Use Case 2: Circuit Breaker**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: streamlit-circuit-breaker
spec:
  host: streamlit-dashboard
  trafficPolicy:
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

If a pod fails 5 times in 30s, Istio automatically stops sending traffic to it!

#### **Use Case 3: Automatic Retries**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-with-retries
spec:
  hosts:
  - fastapi-service
  http:
  - retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset,connect-failure
```

Istio automatically retries failed requests!

---

## 🎯 **Quick Access Summary**

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Streamlit** | http://localhost:8501 | - | Main dashboard |
| **Airflow** | http://localhost:8080 | admin/admin | DAG management |
| **Grafana** | http://localhost:3000 | admin/admin | Metrics & monitoring |
| **ArgoCD** | https://localhost:30009 | admin/ZTfydHTqtQmRjPso | GitOps deployments |
| **Istio Gateway** | http://localhost:30080 | - | Service mesh entry |

---

## 💡 **Practical Demo Scenarios**

### **Scenario 1: Deploy New Feature with ArgoCD**

1. Create a Git repo with your K8s manifests
2. Configure ArgoCD app to watch the repo
3. Update `streamlit-dashboard.yaml` (add new feature)
4. Push to Git
5. **ArgoCD auto-deploys** within 3 minutes
6. View deployment progress in ArgoCD UI
7. Rollback by reverting Git commit if needed

### **Scenario 2: Blue-Green Deployment with Istio**

1. Deploy new version (green) alongside old (blue)
2. Use Istio VirtualService to route 0% to green
3. Test green version internally
4. Switch 100% traffic to green instantly
5. Keep blue running for quick rollback
6. Delete blue when confident

### **Scenario 3: Monitor with Prometheus/Grafana**

1. Open Grafana: http://localhost:3000
2. View pre-configured dashboards
3. See pod CPU/memory usage
4. Set up alerts (e.g., if API latency > 1s)
5. Get notifications via email/Slack

### **Scenario 4: Manage Everything with Helm**

```bash
# List all apps
helm list -A

# Upgrade Istio to new version
helm upgrade istiod istio/istiod \
  --namespace istio-system \
  --version 1.28.0

# Rollback if issues
helm rollback istiod -n istio-system
```

---

## 🚀 **Try It Now!**

### **1. Explore ArgoCD:**
```bash
open https://localhost:30009
# Login: admin / ZTfydHTqtQmRjPso
# Click around the UI
```

### **2. Check Istio Traffic:**
```bash
# See all Istio routing rules
kubectl get virtualservice,gateway --all-namespaces

# View Istio configuration
kubectl describe gateway inquiries-gateway -n inquiries-system
```

### **3. Use Helm:**
```bash
# See everything Helm manages
helm list -A

# Check for updates
helm repo update
helm search repo prometheus --versions | head -10
```

---

## 📚 **Learn More:**

- **Helm**: https://helm.sh/docs/
- **ArgoCD**: https://argo-cd.readthedocs.io/
- **Istio**: https://istio.io/latest/docs/

---

## 🎓 **Key Takeaways:**

1. **Helm** = Package manager (install/upgrade/rollback apps)
2. **ArgoCD** = GitOps (Git → Kubernetes automatically)
3. **Istio** = Service mesh (traffic management, security, observability)

Together they provide:
- ✅ Easy application management (Helm)
- ✅ Automated deployments from Git (ArgoCD)  
- ✅ Advanced traffic control & security (Istio)
- ✅ Full observability (Prometheus/Grafana via Helm)

**This is production-grade infrastructure!** 🚀
