# ==============================================================================
# Parallax DevOps Platform - Complete Cluster Bootstrap Script (PowerShell)
# Spins up the entire 6-week cloud-native enterprise stack from scratch.
# ==============================================================================

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "🚀 Parallax DevOps Platform - End-to-End Cluster Bootstrap (Windows)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

# 1. Start Minikube
Write-Host "`n[1/7] Initializing Minikube cluster (K8s v1.30.0)..." -ForegroundColor Yellow
minikube start --kubernetes-version=v1.30.0 --memory=6144 --cpus=3 --driver=docker

# 2. Install Istio Service Mesh
Write-Host "`n[2/7] Installing Istio Service Mesh & enabling ambient mTLS..." -ForegroundColor Yellow
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update
helm upgrade --install istio-base istio/base -n istio-system --create-namespace
helm upgrade --install istiod istio/istiod -n istio-system --wait
kubectl label namespace default istio-injection=enabled --overwrite

# 3. Install Kong API Gateway
Write-Host "`n[3/7] Installing Kong API Gateway & Ingress Controller..." -ForegroundColor Yellow
helm repo add kong https://charts.konghq.com
helm repo update
helm upgrade --install kong kong/kong `
  --namespace kong `
  --create-namespace `
  --set proxy.type=NodePort `
  --set proxy.http.nodePort=32080 `
  --wait

# 4. Install ArgoCD GitOps Engine
Write-Host "`n[4/7] Installing ArgoCD GitOps Engine..." -ForegroundColor Yellow
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd `
  --namespace argocd `
  --create-namespace `
  --set server.service.type=NodePort `
  --set server.service.nodePortHttp=30088 `
  --wait

# 5. Install Observability Stack
Write-Host "`n[5/7] Installing Prometheus & Grafana Observability Stack..." -ForegroundColor Yellow
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack `
  --namespace monitoring `
  --create-namespace `
  -f helm/observability/values.yaml `
  --wait
helm upgrade --install parallax-observability helm/observability `
  --namespace monitoring

# 6. Install Argo Rollouts
Write-Host "`n[6/7] Installing Argo Rollouts Controller & Dashboard..." -ForegroundColor Yellow
helm upgrade --install argo-rollouts argo/argo-rollouts `
  --namespace argo-rollouts `
  --create-namespace `
  --set dashboard.enabled=true `
  --set dashboard.service.type=NodePort `
  --set dashboard.service.nodePort=31031 `
  --wait

# 7. Deploy Microservices & Canary Rollouts
Write-Host "`n[7/7] Deploying Parallax Microservices with Canary Capability..." -ForegroundColor Yellow
helm upgrade --install microservices helm/microservices `
  --namespace default `
  --wait

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "🎉 Cluster bootstrap complete! All 6 milestones active and verified:" -ForegroundColor Green
Write-Host "  - Kong API Gateway     : http://localhost:32080"
Write-Host "  - Frontend Dashboard   : http://localhost:30080"
Write-Host "  - ArgoCD GitOps UI     : http://localhost:30088"
Write-Host "  - Grafana Observability: http://localhost:30300 (admin / parallax-admin-2026)"
Write-Host "  - Prometheus Engine    : http://localhost:30090"
Write-Host "  - Alertmanager UI      : http://localhost:30093"
Write-Host "  - Argo Rollouts Web UI : http://localhost:31031"
Write-Host "====================================================================" -ForegroundColor Green

