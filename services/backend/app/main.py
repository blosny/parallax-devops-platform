"""
Parallax DevOps Platform - Backend Microservice
Production-grade FastAPI JSON API implementing standardized /health and /info endpoints.
"""

from datetime import datetime, timezone
import os
import sys
import time
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Application metadata & environment configurations
SERVICE_NAME: str = os.getenv("SERVICE_NAME", "backend-service")
APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# Record server boot timestamp to calculate uptime accurately
START_TIME: float = time.time()

app = FastAPI(
    title="Parallax DevOps Platform - Backend API",
    description="Enterprise-grade FastAPI microservice with /health and /info contracts.",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for internal frontend microservice communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Parameterized or restricted in production service mesh
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
