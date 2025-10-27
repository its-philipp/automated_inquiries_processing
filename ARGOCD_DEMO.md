# 🚀 ArgoCD GitOps Demo

## What We'll Demonstrate

We'll show how ArgoCD automatically detects and deploys changes from Git to Kubernetes!

## Setup

### Current Status:
- ✅ ArgoCD running at: https://localhost:30009
- ✅ Streamlit app deployed in: `inquiries-system` namespace
- ✅ K8s manifests in: `k8s/services/`

### The Demo:

**Scenario:** Update the Streamlit dashboard and watch ArgoCD auto-deploy it!

---

## Option 1: Full GitOps with GitHub (Recommended for Real Use)

### Step 1: Push this repo to GitHub

```bash
cd /Users/philipptrinh/workspace/playground/automated_inquiries_processing

# Create GitHub repo first, then:
git init
git add .
git commit -m "Initial commit - Inquiry automation platform"
git remote add origin https://github.com/YOUR_USERNAME/automated-inquiries.git
git push -u origin main
```

### Step 2: Create ArgoCD Application

In ArgoCD UI (https://localhost:30009):

1. Click **"+ NEW APP"**
2. Fill in:
   - **Application Name**: `streamlit-dashboard`
   - **Project**: `default`
   - **Sync Policy**: `Automatic`
   - **Repository URL**: `https://github.com/YOUR_USERNAME/automated-inquiries`
   - **Revision**: `HEAD` or `main`
   - **Path**: `k8s/services`
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `inquiries-system`
3. Click **CREATE**

### Step 3: Make a Change

```bash
# Edit the Streamlit deployment
vim k8s/services/streamlit-dashboard.yaml

# Change something (e.g., add a label):
metadata:
  labels:
    app: streamlit-dashboard
    version: v2.0  # <-- Add this

# Commit and push
git add k8s/services/streamlit-dashboard.yaml
git commit -m "Update Streamlit to v2.0"
git push
```

### Step 4: Watch ArgoCD Magic! ✨

1. Go to ArgoCD UI: https://localhost:30009
2. Within 3 minutes, you'll see:
   - App shows "Out of Sync" (orange)
   - Click "Sync" or wait for auto-sync
   - Watch the visual graph update
   - See the new pod rolling out
   - App returns to "Synced" (green)

**Benefits:**
- ✅ Full audit trail in Git
- ✅ Easy rollbacks (revert Git commit)
- ✅ Team collaboration (PR reviews before deploy)
- ✅ Disaster recovery (cluster dies? Redeploy from Git!)

---

## Option 2: Quick Local Demo (No GitHub Required)

For a quick demo without GitHub, we can manually demonstrate the workflow:

### Step 1: See Current State

```bash
kubectl get deployment streamlit-dashboard -n inquiries-system -o yaml | grep -A 5 "labels:"
```

### Step 2: Make a Change via Git-Style Workflow

```bash
# Edit the manifest
vim k8s/services/streamlit-dashboard.yaml

# Change replicas from 1 to 2
spec:
  replicas: 2  # <-- Change this
```

### Step 3: Apply the Change

```bash
kubectl apply -f k8s/services/streamlit-dashboard.yaml
```

### Step 4: Observe What Happened

```bash
# See the new replica
kubectl get pods -n inquiries-system -l app=streamlit-dashboard

# This is what ArgoCD would do automatically!
```

### Step 5: Rollback Demo

```bash
# Change back to 1 replica
vim k8s/services/streamlit-dashboard.yaml
# Set replicas: 1

kubectl apply -f k8s/services/streamlit-dashboard.yaml

# With ArgoCD, you'd just:
# 1. Revert the Git commit
# 2. ArgoCD auto-deploys the old version
```

---

## Option 3: Demonstrate ArgoCD UI (Current Setup)

Even without GitOps fully configured, you can explore ArgoCD:

### Open ArgoCD UI:
```bash
open https://localhost:30009
```

**Login:**
- Username: `admin`
- Password: `ZTfydHTqtQmRjPso`

### What to Explore:

1. **Applications Page**:
   - Clean interface
   - Would show your apps if connected to Git

2. **Settings → Repositories**:
   - Add a Git repo
   - Connect to GitHub/GitLab
   - Set up SSH keys or tokens

3. **Settings → Projects**:
   - Organize apps into projects
   - Set RBAC permissions
   - Control which namespaces/clusters apps can deploy to

4. **User Info**:
   - See your admin account
   - Add more users
   - Set up SSO (GitHub, Google, etc.)

---

## 🎯 Practical GitOps Workflow (Once Set Up)

### Daily Developer Workflow:

```bash
# 1. Make code changes
vim inquiry_monitoring_dashboard.py

# 2. Test locally
streamlit run inquiry_monitoring_dashboard.py

# 3. Update K8s manifest if needed
vim k8s/services/streamlit-dashboard.yaml

# 4. Commit and push
git add .
git commit -m "Add new dashboard chart"
git push

# 5. ArgoCD automatically:
#    - Detects the commit (within 3 min)
#    - Compares with cluster state
#    - Shows "Out of Sync"
#    - Auto-deploys new version
#    - Shows "Synced" when complete
#
# 6. You get a notification (Slack/Email)
#    "streamlit-dashboard deployed successfully!"
```

### Rollback Workflow:

```bash
# Something broke? Just revert the Git commit:
git revert HEAD
git push

# ArgoCD automatically rolls back!
# No kubectl commands needed!
```

---

## 🚀 Quick Demo Script You Can Run Now

```bash
#!/bin/bash

echo "🎯 ArgoCD + Istio Gateway Demo"
echo ""

# 1. Show current Streamlit deployment
echo "1️⃣  Current Streamlit deployment:"
kubectl get deployment streamlit-dashboard -n inquiries-system

# 2. Access through Istio Gateway
echo ""
echo "2️⃣  Accessing through Istio Gateway:"
curl -s http://localhost:30080 | grep -o "<title>.*</title>"

# 3. Show ArgoCD UI
echo ""
echo "3️⃣  Opening ArgoCD UI..."
open https://localhost:30009

echo ""
echo "✅ Demo ready!"
echo ""
echo "Next steps:"
echo "  1. Login to ArgoCD (admin / ZTfydHTqtQmRjPso)"
echo "  2. Explore the UI"
echo "  3. Try creating an app pointing to a Git repo"
echo "  4. Make changes and watch auto-deploy!"
```

---

## 🎓 Key Takeaways

### Traditional Deployment:
```bash
# Developer makes change
kubectl apply -f deployment.yaml

# Problems:
# ❌ No audit trail
# ❌ Manual process
# ❌ Hard to rollback
# ❌ Cluster state != Git state
```

### GitOps with ArgoCD:
```bash
# Developer makes change
git push

# ArgoCD handles the rest!
# ✅ Full Git audit trail
# ✅ Automatic deployment
# ✅ Easy rollbacks (git revert)
# ✅ Git is single source of truth
# ✅ Declarative config
# ✅ Multi-cluster from one UI
```

---

## 📚 Next Steps

1. **Try the Istio Gateway:**
   ```bash
   open http://localhost:30080
   # See Streamlit through Istio!
   ```

2. **Explore ArgoCD UI:**
   ```bash
   open https://localhost:30009
   ```

3. **Set up a test Git repo:**
   - Create a simple repo with one K8s manifest
   - Connect ArgoCD to it
   - Make a change and watch magic happen!

4. **Read the full guide:**
   ```bash
   cat CNCF_SERVICES_GUIDE.md
   ```

---

## 🌟 Why This Matters

You now have:
- ✅ **Istio** managing traffic (smart routing, security)
- ✅ **ArgoCD** ready for GitOps (auto-deploy from Git)
- ✅ **Prometheus** monitoring everything
- ✅ **Helm** managing complex apps

This is the same stack used by:
- Netflix
- Spotify  
- Airbnb
- Many Fortune 500 companies

**You're running enterprise-grade infrastructure!** 🚀

