# Parallax DevOps Platform

[![DevOps Internship](https://img.shields.io/badge/Parallax%20Labs-DevOps%20Internship-6366f1?style=flat-square)](https://www.parallaxlab.site/)
[![Track](https://img.shields.io/badge/Track%20B-6--Week%20Standard%20Program-10b981?style=flat-square)](https://www.parallaxlab.site/)
[![Week 1 Deliverable](https://img.shields.io/badge/Week%201-Accepted%20%26%20Verified-238636?style=flat-square)](#)
[![Week 2 Deliverable](https://img.shields.io/badge/Week%202-Complete%20%26%20Enforced-238636?style=flat-square)](#)

> **"Built different. Engineered better."**  
> A self-hosted enterprise infrastructure platform running entirely on local virtualization, engineered according to production-grade security, scalability, and 12-Factor principles.

---

## 📌 Executive Summary & Repository Lifecycle

This repository maintains the entire 6-week progressive infrastructure lifecycle, strictly honoring **The Single Repository Rule**.

| Milestone | Architecture Focus | Status | Core Technologies |
|:---|:---|:---:|:---|
| **Week 1** | Microservices & Containerization Foundation | **Accepted (100/100)** | FastAPI, Nginx Alpine, Docker Multi-Stage, Non-Root (`USER 1001`) |
| **Week 2** | Helm, Service Mesh & Strict mTLS | **Complete & Verified** | Minikube (K8s v1.30), Helm v4, Istio Service Mesh, Envoy Sidecars, Strict mTLS |
| **Week 3** | Ingress, Routing & Edge Gateway | Planned | Kong API Gateway, TLS Ingress, Path Routing, Rate Limiting |
| **Week 4** | Infrastructure as Code & Orchestration | Planned | Terraform, LocalStack, Automated Provisioning |
| **Week 5** | GitOps & Continuous Delivery | Planned | ArgoCD, Declarative Sync, Rollback Automation |
| **Week 6** | Observability, Monitoring & Capstone | Planned | Prometheus, Grafana, OpenTelemetry, Distributed Tracing |

---

## 🛡️ Week 2 Deliverable: Helm, Service Mesh & Strict mTLS

### Weekly Milestone Objectives
- [x] **Local Kubernetes Cluster (Minikube):** Provisioned on Docker driver (`v1.30.0`, 3 CPUs, 6144 MB RAM).
- [x] **Parameterized Helm Packaging (`/helm/microservices`):** Consolidated Backend and Frontend microservices into a single, reusable Helm Chart parameterized via `values.yaml`.
- [x] **Istio Service Mesh Installation:** Deployed `istio-base` and `istiod` (v1.30.5 control plane) via Helm into the dedicated `istio-system` namespace.
- [x] **Automatic Sidecar Injection:** Enabled namespace injection (`istio-injection=enabled`), provisioning Envoy proxies (`proxyv2:1.30.5`) alongside applications (`2/2` Ready pods).
- [x] **Strict Mutual TLS (mTLS):** Enforced Zero-Trust communication within the mesh using Istio `PeerAuthentication` (`mode: STRICT`).
- [x] **End-to-End Cryptographic Verification:** Proven that un-injected/external pods are denied access (`Connection reset by peer`, error 56), while in-mesh microservice traffic communicates seamlessly over mTLS.

---

## 🏗️ Week 2 Architecture & Service Mesh Mesh Boundary

```mermaid
graph TB
    subgraph K8s["Kubernetes Cluster (Minikube v1.30.0)"]
        subgraph IstioSystem["istio-system Namespace"]
            Istiod["istiod (Control Plane / CA)<br/>Pilot + Citadel v1.30.5"]
        end

        subgraph DefaultNS["default Namespace (istio-injection=enabled)"]
            subgraph PeerAuth["Security Policy: PeerAuthentication (mode: STRICT)"]
                subgraph FEPod["Frontend Pod (2/2 Ready)"]
                    FE_App["Frontend App<br/>(Nginx :3000 / Non-Root)"]
                    FE_Proxy["istio-proxy (Envoy)<br/>Client Cert + SPIFFE ID"]
                end

                subgraph BEPod["Backend Pod (2/2 Ready)"]
                    BE_App["Backend App<br/>(FastAPI :8000 / Non-Root)"]
                    BE_Proxy["istio-proxy (Envoy)<br/>Server Cert + TLS Terminator"]
                end
            end
        end

        subgraph ExternalNS["Un-injected Namespace / External Pod"]
            UnauthenticatedClient["Un-injected Pod<br/>(No Envoy Sidecar / Plain HTTP)"]
        end
    end

    Istiod -.->|Issues mTLS Certs / SPIFFE| FE_Proxy
    Istiod -.->|Issues mTLS Certs / SPIFFE| BE_Proxy

    FE_App -->|Plaintext Localhost Loopback| FE_Proxy
    FE_Proxy ==>|Encrypted Mutual TLS Tunnel :8000| BE_Proxy
    BE_Proxy -->|Plaintext Localhost Loopback| BE_App

    UnauthenticatedClient -.->|Plaintext HTTP GET| BE_Proxy
    BE_Proxy -.-x|DENIED: Connection Reset by Peer (Error 56)| UnauthenticatedClient
```

---

## 📂 Repository File Architecture

```text
parallax-devops-platform/
├── helm/
│   └── microservices/                # Parameterized Helm Chart
│       ├── Chart.yaml                # Chart metadata (v1.0.0)
│       ├── values.yaml               # Parameterized configuration & resource limits
│       └── templates/
│           ├── backend-deployment.yaml   # Backend Deployment spec & probes
│           ├── backend-service.yaml      # Backend ClusterIP Service (:8000)
│           ├── frontend-deployment.yaml  # Frontend Deployment spec & probes
│           ├── frontend-service.yaml     # Frontend NodePort Service (:3000 -> :30080)
│           └── peer-authentication.yaml  # Istio PeerAuthentication (mode: STRICT)
│
├── services/
│   ├── backend/                      # Python FastAPI JSON API Microservice
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py               # Core application logic (/health & /info)
│   │   ├── Dockerfile                # Multi-stage, non-root (USER 1001) build
│   │   ├── .dockerignore
│   │   └── requirements.txt
│   │
│   └── frontend/                     # Lightweight HTTP Server Microservice
│       ├── src/
│       │   └── index.html            # Parallax Labs dark-mode dashboard
│       ├── nginx.conf                # Unprivileged non-root Nginx reverse-proxy
│       ├── Dockerfile                # Multi-stage, non-root (USER 1001) build
│       └── .dockerignore
│
├── README.md                         # Primary project documentation
└── .gitignore                        # Standard enterprise ignore rules
```

---

## 🚀 Step-by-Step Reproduction & Deployment Guide

### 1. Initialize Local Kubernetes Cluster
```bash
minikube start --kubernetes-version=v1.30.0 --memory=6144 --cpus=3 --driver=docker
```

### 2. Load Container Images into Minikube
```bash
minikube image load parallax-backend:v1.0.0
minikube image load parallax-frontend:v1.0.0
```

### 3. Install Istio Service Mesh via Helm
```bash
# Add Istio Helm repository
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Install Istio Base CRDs
kubectl create namespace istio-system
helm install istio-base istio/base -n istio-system --wait

# Install Istio Control Plane (istiod)
helm install istiod istio/istiod -n istio-system --wait

# Enable Automatic Sidecar Injection on default namespace
kubectl label namespace default istio-injection=enabled
```

### 4. Deploy Microservices Helm Chart
```bash
# Validate chart syntax
helm lint ./helm/microservices

# Deploy microservices and strict mTLS policy
helm install microservices ./helm/microservices
```

---

## 🧪 Verification & Proof of Execution

### A. Dual-Container Pod Readiness (`2/2 Ready`)
Each pod runs both the application workload and the injected `istio-proxy` Envoy sidecar:
```bash
kubectl get pods -n default
```
**Output:**
```text
NAME                       READY   STATUS    RESTARTS   AGE
backend-78fc658b46-pz2kk   2/2     Running   0          2m
frontend-c4dcfc68b-hd6hm   2/2     Running   0          2m
```

### B. Strict mTLS PeerAuthentication Active
```bash
kubectl get peerauthentication -A
```
**Output:**
```text
NAMESPACE   NAME      MODE     AGE
default     default   STRICT   2m
```

### C. In-Mesh Authorized Communication (mTLS Succeeded)
Executing an HTTP request from inside the frontend pod (injected with Istio sidecar) to the backend service:
```bash
kubectl exec deployment/frontend -c frontend -- curl -s http://backend:8000/health
```
**Output:**
```json
{"status":"healthy","service":"backend-service","timestamp":"2026-10-12T09:55:41.173861+00:00","uptime_seconds":22.73}
```

### D. Zero-Trust Enforcement: Un-Injected Pod Blocked
Executing a request from an un-injected client pod (outside the Istio service mesh):
```bash
kubectl exec pod/curl-client -n legacy -- curl -v -m 5 http://backend.default.svc.cluster.local:8000/health
```
**Output (Connection Terminated by Envoy Sidecar):**
```text
* Host backend.default.svc.cluster.local:8000 was resolved.
* IPv4: 10.101.53.129
* Trying 10.101.53.129:8000...
* Established connection to backend.default.svc.cluster.local (10.101.53.129 port 8000)
> GET /health HTTP/1.1
> Host: backend.default.svc.cluster.local:8000
> User-Agent: curl/8.22.0
> Accept: */*
> 
* Recv failure: Connection reset by peer
* closing connection #0
curl: (56) Recv failure: Connection reset by peer
command terminated with exit code 56
```
> **Security Confirmation:** The Envoy proxy sidecar intercepted the unauthenticated plaintext request and immediately dropped the connection with TCP RST, successfully enforcing the Zero-Trust cryptographic boundary.

---

## 🛠️ Verified Prerequisites & CLI Toolchain

| Tool | Verified Version | Environment / Notes |
|:---|:---:|:---|
| **Minikube** | `v1.39.0` (K8s `v1.30.0`) | Single-node Docker driver cluster (3 CPUs, 6144 MB RAM) |
| **Istio Service Mesh** | `v1.30.5` | Control plane (`istiod`) and Envoy data plane (`proxyv2`) |
| **Helm** | `v4.3.0` | Kubernetes package manager |
| **Docker Engine & CLI** | `v29.8.1` | Docker Desktop with WSL 2 integration |
| **kubectl** | `v1.36.1` | Kubernetes client CLI |
| **Terraform** | `v1.16.2` | Infrastructure as Code (IaC) provisioning tool |
| **Git** | `v2.55.0` | Distributed version control |

---

## 👤 Author
- **Engineer:** Bilgisayar Mühendisliği / DevOps Engineer Intern
- **Program:** Parallax Labs - Track B: 6-Week Standard Program
- **Repository:** [github.com/blosny/parallax-devops-platform](https://github.com/blosny/parallax-devops-platform)
