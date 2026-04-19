# Kubernetes Deployment Guide

This guide explains how to deploy the Chatbot application to Kubernetes.

## 📋 Prerequisites

- **kubectl** installed and configured
- **Docker** installed (for building images)
- Access to a Kubernetes cluster (v1.24+)
- Container registry access (optional, for production)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────┐
│         Ingress Controller              │
│    (NGINX / Traefik / ALB)              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      chatbot-service (ClusterIP)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     chatbot-deployment (3+ replicas)    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ Pod 1   │ │ Pod 2   │ │ Pod 3   │  │
│  └─────────┘ └─────────┘ └─────────┘  │
└─────────────────────────────────────────┘
         │              │
         ▼              ▼
  ┌─────────────┐ ┌──────────┐
  │ Wiki Data   │ │  Temp    │
  │   (PVC)     │ │ Volume   │
  └─────────────┘ └──────────┘
```

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

#### Linux/Mac:
```bash
cd k8s
chmod +x deploy.sh
./deploy.sh production latest
```

#### Windows PowerShell:
```powershell
cd k8s
.\deploy.ps1 -Environment production -ImageTag latest
```

### Option 2: Manual Deployment with Kustomize

```bash
# Apply all resources
kubectl apply -k k8s/

# Or use kubectl directly
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/networkpolicy.yaml
```

## ⚙️ Configuration

### 1. Update Secrets

Edit `k8s/secret.yaml` and replace placeholder values:

```yaml
stringData:
  LLM_API_KEY: "your-actual-llm-api-key"
  JWT_SECRET: "generate-strong-random-string"
  API_SECRET_KEY: "generate-another-strong-random-string"
  LDAP_BIND_DN: "CN=service_account,OU=Service Accounts,DC=company,DC=com"
  LDAP_BIND_PASSWORD: "your-ad-service-account-password"
```

**Generate secure secrets:**
```bash
# Generate random secret
openssl rand -base64 32

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Update ConfigMap

Edit `k8s/configmap.yaml` with your environment settings:

```yaml
data:
  LLM_API_BASE_URL: "http://your-company-ai-platform/v1"
  LDAP_SERVER_URL: "ldaps://ad.company.com"
  LDAP_BASE_DN: "DC=company,DC=com"
  LDAP_DOMAIN: "COMPANY"
```

### 3. Update Ingress

Edit `k8s/ingress.yaml` and change the host:

```yaml
spec:
  rules:
    - host: chatbot.your-company.com  # Change this
```

### 4. Configure TLS

For production, obtain a TLS certificate:

**Option A: Using cert-manager (recommended)**
```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

**Option B: Manual certificate**
```bash
kubectl create secret tls chatbot-tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n chatbot
```

## 📦 Building and Pushing Image

### Build Locally

```bash
docker build -t chatbot:latest .
```

### Tag and Push to Registry

```bash
# Docker Hub
docker tag chatbot:latest yourusername/chatbot:latest
docker push yourusername/chatbot:latest

# Private Registry
docker tag chatbot:latest registry.company.com/chatbot:latest
docker push registry.company.com/chatbot:latest
```

### Update Deployment Image

Edit `k8s/deployment.yaml`:
```yaml
spec:
  template:
    spec:
      containers:
        - name: chatbot
          image: registry.company.com/chatbot:latest  # Update this
```

Or use kubectl:
```bash
kubectl set image deployment/chatbot-deployment \
  chatbot=registry.company.com/chatbot:latest \
  -n chatbot
```

## 🔍 Monitoring and Debugging

### Check Deployment Status

```bash
# View pods
kubectl get pods -n chatbot

# View detailed pod info
kubectl describe pod -l app=chatbot -n chatbot

# View deployment status
kubectl rollout status deployment/chatbot-deployment -n chatbot
```

### View Logs

```bash
# Follow logs from all pods
kubectl logs -l app=chatbot -n chatbot -f

# Logs from specific pod
kubectl logs <pod-name> -n chatbot -f

# Previous container logs (after restart)
kubectl logs <pod-name> -n chatbot --previous
```

### Port Forwarding (Local Testing)

```bash
# Forward local port 8000 to service
kubectl port-forward svc/chatbot-service 8000:80 -n chatbot

# Now access: http://localhost:8000
```

### Execute Commands in Pod

```bash
# Open shell in pod
kubectl exec -it <pod-name> -n chatbot -- /bin/bash

# Run command
kubectl exec <pod-name> -n chatbot -- python --version
```

## 🔄 Updating the Application

### Rolling Update

```bash
# Update image
kubectl set image deployment/chatbot-deployment \
  chatbot=chatbot:v3.1.0 \
  -n chatbot

