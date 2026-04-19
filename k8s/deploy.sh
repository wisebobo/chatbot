#!/bin/bash
# Kubernetes Deployment Script for Chatbot Application
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
NAMESPACE="chatbot"
IMAGE_NAME="chatbot"
IMAGE_TAG="${2:-latest}"

echo "=========================================="
echo "  Chatbot K8s Deployment Script"
echo "  Environment: $ENVIRONMENT"
echo "  Image: $IMAGE_NAME:$IMAGE_TAG"
echo "=========================================="

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if Docker is installed (for building image)
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. Skipping image build."
    BUILD_IMAGE=false
else
    BUILD_IMAGE=true
fi

# Step 1: Build Docker image
if [ "$BUILD_IMAGE" = true ]; then
    echo ""
    echo "📦 Step 1: Building Docker image..."
    docker build -t $IMAGE_NAME:$IMAGE_TAG .
    
    # Optional: Push to registry
    # echo "📤 Pushing image to registry..."
    # docker tag $IMAGE_NAME:$IMAGE_TAG your-registry.com/$IMAGE_NAME:$IMAGE_TAG
    # docker push your-registry.com/$IMAGE_NAME:$IMAGE_TAG
fi

# Step 2: Create namespace
echo ""
echo "🏗️  Step 2: Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Step 3: Apply configurations
echo ""
echo "⚙️  Step 3: Applying ConfigMap and Secrets..."
echo "⚠️  IMPORTANT: Update k8s/secret.yaml with actual values before deploying!"
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Step 4: Deploy application
echo ""
echo "🚀 Step 4: Deploying application..."
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Step 5: Configure autoscaling
echo ""
echo "📊 Step 5: Configuring horizontal pod autoscaler..."
kubectl apply -f k8s/hpa.yaml

# Step 6: Setup networking
echo ""
echo "🌐 Step 6: Configuring network policies and ingress..."
kubectl apply -f k8s/networkpolicy.yaml
kubectl apply -f k8s/ingress.yaml

# Step 7: Wait for deployment
echo ""
echo "⏳ Step 7: Waiting for deployment to be ready..."
kubectl rollout status deployment/chatbot-deployment -n $NAMESPACE --timeout=300s

# Step 8: Verify deployment
echo ""
echo "✅ Step 8: Verifying deployment..."
echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE -l app=chatbot
echo ""
echo "Services:"
kubectl get svc -n $NAMESPACE -l app=chatbot
echo ""
echo "HPA:"
kubectl get hpa -n $NAMESPACE

# Step 9: Show access information
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "📝 Access Information:"
echo "   - Internal Service: chatbot-service.chatbot.svc.cluster.local:80"
echo "   - External URL: https://chatbot.company.com (update Ingress host)"
echo "   - Metrics: http://<pod-ip>:8000/metrics"
echo ""
echo "🔍 Useful Commands:"
echo "   - View logs: kubectl logs -n chatbot -l app=chatbot -f"
echo "   - Port forward: kubectl port-forward -n chatbot svc/chatbot-service 8000:80"
echo "   - Scale manually: kubectl scale -n chatbot deployment/chatbot-deployment --replicas=5"
echo "   - Restart: kubectl rollout restart -n chatbot deployment/chatbot-deployment"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Update LDAP configuration in k8s/secret.yaml"
echo "   2. Update LLM API credentials"
echo "   3. Configure TLS certificate for Ingress"
echo "   4. Test the application: curl https://chatbot.company.com/api/v1/auth/health"
echo ""
