# Kubernetes Quick Reference Card

## 🚀 Deployment Commands

```bash
# Deploy everything
kubectl apply -k k8s/

# Or use the script
./k8s/deploy.sh production latest        # Linux/Mac
.\k8s\deploy.ps1 -Environment production # Windows

# Check status
kubectl get all -n chatbot
```

## 🔍 Monitoring

```bash
# View pods
kubectl get pods -n chatbot -w

# View logs
kubectl logs -l app=chatbot -n chatbot -f

# Port forward for local testing
kubectl port-forward svc/chatbot-service 8000:80 -n chatbot

# Check HPA
kubectl get hpa -n chatbot -w
```

## 🔄 Updates & Rollbacks

```bash
# Update image
kubectl set image deployment/chatbot-deployment \
  chatbot=chatbot:v3.1.0 -n chatbot

# Monitor rollout
kubectl rollout status deployment/chatbot-deployment -n chatbot

# Rollback
kubectl rollout undo deployment/chatbot-deployment -n chatbot

# View history
kubectl rollout history deployment/chatbot-deployment -n chatbot
```

## 📊 Scaling

```bash
# Manual scale
kubectl scale deployment/chatbot-deployment --replicas=5 -n chatbot

# Check autoscaling
kubectl get hpa chatbot-hpa -n chatbot -w
```

## 🛠️ Debugging

```bash
# Describe pod (detailed info)
kubectl describe pod <pod-name> -n chatbot

# Execute command in pod
kubectl exec -it <pod-name> -n chatbot -- /bin/bash

# Check events
kubectl get events -n chatbot --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n chatbot
```

## 🧹 Cleanup

```bash
# Delete everything
kubectl delete namespace chatbot

# Or delete resources
kubectl delete -f k8s/
```

## 📝 Common Issues

### Pod stuck in Pending
```bash
kubectl describe pod <pod-name> -n chatbot
# Check: Resource quotas, node availability
```

### CrashLoopBackOff
```bash
kubectl logs <pod-name> -n chatbot --previous
# Check: Environment variables, application errors
```

### ImagePullBackOff
```bash
kubectl describe pod <pod-name> -n chatbot | grep Image
# Check: Image name, registry credentials
```

### OOMKilled
```bash
kubectl describe pod <pod-name> -n chatbot | grep -A 5 "Last State"
# Fix: Increase memory limit in deployment.yaml
```

## 🔐 Secrets Management

```bash
# Create secret from file
kubectl create secret generic chatbot-secrets \
  --from-file=LLM_API_KEY=./secrets/llm_key.txt \
  --from-file=JWT_SECRET=./secrets/jwt_secret.txt \
  -n chatbot

# View secret keys (not values)
kubectl get secrets -n chatbot

# Decode secret (base64)
kubectl get secret chatbot-secrets -n chatbot -o jsonpath='{.data.LLM_API_KEY}' | base64 --decode
```

## 🌐 Networking

```bash
# Get service details
kubectl get svc -n chatbot

# Get ingress
kubectl get ingress -n chatbot

# Test connectivity
kubectl run test-pod --rm -it --image=busybox --restart=Never -- \
  wget -qO- http://chatbot-service.chatbot.svc.cluster.local/api/v1/auth/health
```

## 💾 Persistent Volumes

```bash
# Check PVC status
kubectl get pvc -n chatbot

# Check PV
kubectl get pv

# Backup wiki data
kubectl cp chatbot/<pod-name>:/app/data/wiki ./wiki-backup -n chatbot
```

## 🎯 Useful One-Liners

```bash
# Restart all pods
kubectl rollout restart deployment/chatbot-deployment -n chatbot

# Get all pod IPs
kubectl get pods -n chatbot -o jsonpath='{.items[*].status.podIP}'

# Count restarts
kubectl get pods -n chatbot -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}'

# Export YAML
kubectl get deployment chatbot-deployment -n chatbot -o yaml > backup.yaml

# Dry run (test without applying)
kubectl apply -f k8s/deployment.yaml --dry-run=client
```

---

**Tip:** Bookmark this page for quick reference! 🔖