# Monitor rollout
kubectl rollout status deployment/chatbot-deployment -n chatbot

# View rollout history
kubectl rollout history deployment/chatbot-deployment -n chatbot
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/chatbot-deployment -n chatbot

# Rollback to specific revision
kubectl rollout undo deployment/chatbot-deployment -n chatbot --to-revision=2
```

## 📊 Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment/chatbot-deployment --replicas=5 -n chatbot
```

### Automatic Scaling (HPA)

HPA is already configured to scale based on CPU (70%) and memory (80%) usage.

```bash
# View HPA status
kubectl get hpa -n chatbot

# Edit HPA thresholds
kubectl edit hpa chatbot-hpa -n chatbot
```

## 🔐 Security Best Practices

### 1. Use External Secret Management

For production, use external secret management:

- **HashiCorp Vault**: Integrate with Vault Agent Injector
- **AWS Secrets Manager**: Use External Secrets Operator
- **Azure Key Vault**: Use Azure Key Vault Provider for Secrets Store CSI Driver

Example with External Secrets Operator:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: chatbot-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: chatbot-secrets
  data:
    - secretKey: LLM_API_KEY
      remoteRef:
        key: chatbot/llm-api-key
        property: api_key
```

### 2. Network Policies

NetworkPolicy is already configured to restrict traffic. Adjust as needed for your environment.

### 3. Pod Security Standards

The deployment uses security contexts:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

### 4. Resource Limits

Resource requests and limits are configured to prevent resource exhaustion.

## 🆘 Troubleshooting

### Pod Won't Start

```bash
# Check events
kubectl get events -n chatbot --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n chatbot

# Check logs
kubectl logs <pod-name> -n chatbot
```

### Common Issues

#### 1. ImagePullBackOff

**Cause:** Image not found or authentication issue

**Solution:**
```bash
# Check image name
kubectl describe pod <pod-name> -n chatbot | grep Image

# Create image pull secret
kubectl create secret docker-registry registry-secret \
  --docker-server=registry.company.com \
  --docker-username=user \
  --docker-password=pass \
  -n chatbot
```

#### 2. CrashLoopBackOff

**Cause:** Application crashes on startup

**Solution:**
```bash
# Check logs
kubectl logs <pod-name> -n chatbot --previous

# Common fixes:
# - Verify environment variables
# - Check LDAP connectivity
# - Verify LLM API credentials
```

#### 3. LDAP Connection Failed

**Cause:** Cannot reach AD server

**Solution:**
```bash
# Test LDAP health endpoint
kubectl port-forward svc/chatbot-service 8000:80 -n chatbot
curl http://localhost:8000/api/v1/auth/health

# Check network policy
kubectl get networkpolicy -n chatbot

# Verify LDAP config
kubectl get secret chatbot-secrets -n chatbot -o yaml
```

#### 4. OOMKilled

**Cause:** Pod exceeded memory limit

**Solution:**
```bash
# Increase memory limit in deployment.yaml
resources:
  limits:
    memory: 4Gi  # Increase from 2Gi

# Apply changes
kubectl apply -f k8s/deployment.yaml
```

## 📈 Performance Tuning

### Adjust Resource Limits

Based on actual usage patterns:

```bash
# Monitor resource usage
kubectl top pods -n chatbot

# Adjust in deployment.yaml
resources:
  requests:
    cpu: 1000m    # Increase if CPU bound
    memory: 1Gi   # Increase if memory bound
  limits:
    cpu: 4000m
    memory: 4Gi
```

### Tune Gunicorn/Uvicorn Workers

In `k8s/configmap.yaml`:
```yaml
API_WORKERS: "8"  # Adjust based on CPU cores
```

Rule of thumb: `(2 x CPU_cores) + 1`

### Enable Connection Pooling

If using PostgreSQL/Redis, configure connection pooling in the application.

## 🧹 Cleanup

### Remove All Resources

```bash
# Delete namespace (removes everything)
kubectl delete namespace chatbot

# Or delete individual resources
kubectl delete -f k8s/
```

### Keep Persistent Volumes

```bash
# Delete deployment but keep PVC
kubectl delete deployment chatbot-deployment -n chatbot
kubectl delete pvc chatbot-wiki-pvc -n chatbot  # Only if you want to remove data
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Guide](https://kustomize.io/)
- [Helm Charts](https://helm.sh/) (for more complex deployments)
- [Prometheus Monitoring](https://prometheus.io/docs/prometheus/latest/configuration/kubernetes_sd_config/)

---

**Last Updated:** 2026-04-19  
**Kubernetes Version:** 1.24+  
**Status:** ✅ Production Ready
