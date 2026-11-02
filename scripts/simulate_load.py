#!/usr/bin/env python3
"""
Parallax DevOps Platform - Production Load & Traffic Simulator
Simulates continuous multi-threaded HTTP traffic against Kong API Gateway and microservices
to drive RED metrics (Rate, Errors, Duration) for Grafana dashboards and trigger Alertmanager alerts.
"""

import argparse
import concurrent.futures
import random
import sys
import time
import urllib.error
import urllib.request

DEFAULT_TARGET = "http://localhost:32080"
DEFAULT_API_KEY = "parallax-secret-key-2026"

ENDPOINTS = [
    ("/", 0.20),
    ("/health", 0.40),
    ("/info", 0.30),
    ("/metrics", 0.10),
]


def send_request(url: str, api_key: str, timeout: float = 5.0) -> tuple[int, float]:
    """Sends a single HTTP GET request with the required Kong API key."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Parallax-LoadTester/1.0",
            "apikey": api_key,
        },
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            duration = time.time() - start
            return response.status, duration
    except urllib.error.HTTPError as e:
        duration = time.time() - start
        return e.code, duration
    except Exception as e:
        duration = time.time() - start
        return 0, duration


def run_workload(target: str, api_key: str, rps: int, duration_sec: int, error_pct: float, latency_pct: float):
    print("=" * 70)
    print("🚀 Parallax Observability Traffic & Load Generator")
    print("=" * 70)
    print(f"Target Gateway : {target}")
    print(f"Target Rate    : ~{rps} req/sec")
    print(f"Total Duration : {duration_sec} seconds")
    print(f"Error Injection: {error_pct * 100:.1f}%")
    print(f"Latency Inject : {latency_pct * 100:.1f}%")
    print("=" * 70)

    start_time = time.time()
    total_requests = 0
    status_counts: dict[int, int] = {}
    latencies: list[float] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(10, rps * 2)) as executor:
        while time.time() - start_time < duration_sec:
            batch_start = time.time()
            futures = []

            for _ in range(rps):
                roll = random.random()
                if roll < error_pct:
                    path = "/simulate/error?status_code=500"
                elif roll < (error_pct + latency_pct):
                    path = "/simulate/latency?seconds=1.2"
                else:
                    # Pick normal endpoint based on weight
                    rand_val = random.random()
                    cumulative = 0.0
                    path = "/"
                    for ep, weight in ENDPOINTS:
                        cumulative += weight
                        if rand_val <= cumulative:
                            path = ep
                            break

                url = f"{target.rstrip('/')}{path}"
                futures.append(executor.submit(send_request, url, api_key))
                total_requests += 1

            for f in concurrent.futures.as_completed(futures):
                status_code, dur = f.result()
                status_counts[status_code] = status_counts.get(status_code, 0) + 1
                latencies.append(dur)

            # Throttle to match target RPS
            elapsed = time.time() - batch_start
            sleep_time = max(0.0, 1.0 - elapsed)
            time.sleep(sleep_time)

            elapsed_total = time.time() - start_time
            print(
                f"\r⏱️  Elapsed: {elapsed_total:4.1f}s | Requests: {total_requests:5d} | "
                f"2xx: {sum(v for k,v in status_counts.items() if 200 <= k < 300)} | "
                f"4xx: {sum(v for k,v in status_counts.items() if 400 <= k < 500)} | "
                f"5xx: {sum(v for k,v in status_counts.items() if 500 <= k < 600)}",
                end="",
                flush=True,
            )

    print("\n" + "=" * 70)
    print("📊 Load Simulation Completed!")
    print(f"Total Sent : {total_requests}")
    print("Status Codes Breakdown:")
    for code, count in sorted(status_counts.items()):
        print(f"  HTTP {code:3d}: {count:5d} ({count / total_requests * 100:.1f}%)")

    if latencies:
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        print(f"Latencies: P50 = {p50*1000:.1f}ms | P95 = {p95*1000:.1f}ms | P99 = {p99*1000:.1f}ms")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Parallax Observability Load Generator")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Target URL (Gateway or Service)")
    parser.add_argument("--apikey", default=DEFAULT_API_KEY, help="Kong API Key header value")
    parser.add_argument("--rps", type=int, default=15, help="Requests per second")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    parser.add_argument("--error-rate", type=float, default=0.05, help="Ratio of 500 errors to inject (0.0 to 1.0)")
    parser.add_argument("--latency-rate", type=float, default=0.05, help="Ratio of high-latency requests (0.0 to 1.0)")

    args = parser.parse_args()
    run_workload(
        target=args.target,
        api_key=args.apikey,
        rps=args.rps,
        duration_sec=args.duration,
        error_pct=args.error_rate,
        latency_pct=args.latency_rate,
    )


if __name__ == "__main__":
    main()

