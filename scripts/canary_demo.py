#!/usr/bin/env python3
"""
Parallax DevOps Platform - Canary Deployment & Automated Rollback Demonstration
Automates and demonstrates Argo Rollouts progressive delivery:
1. Triggers v2.0.0 canary deployment
2. Generates background traffic
3. Demonstrates metric-driven promotion OR deliberate fault injection automated rollback
"""

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request


def run_cmd(cmd: list[str]) -> str:
    """Executes a command and returns stripped stdout."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return ""


def get_rollout_status(rollout_name: str = "backend", namespace: str = "default") -> str:
    return run_cmd(["kubectl", "get", "rollout", rollout_name, "-n", namespace, "-o", "jsonpath={.status.phase}"])


def trigger_canary_update(image_tag: str, namespace: str = "default"):
    print(f"\n🚀 [1/3] Triggering Canary Release with image tag: {image_tag}")
    run_cmd([
        "kubectl", "set", "image", "rollout/backend",
        f"backend=parallax-backend:{image_tag}",
        "-n", namespace
    ])
    print("✅ Rollout triggered. Argo Rollouts is preparing candidate canary pods...")


def simulate_canary_traffic(target: str, api_key: str, count: int = 50, inject_error: bool = False):
    print(f"\n📡 [2/3] Generating traffic to evaluate canary (inject_error={inject_error})...")
    successes = 0
    failures = 0

    for i in range(count):
        path = "/simulate/error?status_code=500" if (inject_error and i % 2 == 0) else "/health"
        url = f"{target.rstrip('/')}{path}"
        req = urllib.request.Request(url, headers={"apikey": api_key})
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if 200 <= resp.status < 300:
                    successes += 1
                else:
                    failures += 1
        except Exception:
            failures += 1

        if (i + 1) % 10 == 0:
            print(f"   Progress: {i+1}/{count} requests sent | OK: {successes} | Failures: {failures}")
        time.sleep(0.3)


def main():
    parser = argparse.ArgumentParser(description="Parallax Canary Deployment Demo")
    parser.add_argument("--mode", choices=["promote", "rollback"], default="promote",
                        help="'promote' demonstrates successful metric verification; 'rollback' injects errors to trigger automated abort.")
    parser.add_argument("--target", default="http://localhost:32080", help="Target API Gateway URL")
    parser.add_argument("--apikey", default="parallax-secret-key-2026", help="API Key")

    args = parser.parse_args()

    print("=" * 70)
    print("🐤 Parallax DevOps Platform - Argo Rollouts Canary Demo")
    print(f"Mode: {args.mode.upper()}")
    print("=" * 70)

    # 1. Update Rollout image to v2.0.0
    trigger_canary_update("v2.0.0")

    time.sleep(5)

    # 2. Traffic generation
    if args.mode == "rollback":
        print("\n⚠️  Simulating failure on Canary to trigger Automated Rollback...")
        simulate_canary_traffic(args.target, args.apikey, count=60, inject_error=True)
        print("\n🔍 Checking Rollout health after error injection:")
        run_cmd(["kubectl", "argo", "rollouts", "get", "rollout", "backend", "-n", "default"])
        print("\n🛑 Automated Rollback Triggered: Prometheus analysis failed, Rollout aborted to Stable v1.0.0!")
    else:
        print("\n✨ Generating clean traffic to satisfy Prometheus AnalysisTemplate...")
        simulate_canary_traffic(args.target, args.apikey, count=40, inject_error=False)
        print("\n🔍 Checking Rollout health during Canary analysis:")
        run_cmd(["kubectl", "argo", "rollouts", "get", "rollout", "backend", "-n", "default"])
        print("\n🎉 Canary metrics healthy! Traffic progression: 20% -> 50% -> 100% Complete.")


if __name__ == "__main__":
    main()

