# 🔐 Security Best Practices

## ⚠️ Important Security Notes

### Current Setup (Local Development)

This project is configured for **local development** with Kind (Kubernetes in Docker). The default passwords and keys in the configuration are:

**✅ Acceptable for local-only development** - Your cluster runs entirely on your laptop  
**❌ NOT suitable for production** - Never deploy this to the cloud as-is!

---

## 🛡️ What's Currently Exposed (Local Only)

### In `k8s/airflow/airflow-with-dags-fix.yaml`:
- **PostgreSQL password**: `postgres` (hardcoded)
- **Airflow Fernet Key**: Encryption key for Airflow connections
- **Airflow Secret Key**: Session encryption key

### Why It's OK for Local Development:
1. ✅ Cluster runs only on your machine (Kind in Docker)
2. ✅ No external access (not exposed to internet)
3. ✅ No production data
4. ✅ Easy to reset (just delete the cluster)

### Why It's NOT OK for Production:
1. ❌ Keys visible in Git history
2. ❌ Anyone with repo access has credentials
3. ❌ Cannot rotate secrets easily
4. ❌ Violates security compliance (SOC2, GDPR, etc.)

---

## 🚀 Production-Ready Security (If Deploying to Cloud)

### Step 1: Use Kubernetes Secrets

**Create secrets from environment variables:**

```bash
# Create namespace
kubectl create namespace inquiries-system

# Create PostgreSQL secret
kubectl create secret generic postgres-credentials \
  --from-literal=username=postgres \
  --from-literal=password=$(openssl rand -base64 32) \
  -n inquiries-system

# Create Airflow secrets
kubectl create secret generic airflow-secrets \
  --from-literal=fernet-key=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
  --from-literal=secret-key=$(openssl rand -base64 32) \
  --from-literal=admin-password=$(openssl rand -base64 16) \
  -n airflow
```

### Step 2: Update K8s Manifests

**Replace hardcoded values with secret references:**

```yaml
# In airflow-with-dags-fix.yaml
env:
- name: AIRFLOW__CORE__FERNET_KEY
  valueFrom:
    secretKeyRef:
      name: airflow-secrets
      key: fernet-key
- name: AIRFLOW__WEBSERVER__SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: airflow-secrets
      key: secret-key
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: postgres-credentials
      key: password
```

### Step 3: Use External Secrets Operator (Advanced)

For production, use [External Secrets Operator](https://external-secrets.io/) to sync from:
- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault
- HashiCorp Vault

---

## 🔒 Recommended Security Improvements

### For Local Development:

1. **Add `.env` file (gitignored)**
   ```bash
   # Copy example
   cp .env.example .env
   
   # Customize with your values
   vim .env
   ```

2. **Rotate default passwords**
   ```bash
   # Generate new Fernet key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   
   # Update in your .env file
   ```

3. **Use `.gitignore`** (already configured)
   - `.env` files never committed
   - Secrets directory excluded

### For Production Deployment:

1. **Never use default passwords**
   - Generate strong random passwords
   - Use password manager or secrets vault

2. **Enable mTLS in Istio**
   ```yaml
   apiVersion: security.istio.io/v1beta1
   kind: PeerAuthentication
   metadata:
     name: default
     namespace: inquiries-system
   spec:
     mtls:
       mode: STRICT
   ```

3. **Use RBAC**
   - Limit who can access Kubernetes resources
   - Create service accounts with minimal permissions

4. **Enable audit logging**
   - Track all access to sensitive data
   - Monitor for suspicious activity

5. **Scan for vulnerabilities**
   ```bash
   # Scan Docker images
   docker scan airflow-ml:2.7.3
   
   # Scan K8s configs
   kubesec scan k8s/airflow/airflow-with-dags-fix.yaml
   ```

---

## 🎯 Quick Security Checklist

### ✅ For Local Development (Current Setup):
- [x] Cluster isolated on local machine
- [x] No external network exposure
- [x] `.gitignore` configured
- [x] `.env.example` provided
- [ ] Users aware of security implications

### 🔐 Before Production Deployment:
- [ ] All secrets in Kubernetes Secrets or external vault
- [ ] No hardcoded passwords in YAML files
- [ ] TLS/HTTPS enabled for all services
- [ ] Istio mTLS enabled
- [ ] RBAC configured
- [ ] Network policies applied
- [ ] Security scanning in CI/CD
- [ ] Audit logging enabled
- [ ] Secrets rotation policy defined
- [ ] Backup and disaster recovery plan

---

## 🚨 What to Do If Secrets Are Exposed

### If you accidentally committed secrets to Git:

1. **Rotate all exposed secrets immediately**
   ```bash
   # Generate new credentials
   # Update K8s secrets
   kubectl delete secret airflow-secrets -n airflow
   kubectl create secret generic airflow-secrets --from-literal=...
   ```

2. **Remove from Git history** (use BFG Repo-Cleaner)
   ```bash
   # Clone a fresh copy
   git clone --mirror https://github.com/user/repo.git
   
   # Remove secrets
   bfg --replace-text passwords.txt repo.git
   
   # Force push (WARNING: Destructive!)
   cd repo.git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

3. **Inform team** - Assume secrets are compromised

4. **Monitor for unauthorized access**

---

## 📚 Further Reading

- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [OWASP Kubernetes Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [GitGuardian: How to Remove Secrets from Git](https://blog.gitguardian.com/rewriting-git-history-cheatsheet/)

---

## 💡 Summary

**For your current local setup**: You're fine! The "exposed" secrets only work on your local machine.

**Before deploying to production**: Follow the production security checklist above.

**Best practice**: Even for local dev, use `.env` files and Kubernetes Secrets to build good habits.

**Remember**: Security is a journey, not a destination! 🛡️

