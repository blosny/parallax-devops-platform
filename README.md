# Parallax DevOps Platform

[![DevOps Internship](https://img.shields.io/badge/Parallax%20Labs-DevOps%20Internship-6366f1?style=flat-square)](https://www.parallaxlab.site/)
[![Track](https://img.shields.io/badge/Track%20B-6--Week%20Standard%20Program-10b981?style=flat-square)](https://www.parallaxlab.site/)
[![Week 1 Deliverable](https://img.shields.io/badge/Week%201-Accepted%20(100%2F100)-238636?style=flat-square)](#)
[![Week 2 Deliverable](https://img.shields.io/badge/Week%202-Accepted%20(100%2F100)-238636?style=flat-square)](#)
[![Week 3 Deliverable](https://img.shields.io/badge/Week%203-Accepted%20(100%2F100)-238636?style=flat-square)](#)
[![Week 4 Deliverable](https://img.shields.io/badge/Week%204-Accepted%20(100%2F100)-238636?style=flat-square)](#)
[![Week 5 Deliverable](https://img.shields.io/badge/Week%205-Complete%20%26%20Verified-238636?style=flat-square)](#)

> **"Built different. Engineered better."**  
> A self-hosted enterprise infrastructure platform running entirely on local virtualization, engineered according to production-grade security, scalability, and 12-Factor principles.

---

## 📌 Executive Summary & Repository Lifecycle

This repository maintains the entire 6-week progressive infrastructure lifecycle, strictly honoring **The Single Repository Rule**.

| Milestone | Architecture Focus | Status | Core Technologies |
|:---|:---|:---:|:---|
| **Week 1** | Microservices & Containerization Foundation | **Accepted (100/100)** | FastAPI, Nginx Alpine, Docker Multi-Stage, Non-Root (`USER 1001`) |
| **Week 2** | Helm, Service Mesh & Strict mTLS | **Accepted (100/100)** | Minikube (K8s v1.30), Helm v4, Istio Service Mesh, Envoy Sidecars, Strict mTLS |
| **Week 3** | Kong Gateway & CI Pipeline | **Accepted (100/100)** | Kong Ingress Controller, Rate Limiting (5/min), API Key Auth, GitHub Actions, GHCR |
| **Week 4** | GitOps Continuous Deployment | **Accepted (100/100)** | ArgoCD, Declarative GitOps Application, Auto-Sync, Self-Healing, Slack Alerts |
| **Week 5** | Observability, Monitoring & Alerting | **Complete & Verified** | Prometheus Operator, Grafana, Dashboard-as-Code, Alertmanager, RED Metrics |
| **Week 6** | Canary Deployments & Final Project Polish | Planned | Flagger/Argo Rollouts, Canary Traffic Shifting, Production Hardening |

---

## 📊 Week 5 Deliverable: Observability, RED Metrics & Alerting

### Weekly Milestone Objectives
- [x] **Prometheus & Grafana via Helm (`helm/observability`):** Packaged and configured production-grade `kube-prometheus-stack` values file with custom NodePort configurations for Grafana (`:30300`), Prometheus (`:30090`), and Alertmanager (`:30093`).
- [x] **Application-Level Telemetry (`/metrics`):** Instrumentated FastAPI backend with HTTP middleware capturing request counts, latency histograms (P50/P90/P95/P99), and in-progress connections.
- [x] **Code-Provisioned Grafana Dashboard (`Dashboard-as-Code`):** Built 16-panel Grafana dashboard (`parallax-red-dashboard.json`) provisioned automatically via Kubernetes ConfigMap (`grafana_dashboard: "1"`), visualizing the **RED Method** (Rate, Errors, Duration) and **USE Method** (Pod CPU/Memory Saturation).
- [x] **Alertmanager Multi-Rule Configuration & Webhook Routing:** Configured 4 automated alert rules with multi-channel routing, inhibition rules, and webhook dispatching:
  1. `HighRequestLatency`: P95 duration > 500ms for 1m (Warning).
  2. `PodCrashLooping`: Container restart detected in 5m (Critical).
  3. `HighHttpErrorRate`: HTTP 5xx error rate > 5% for 1m (Critical).
  4. `MicroserviceTargetDown`: Scrape target unreachable for 1m (Critical).
- [x] **SRE Incident Response Runbook (`docs/RUNBOOK.md`):** Authored enterprise-grade runbook detailing Golden Signals, SLO/SLA error budgets, triage commands, and deliberate fault injection procedures.
- [x] **Simulated Load & Fault Injection Test Suite:** Built multi-threaded load generator (`scripts/simulate_load.py`) and fault injection endpoints (`/simulate/latency`, `/simulate/error`, `/simulate/crash`) to deliberately trigger each alert and validate dashboard responsiveness under load.

---

## 🏗️ Observability & Telemetry Architecture

```mermaid
graph TB
    subgraph Clients["Traffic Sources & Testing Tools"]
        LoadGen["Load Generator (scripts/simulate_load.py)"]
        CurlTest["Fault Injection Suite (scripts/trigger_alerts.sh)"]
    end

    subgraph KongNS["kong Namespace (Ingress Layer)"]
        KongProxy["Kong API Gateway (:32080)<br/>API Key Auth + Rate Limiting"]
    end

    subgraph DefaultNS["default Namespace (Workloads)"]
        Frontend["Frontend Service (Nginx)"]
        Backend["Backend Service (FastAPI)<br/>Instrumented /metrics + /simulate/*"]
        Frontend -->|"mTLS Tunnel"| Backend
    end

    subgraph MonitoringNS["monitoring Namespace (Observability Stack)"]
        Prometheus["Prometheus Server (:30090)<br/>15s Scrape Interval"]
        Alertmanager["Alertmanager (:30093)<br/>Grouping + Inhibition + Webhook"]
        Grafana["Grafana Server (:30300)<br/>Dashboard-as-Code Sidecar"]
        DashConfigMap["ConfigMap: parallax-red-dashboard<br/>(label: grafana_dashboard='1')"]

        DashConfigMap -.->|"Auto-Discovered by Sidecar"| Grafana
        Prometheus ==>|"Scrapes /metrics via ServiceMonitor"| Backend
        Prometheus ==>|"Scrapes /health"| Frontend
        Prometheus -->|"Fires Alerts (P95>500ms, 5xx>5%, Restarts>0)"| Alertmanager
        Grafana -->|"Queries Metrics (PromQL)"| Prometheus
    end

    subgraph Notifications["Alert Notification Channels"]
        SlackWebhook["DevOps Webhook / Slack Channel"]
        Alertmanager -->|"Dispatches JSON Payloads"| SlackWebhook
    end

    Clients --> KongProxy
    KongProxy --> Frontend
    KongProxy --> Backend
```

---

## 📈 RED Method Telemetry Formulations

The custom Grafana dashboard provisioned in `helm/observability/dashboards/parallax-red-dashboard.json` visualizes the three core golden signals:

| Signal | Metric Description | PromQL Query Formulation | Threshold / SLA |
|:---|:---|:---|:---:|
| **Rate (R)** | Total HTTP throughput by endpoint and method | `sum(rate(http_requests_total[1m])) by (method, endpoint)` | Nominal baseline |
| **Errors (E)** | HTTP 5xx error percentage over total traffic | `(sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))) * 100` | `< 5.0%` (Error Budget) |
| **Duration (D)** | 95th percentile (P95) request latency | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))` | `< 0.50s` (500ms SLA) |
| **Saturation** | Pod Memory Working Set / CPU Usage | `sum(container_memory_working_set_bytes{container="backend"}) by (pod)` | `< 256Mi` |

---

## 🚀 Running & Validating Week 5 Observability

### 1. Install / Upgrade Observability Stack via Helm
```bash
# Add official Prometheus Community chart repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack using our custom enterprise values
helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f helm/observability/values.yaml

# Apply the code-provisioned dashboard ConfigMap and Alert Rules
helm upgrade --install parallax-observability helm/observability \
  --namespace monitoring
```

### 2. Access Web Observability Portals
* **Grafana Dashboard:** `http://localhost:30300`  
  - *Username:* `admin` | *Password:* `parallax-admin-2026`  
  - *Dashboard:* Navigate to **Parallax Platform - Microservices RED Observability**
* **Prometheus Targets & Queries:** `http://localhost:30090`
* **Alertmanager Active Alarms:** `http://localhost:30093`

### 3. Generate Simulated Load & Verify Dashboard
Run the Python load testing script to generate realistic traffic across all endpoints:
```bash
python scripts/simulate_load.py --target http://localhost:32080 --rps 20 --duration 60
```

### 4. Deliberately Trigger Alarms & Test Runbook
Validate that Alertmanager detects anomalies according to [docs/RUNBOOK.md](docs/RUNBOOK.md):
```bash
# Trigger High Latency Alert (>500ms):
curl -s "http://localhost:32080/simulate/latency?seconds=1.5" -H "apikey: parallax-secret-key-2026"

# Trigger High Error Rate Alert (HTTP 500 Spike):
for i in {1..20}; do curl -s "http://localhost:32080/simulate/error?status_code=500" -H "apikey: parallax-secret-key-2026"; done

# Trigger Pod CrashLooping Alert:
curl -X POST "http://localhost:32080/simulate/crash" -H "apikey: parallax-secret-key-2026"
```

---


---

## 🐙 Week 4 Deliverable: GitOps Continuous Deployment (ArgoCD)

### Weekly Milestone Objectives
- [x] **ArgoCD Infrastructure:** Installed declarative GitOps engine via Helm into the dedicated `argocd` namespace with web UI exposed on NodePort 30088.
- [x] **Declarative GitOps Application (`gitops/application.yaml`):** Configured ArgoCD `Application` CRD monitoring the `main` branch of this repository (`helm/microservices` path) with automated sync, self-healing, and resource pruning enabled.
- [x] **Auto-Sync & Drift Reconciliation:** Validated that state changes in Git (e.g. scaling `frontend.replicaCount: 2`) are automatically detected and reconciled into the cluster within **2 seconds** without manual `kubectl` intervention.
- [x] **GitOps Alerting & Notifications (`gitops/notifications.yaml`):** Configured ArgoCD Notifications Controller with `trigger.on-sync-failed` to dispatch immediate alerts via Slack/Webhook upon sync or deployment errors.
- [x] **End-to-End CI/CD Handover:** Seamlessly bridged the CI pipeline (GitHub Actions publishing Git Commit SHA-tagged images to GHCR) with the CD engine (ArgoCD pulling and deploying desired states).

---

## 🏗️ GitOps Continuous Delivery Architecture

```mermaid
graph TB
    subgraph Developer["Developer Workflow"]
        CodeChange["1. Code / Helm Manifest Change"]
        GitPush["2. git push origin main"]
        CodeChange --> GitPush
    end

    subgraph GitHub["GitHub Ecosystem (Single Source of Truth)"]
        Repo["Git Repository (blosny/parallax-devops-platform)<br/>helm/microservices/values.yaml"]
        subgraph CI["GitHub Actions CI Pipeline"]
            LintTest["Linting & Syntax Checks"]
            BuildImg["Build & Tag with Git Commit SHA"]
            PushGHCR["Push to GHCR (ghcr.io)"]
            LintTest --> BuildImg --> PushGHCR
        end
        GitPush --> Repo
        GitPush --> CI
    end

    subgraph K8s["Kubernetes Cluster (Minikube v1.30.0)"]
        subgraph ArgoCD["argocd Namespace (GitOps Engine)"]
            AppController["ArgoCD Application Controller<br/>(Reconciliation Loop)"]
            RepoServer["ArgoCD Repo Server (Helm Template Engine)"]
            NotifController["ArgoCD Notifications Controller"]
            SlackAlerts["Slack Webhook / Alert Receiver"]

            AppController --- RepoServer
            AppController -->|"On Sync Failed"| NotifController
            NotifController -.-> SlackAlerts
        end

        subgraph DefaultNS["default Namespace (Workloads)"]
            FrontendPods["Frontend Pods (Replicas: 2)<br/>(Auto-Synced by ArgoCD)"]
            BackendPods["Backend Pod (FastAPI)<br/>(mTLS STRICT Boundary)"]
        end

        subgraph KongNS["kong Namespace"]
            KongProxy["Kong API Gateway (:32080)<br/>Rate Limiting + API Key Auth"]
        end
    end

    Repo -.->|"Polls Git Every 3m / Webhook"| RepoServer
    AppController ==>|"Reconciles Desired State (Auto-Sync: ~2s)"| DefaultNS
    KongProxy --> FrontendPods
    FrontendPods ==>|"mTLS Tunnel"| BackendPods
```

---

## 📂 Repository File Architecture

```text
parallax-devops-platform/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated CI Pipeline (Lint, Test, Build, GHCR Push)
│
├── docs/
│   ├── RUNBOOK.md                    # SRE Incident Response Runbook (Golden Signals & Alerts)
│   ├── NOTES.md                      # DevOps Engineering Architecture Decisions
│   └── TODO.md                       # 6-Week Progress & Deliverables Tracker
│
├── gitops/
│   ├── application.yaml              # ArgoCD Declarative Application (Microservices Auto-Sync)
│   ├── observability-application.yaml# ArgoCD Declarative Application (Observability Stack)
│   └── notifications.yaml            # ArgoCD Notifications ConfigMap (Slack/Webhook alerts)
│
├── helm/
│   ├── microservices/                # Consolidated Parameterized Helm Chart
│   │   ├── Chart.yaml                # Chart metadata (v1.0.0)
│   │   ├── values.yaml               # Parameterized configuration (Replicas, Probes, ServiceMonitor)
│   │   └── templates/
│   │       ├── backend-deployment.yaml   # Backend Deployment with Prometheus annotations
│   │       ├── backend-service.yaml      # Backend ClusterIP Service (:8000)
│   │       ├── frontend-deployment.yaml  # Frontend Deployment spec & probes
│   │       ├── frontend-service.yaml     # Frontend NodePort Service (:3000)
│   │       ├── servicemonitor.yaml       # Prometheus Operator ServiceMonitor custom resources
│   │       ├── ingress.yaml              # Kong Ingress rules (Public & Protected routes)
│   │       ├── kong-plugins.yaml         # KongPlugin (rate-limiting, key-auth, consumer, secret)
│   │       └── peer-authentication.yaml  # Istio PeerAuthentication policies (STRICT mTLS)
│   │
│   └── observability/                # Observability Stack Helm Chart & Values
│       ├── Chart.yaml                # Observability chart definition
│       ├── values.yaml               # Custom kube-prometheus-stack values (Grafana, Alertmanager)
│       ├── dashboards/
│       │   └── parallax-red-dashboard.json # 16-panel code-provisioned Grafana RED Dashboard
│       └── templates/
│           ├── dashboard-configmap.yaml    # ConfigMap provisioning dashboard via Grafana sidecar
│           └── alert-rules.yaml            # PrometheusRule CRD (Latency, Crash, 5xx Errors)
│
├── scripts/
│   ├── simulate_load.py              # Multi-threaded HTTP load generator for RED metrics
│   └── trigger_alerts.sh             # Automated script to deliberately trigger all 3 alert rules
│
├── services/
│   ├── backend/                      # Python FastAPI JSON API Microservice (/health, /info, /metrics)
│   └── frontend/                     # Lightweight HTTP Observability Dashboard
│
├── README.md                         # Primary project documentation
└── .gitignore                        # Standard enterprise ignore rules
```

---

## 🚀 Step-by-Step Reproduction & Deployment Guide

### 1. Initialize Minikube & Service Mesh Prerequisites
```bash
minikube start --kubernetes-version=v1.30.0 --memory=6144 --cpus=3 --driver=docker
```

### 2. Install ArgoCD via Helm
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd -n argocd \
  --set server.insecure=true \
  --set server.service.type=NodePort \
  --set server.service.nodePortHttp=30088 \
  --set notifications.enabled=true
```

### 3. Deploy GitOps Declarative Application
```bash
# Apply notification alert triggers
kubectl apply -f gitops/notifications.yaml

# Register repository with ArgoCD Application Controller
kubectl apply -f gitops/application.yaml
```

---

## 🧪 Verification & Proof of Execution

### A. ArgoCD Application Synchronized & Healthy
Inspecting the deployed `parallax-microservices` application managed by ArgoCD:
```bash
kubectl get application -n argocd
```
**Output:**
```text
NAME                     SYNC STATUS   HEALTH STATUS
parallax-microservices   Synced        Healthy
```

---

### B. Auto-Sync Timing & Reconciliation Speed
Querying the reconciliation operation lifecycle:
```bash
kubectl describe application parallax-microservices -n argocd
```
**Output:**
```text
Deploy Started At:  2026-10-27T04:01:20Z
Finished At:        2026-10-27T04:01:22Z
Sync Duration:      2 seconds
Sync Status:        Synced
Health Status:      Healthy
Sync Operation:     Sync operation to 1deb068abaee91083961c282063d8d09443faeef succeeded
```

---

### C. Self-Healing & Scaling Verification (`Replicas: 2`)
Demonstrating that changing `frontend.replicaCount: 2` in Git automatically scales the live pods without manual commands:
```bash
kubectl get pods -n default -l app=frontend
```
**Output:**
```text
NAME                        READY   STATUS    RESTARTS   AGE
frontend-c4dcfc68b-hd6hm    2/2     Running   0          14d
frontend-c4dcfc68b-x7m2p    2/2     Running   0          45s
```

---

### D. ArgoCD Sync Failure Notification Trigger
The notifications controller evaluates sync events according to the defined trigger:
```yaml
trigger.on-sync-failed: |
  - description: Application syncing has failed
    send:
      - app-sync-failed
    when: app.status.operationState != nil and app.status.operationState.phase in ['Error', 'Failed']
```
When an invalid manifest is committed, ArgoCD rejects the drift and dispatches a JSON webhook payload to Slack containing the commit SHA, repository URL, and exact failure reason.

---

### E. ArgoCD Web UI Access
To inspect the live GitOps DAG dependency graph in your browser:
```bash
# Port-forward or open via NodePort 30088:
kubectl port-forward svc/argocd-server -n argocd 8080:80
```
- **URL:** `http://localhost:8080`
- **Username:** `admin`
- **Initial Password:** Retrieve dynamically via:
  ```powershell
  $b64 = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
  [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64))
  ```

---

## 🛠️ Verified Prerequisites & CLI Toolchain

| Tool | Verified Version | Environment / Notes |
|:---|:---:|:---|
| **Prometheus** | `v2.50.0` (Chart `kube-prometheus-stack`) | Time-series metrics collection & PromQL engine |
| **Grafana** | `v10.3.0` (Chart `kube-prometheus-stack`) | Observability visualization & Dashboard-as-Code |
| **Alertmanager** | `v0.27.0` (Chart `kube-prometheus-stack`) | Alert routing, grouping, and notification dispatcher |
| **ArgoCD** | `v3.5.6` (Chart `v10.11.6`) | Declarative GitOps continuous delivery engine |
| **Kong API Gateway** | `v3.9.4` (Chart `v3.4.1`) | Cloud-native API Gateway & Ingress Controller |
| **Istio Service Mesh** | `v1.30.5` | Control plane (`istiod`) and Envoy data plane (`proxyv2`) |
| **Minikube** | `v1.39.0` (K8s `v1.30.0`) | Single-node Docker driver cluster (3 CPUs, 6144 MB RAM) |
| **Helm** | `v4.3.0` | Kubernetes package manager |
| **Docker Engine & CLI** | `v29.8.1` | Docker Desktop with WSL 2 integration |
| **kubectl** | `v1.36.1` | Kubernetes client CLI |
| **Git** | `v2.55.0` | Distributed version control |
