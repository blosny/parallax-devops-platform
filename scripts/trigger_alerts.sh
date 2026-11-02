#!/usr/bin/env bash
# ==============================================================================
# Parallax Observability - Automated Alert Trigger & Validation Script
# Deliberately triggers the 3 required Prometheus / Alertmanager rules:
#   1. HighLatencyAlert (injects >500ms delay)
#   2. HighHttpErrorRate (injects HTTP 500 errors)
#   3. PodCrashLooping (terminates backend process to trigger K8s restart)
# ==============================================================================

set -euo pipefail

TARGET="${1:-http://localhost:32080}"
API_KEY="${2:-parallax-secret-key-2026}"

echo "===================================================================="
echo "🎯 Parallax Alertmanager Test & Verification Suite"
echo "Target: $TARGET"
echo "===================================================================="

test_latency() {
  echo -e "\n[1/3] Triggering HighRequestLatency Alert (Injecting 1.5s delay)..."
  for i in $(seq 1 30); do
    curl -s -o /dev/null -w "%{http_code} (took %{time_total}s)\n" \
      "$TARGET/simulate/latency?seconds=1.5" \
      -H "apikey: $API_KEY" || true
    sleep 0.5
  done
  echo "✅ High latency requests dispatched. Check Alertmanager UI (:30093) for firing status."
}

test_errors() {
  echo -e "\n[2/3] Triggering HighHttpErrorRate Alert (Injecting HTTP 500 errors)..."
  for i in $(seq 1 40); do
    curl -s -o /dev/null -w "%{http_code}\n" \
      "$TARGET/simulate/error?status_code=500" \
      -H "apikey: $API_KEY" || true
    sleep 0.2
  done
  echo "✅ HTTP 500 error flood dispatched. Check Grafana error panel and Alertmanager."
}

test_crash() {
  echo -e "\n[3/3] Triggering PodCrashLooping Alert (Terminating backend container)..."
  curl -s -X POST "$TARGET/simulate/crash" \
    -H "apikey: $API_KEY" || true
  echo "✅ Crash signal sent. Kubernetes will restart the pod, firing PodCrashLooping alert."
}

case "${3:-all}" in
  latency) test_latency ;;
  errors)  test_errors ;;
  crash)   test_crash ;;
  all)
    test_latency
    test_errors
    test_crash
    ;;
  *)
    echo "Usage: $0 [TARGET_URL] [API_KEY] [latency|errors|crash|all]"
    exit 1
    ;;
esac

echo -e "\n===================================================================="
echo "🎉 Verification suite finished! Open Grafana (:30300) & Alertmanager (:30093)"
echo "===================================================================="

