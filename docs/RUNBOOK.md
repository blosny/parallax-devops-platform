# 📖 SRE Runbook & Incident Response Guide

> **Platform:** Parallax DevOps Platform  
> **Environment:** Production & Staging Clusters  
> **Classification:** SRE & DevOps Operational Handbook  
> **Version:** 1.0.0 (Week 5 Deliverable)

---

## 🎯 Executive Overview & Golden Signals Policy

This runbook defines the standardized operational procedures for on-call SREs and DevOps engineers responding to automated alerts dispatched by **Prometheus Alertmanager**.

### Service Level Objectives (SLOs) & Error Budgets
| Metric Category | Golden Signal | Target SLA / SLO | Alert Trigger Threshold |
|:---|:---|:---:|:---:|
| **Latency** | Duration (D) | 99% requests < 500ms | P95 > 500ms for 1m |
| **Availability** | Errors (E) | 99.9% success rate | 5xx Errors > 5% for 1m |
| **Throughput** | Rate (R) | Capacity up to 500 rps | Sudden drop > 80% |
| **Stability** | Saturation (USE) | Zero unexpected restarts | Restart rate > 0 in 5m |

---

## 🚨 Incident Severity Classification Matrix

* **SEV-1 (Critical):** Core user-facing services unavailable, error rate > 5%, or pod crash looping. Immediate triage required (MTTR target: < 15 minutes).
* **SEV-2 (Warning / Degraded):** High latency or performance degradation without total loss of service. Triage within 30 minutes.
* **SEV-3 (Informational):** Non-impacting warning, certificate expiry > 14 days, or scheduled maintenance.

---

## 🔍 Alert Response Runbooks

---

### 1. `HighRequestLatency`
* **Severity:** `SEV-2 (Warning)`
* **Alert Expression:**
  ```promql
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) > 0.50
  ```
* **Condition:** The 95th percentile (P95) latency exceeds 500 milliseconds for longer than 1 continuous minute.

#### Symptoms & Business Impact
* Frontend UI feels sluggish; API requests take longer to complete.
* Potential cascade timeouts across Istio service mesh and Kong API Gateway.

#### Triage & Investigation Steps
1. **Inspect Live Metrics in Grafana:**
   * Navigate to `http://localhost:30300` -> **Parallax Platform - Microservices RED Observability**.
   * Review panel: **Latency Distribution Quantiles (P50, P90, P95, P99)** to see if latency is localized to a single endpoint or widespread.
2. **Check Pod Resource Constraints:**
   ```bash
   kubectl top pods -n default
   ```
   Look for CPU throttling (`rate(container_cpu_usage_seconds_total) >= limits.cpu`).
3. **Examine Istio Envoy Proxy Latency:**
   ```bash
   kubectl logs -l app=backend -n default -c istio-proxy --tail=100
   ```

#### Mitigation & Remediation
* **Horizontal Scaling:** If CPU is near limits, increase replica count:
  ```bash
  kubectl scale deployment backend --replicas=3 -n default
  ```
* **Rate Limiting:** If incoming traffic spiked, tighten Kong Rate Limiting plugin via `helm/microservices/values.yaml`.

#### Deliberate Trigger & Verification Procedure
Run the following curl loop against the backend to inject a 1.5-second sleep into responses:
```bash
for i in {1..40}; do
  curl -s "http://localhost:32080/simulate/latency?seconds=1.5" -H "apikey: parallax-secret-key-2026"
  sleep 0.5
done
```
*Expected Result:* Within 60 seconds, Prometheus transitions `HighRequestLatency` from `Pending` to `Firing`, and Alertmanager routes notification to the configured channel.

---

### 2. `PodCrashLooping`
* **Severity:** `SEV-1 (Critical)`
* **Alert Expression:**
  ```promql
  (rate(kube_pod_container_status_restarts_total{container=~"backend|frontend"}[5m]) * 60) > 0
  ```
* **Condition:** A microservice container has terminated and restarted at least once within a 5-minute evaluation window.

#### Symptoms & Business Impact
* Service downtime, 502/503 errors returned to Kong Gateway, partial traffic loss.

#### Triage & Investigation Steps
1. **Identify the Failing Pod:**
   ```bash
   kubectl get pods -n default -o wide
   ```
