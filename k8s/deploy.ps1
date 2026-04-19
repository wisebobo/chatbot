# Kubernetes Deployment Script for Chatbot Application (PowerShell)
# Usage: .\deploy.ps1 [-Environment production] [-ImageTag latest]

param(
    [string]$Environment = "production",
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"
$Namespace = "chatbot"
$ImageName = "chatbot"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Chatbot K8s Deployment Script" -ForegroundColor Cyan
Write-Host "  Environment: $Environment" -ForegroundColor Cyan
Write-Host "  Image: $ImageName`:$ImageTag" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if kubectl is installed
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ kubectl is not installed. Please install kubectl first." -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
$BuildImage = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $BuildImage = $true
} else {
    Write-Host "⚠️  Docker is not installed. Skipping image build." -ForegroundColor Yellow
}

# Step 1: Build Docker image
if ($BuildImage) {
    Write-Host ""
    Write-Host "📦 Step 1: Building Docker image..." -ForegroundColor Green
    docker build -t "$ImageName`:$ImageTag" .
    
    # Optional: Push to registry
    # Write-Host "📤 Pushing image to registry..." -ForegroundColor Green
    # docker tag "$ImageName`:$ImageTag" "your-registry.com/$ImageName`:$ImageTag"
    # docker push "your-registry.com/$ImageName`:$ImageTag"
}

# Step 2: Create namespace
Write-Host ""
Write-Host "🏗️  Step 2: Creating namespace..." -ForegroundColor Green
kubectl apply -f k8s/namespace.yaml

# Step 3: Apply configurations
Write-Host ""
Write-Host "⚙️  Step 3: Applying ConfigMap and Secrets..." -ForegroundColor Green
Write-Host "⚠️  IMPORTANT: Update k8s/secret.yaml with actual values before deploying!" -ForegroundColor Yellow
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Step 4: Deploy application
Write-Host ""
Write-Host "🚀 Step 4: Deploying application..." -ForegroundColor Green
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Step 5: Configure autoscaling
Write-Host ""
Write-Host "📊 Step 5: Configuring horizontal pod autoscaler..." -ForegroundColor Green
kubectl apply -f k8s/hpa.yaml

# Step 6: Setup networking
Write-Host ""
Write-Host "🌐 Step 6: Configuring network policies and ingress..." -ForegroundColor Green
kubectl apply -f k8s/networkpolicy.yaml
kubectl apply -f k8s/ingress.yaml

# Step 7: Wait for deployment
Write-Host ""
Write-Host "⏳ Step 7: Waiting for deployment to be ready..." -ForegroundColor Green
kubectl rollout status deployment/chatbot-deployment -n $Namespace --timeout=300s

# Step 8: Verify deployment
Write-Host ""
Write-Host "✅ Step 8: Verifying deployment..." -ForegroundColor Green
Write-Host ""
Write-Host "Pods:" -ForegroundColor Cyan
kubectl get pods -n $Namespace -l app=chatbot
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
kubectl get svc -n $Namespace -l app=chatbot
Write-Host ""
Write-Host "HPA:" -ForegroundColor Cyan
kubectl get hpa -n $Namespace

# Step 9: Show access information
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Access Information:" -ForegroundColor Green
Write-Host "   - Internal Service: chatbot-service.chatbot.svc.cluster.local:80"
Write-Host "   - External URL: https://chatbot.company.com (update Ingress host)"
Write-Host "   - Metrics: http://<pod-ip>:8000/metrics"
Write-Host ""
Write-Host "🔍 Useful Commands:" -ForegroundColor Green
Write-Host "   - View logs: kubectl logs -n chatbot -l app=chatbot -f"
Write-Host "   - Port forward: kubectl port-forward -n chatbot svc/chatbot-service 8000:80"
Write-Host "   - Scale manually: kubectl scale -n chatbot deployment/chatbot-deployment --replicas=5"
Write-Host "   - Restart: kubectl rollout restart -n chatbot deployment/chatbot-deployment"
Write-Host ""
Write-Host "⚠️  Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Update LDAP configuration in k8s/secret.yaml"
Write-Host "   2. Update LLM API credentials"
Write-Host "   3. Configure TLS certificate for Ingress"
Write-Host "   4. Test the application: curl https://chatbot.company.com/api/v1/auth/health"
Write-Host ""
