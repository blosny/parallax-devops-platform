"""
Parallax DevOps Platform - Backend Microservice
Production-grade FastAPI JSON API implementing standardized /health, /info, /metrics endpoints
and RED (Rate, Errors, Duration) observability instrumentation.
"""

import asyncio
from datetime import datetime, timezone
import os
import sys
import threading
import time
from typing import Callable, Union
from fastapi import FastAPI, Request, Response, status, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# Application metadata & environment configurations
SERVICE_NAME: str = os.getenv("SERVICE_NAME", "backend-service")
APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# Record server boot timestamp to calculate uptime accurately
START_TIME: float = time.time()

# Prometheus metrics setup with guaranteed symbol definitions for linters
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None
    Histogram = None
    Gauge = None
    generate_latest = None
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    REGISTRY = None

# Initialize Prometheus metrics or in-memory fallback
_fallback_stats = {
    "requests_total": 0,
    "errors_total": 0,
    "latency_sum": 0.0,
    "status_counts": {},
}

if PROMETHEUS_AVAILABLE and Counter is not None and Histogram is not None and Gauge is not None:
    REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total number of HTTP requests processed by endpoint and status code.",
        ["method", "endpoint", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "http_request_duration_seconds",
        "Histogram of HTTP request latency in seconds.",
        ["method", "endpoint"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0),
    )
    IN_PROGRESS = Gauge(
        "http_requests_in_progress",
        "Number of HTTP requests currently being processed.",
        ["method", "endpoint"],
    )
else:
    REQUEST_COUNT = None
    REQUEST_LATENCY = None
    IN_PROGRESS = None

app = FastAPI(
    title="Parallax DevOps Platform - Backend API",
    description="Enterprise-grade FastAPI microservice with /health, /info, /metrics contracts.",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for internal frontend microservice communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next: Callable) -> Response:
    """HTTP middleware tracking RED metrics: Rate, Errors, Duration."""
    method = request.method
    path = request.url.path

    start_time = time.time()

    if PROMETHEUS_AVAILABLE and IN_PROGRESS is not None:
        IN_PROGRESS.labels(method=method, endpoint=path).inc()

    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        duration = time.time() - start_time
        if PROMETHEUS_AVAILABLE and IN_PROGRESS is not None and REQUEST_COUNT is not None and REQUEST_LATENCY is not None:
            IN_PROGRESS.labels(method=method, endpoint=path).dec()
            REQUEST_COUNT.labels(method=method, endpoint=path, status=str(status_code)).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)
        else:
            _fallback_stats["requests_total"] += 1
            if status_code >= 400:
                _fallback_stats["errors_total"] += 1
            _fallback_stats["latency_sum"] += duration
            key = f"{method}_{path}_{status_code}"
            _fallback_stats["status_counts"][key] = _fallback_stats["status_counts"].get(key, 0) + 1


class HealthResponse(BaseModel):
    """Pydantic schema for Kubernetes liveness/readiness probes."""
    status: str = Field(..., example="healthy")
    service: str = Field(..., example="backend-service")
    timestamp: str = Field(..., example="2026-10-05T10:30:00Z")
    uptime_seconds: float = Field(..., example=120.45)


class InfoResponse(BaseModel):
    """Pydantic schema for service catalog and metadata discovery."""
    service: str = Field(..., example="backend-service")
    version: str = Field(..., example="1.0.0")
    framework: str = Field(..., example="FastAPI")
    environment: str = Field(..., example="production")
    python_version: str = Field(..., example="3.11.8")


@app.get(
    "/",
    tags=["Root"],
    summary="Root Welcome Endpoint",
    description="Returns service welcome message and documentation links.",
)
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to Parallax DevOps Platform - Backend Microservice",
        "service": SERVICE_NAME,
        "docs": "/docs",
        "health": "/health",
        "info": "/info",
        "metrics": "/metrics",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Observability"],
    summary="Liveness and Readiness Health Check",
    description="Mandatory health probe endpoint returning service status, timestamp, and uptime.",
)
async def health_check() -> HealthResponse:
    uptime: float = round(time.time() - START_TIME, 2)
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime,
    )


@app.get(
    "/info",
    response_model=InfoResponse,
    status_code=status.HTTP_200_OK,
    tags=["Observability"],
    summary="Service Metadata Information",
    description="Mandatory service metadata endpoint for Kong Gateway and service mesh catalog.",
)
async def service_info() -> InfoResponse:
    return InfoResponse(
        service=SERVICE_NAME,
        version=APP_VERSION,
        framework="FastAPI",
        environment=ENVIRONMENT,
        python_version=sys.version.split()[0],
    )


@app.get(
    "/metrics",
    tags=["Observability"],
    summary="Prometheus Metrics Scrape Endpoint",
    description="Exposes application-level RED metrics in Prometheus exposition format.",
)
async def metrics() -> Response:
    if PROMETHEUS_AVAILABLE and generate_latest is not None and REGISTRY is not None:
        data = generate_latest(REGISTRY)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    
    # Text-formatted Prometheus fallback
    uptime = time.time() - START_TIME
    lines = [
        "# HELP http_requests_total Total number of HTTP requests processed.",
        "# TYPE http_requests_total counter",
        f'http_requests_total{{service="{SERVICE_NAME}"}} {_fallback_stats["requests_total"]}',
        "# HELP http_request_errors_total Total number of HTTP 4xx/5xx errors.",
        "# TYPE http_request_errors_total counter",
        f'http_request_errors_total{{service="{SERVICE_NAME}"}} {_fallback_stats["errors_total"]}',
        "# HELP process_uptime_seconds Application process uptime in seconds.",
        "# TYPE process_uptime_seconds gauge",
        f'process_uptime_seconds{{service="{SERVICE_NAME}"}} {uptime:.2f}',
    ]
    return PlainTextResponse("\n".join(lines) + "\n")


# ============================================================================
# Fault Injection & Testing Endpoints (For Runbook & Alert Verification)
# ============================================================================

@app.get(
    "/simulate/latency",
    tags=["Testing & Runbook"],
    summary="Simulate High Latency",
    description="Deliberately delays response to test High Latency alert rules.",
)
async def simulate_latency(
    seconds: float = Query(default=1.5, ge=0.1, le=10.0, description="Delay in seconds")
) -> dict[str, Union[str, float]]:
    await asyncio.sleep(seconds)
    return {
        "status": "simulated_latency_completed",
        "delay_seconds": seconds,
        "message": f"Response intentionally delayed by {seconds}s for Alertmanager validation.",
    }


@app.get(
    "/simulate/error",
    tags=["Testing & Runbook"],
    summary="Simulate HTTP Error",
    description="Deliberately raises an HTTP error status (e.g. 500, 503) to test High Error Rate alerts.",
)
async def simulate_error(
    status_code: int = Query(default=500, ge=400, le=599, description="HTTP Error code to return")
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=f"Intentional test failure with HTTP {status_code} for Alertmanager validation.",
    )


@app.post(
    "/simulate/crash",
    tags=["Testing & Runbook"],
    summary="Simulate Pod Crash",
    description="Deliberately terminates the backend process to test Pod CrashLoopBackOff alerts.",
)
async def simulate_crash() -> dict[str, str]:
    def _exit():
        time.sleep(0.5)
        os._exit(1)

    threading.Thread(target=_exit, daemon=True).start()
    return {
        "status": "terminating",
        "message": "Process exit scheduled in 0.5s to trigger Kubernetes restart and CrashLoop alert.",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