2. **Inspect Container Termination Reason & Exit Code:**
   ```bash
   kubectl describe pod -l app=backend -n default
   ```
   *Look under `Last State`:*
   * `Exit Code 137`: **OOMKilled** (Out Of Memory). Container exceeded `resources.limits.memory`.
   * `Exit Code 1` or `143`: Unhandled exception or SIGTERM during health probe timeout.
3. **Inspect Crash Logs of Previous Instance:**
   ```bash
   kubectl logs -l app=backend -n default -c backend --previous --tail=150
   ```

#### Mitigation & Remediation
* **If OOMKilled:** Update `helm/microservices/values.yaml` memory limits from `256Mi` to `512Mi`, commit and let ArgoCD sync.
* **If Bad Deployment:** Trigger ArgoCD rollback to the previous stable Git commit SHA:
  ```bash
  argocd app rollback parallax-microservices
  ```

#### Deliberate Trigger & Verification Procedure
Trigger deliberate process termination via the fault injection endpoint:
```bash
curl -X POST "http://localhost:32080/simulate/crash" -H "apikey: parallax-secret-key-2026"
```
*Expected Result:* The container exits immediately, Kubernetes restarts the pod, and Prometheus fires the `PodCrashLooping` alert.

---

### 3. `HighHttpErrorRate`
* **Severity:** `SEV-1 (Critical)`
* **Alert Expression:**
  ```promql
  (sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))) * 100 > 5
  ```
* **Condition:** HTTP 5xx server errors account for more than 5% of all incoming requests over a 1-minute period.

#### Symptoms & Business Impact
* Users receive `HTTP 500 Internal Server Error` or `503 Service Unavailable`.
* Breaches the 99.9% availability SLA.

#### Triage & Investigation Steps
1. **Review Error Rate & Breakdown in Grafana:**
   * Open Grafana panel **Error Percentage (4xx vs 5xx)** to determine exact error volume.
2. **Check Application Logs for Stack Traces:**
   ```bash
   kubectl logs -l app=backend -n default -c backend --tail=200 | grep -E "ERROR|Exception|Traceback"
   ```
3. **Verify Upstream Dependencies & mTLS:**
   * Verify Istio mTLS mutual authentication is healthy:
     ```bash
     istioctl proxy-status
     ```

#### Mitigation & Remediation
* If a new release introduced the bug, revert the Git commit SHA in `helm/microservices/values.yaml`.
* If a downstream dependent service is saturated, restart the affected service:
  ```bash
  kubectl rollout restart deployment backend -n default
  ```

#### Deliberate Trigger & Verification Procedure
Simulate an error spike by sending HTTP 500 responses:
```bash
for i in {1..30}; do
  curl -s "http://localhost:32080/simulate/error?status_code=500" -H "apikey: parallax-secret-key-2026"
  sleep 0.2
done
```
*Expected Result:* Grafana error panel spikes to 100%, and `HighHttpErrorRate` alert fires in Alertmanager.

---

### 4. `MicroserviceTargetDown`
* **Severity:** `SEV-1 (Critical)`
* **Alert Expression:**
  ```promql
  up{job=~".*backend.*|.*frontend.*"} == 0
  ```
* **Condition:** Prometheus scrape agent cannot reach the `/metrics` endpoint of the microservice for 1 minute.

#### Symptoms & Business Impact
* Total blackout of metrics telemetry; pod is dead, network is partitioned, or scrape port is blocked.

#### Triage & Investigation Steps
1. **Check Service Endpoints:**
   ```bash
   kubectl get endpoints -n default
   ```
2. **Verify Pod Status:**
   ```bash
   kubectl get pods -n default
   ```
3. **Verify ServiceMonitor Selector Match:**
   ```bash
   kubectl get servicemonitor -n default
   ```

#### Deliberate Trigger & Verification Procedure
Scale the backend deployment to 0 replicas:
```bash
kubectl scale deployment backend --replicas=0 -n default
```
*Expected Result:* Prometheus loses the scrape target (`up == 0`), firing `MicroserviceTargetDown` after 1 minute. Restore with `--replicas=1`.

---

## 📋 Post-Incident Review (Blameless Post-Mortem)

After every SEV-1 incident, the team must complete a blameless post-mortem document covering:
1. **Incident Timeline:** First alert trigger time -> triage start -> mitigation -> full resolution.
2. **Root Cause Analysis (5 Whys):** Technical and procedural factors that led to the event.
3. **Action Items & Preventative Measures:** Code fixes, alert rule fine-tuning, or architectural adjustments to prevent recurrence.

