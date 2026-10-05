# ==========================================
# Stage 1: Build & Dependencies Resolution
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies if needed and compile wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a separate prefix directory for clean copy
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==========================================
# Stage 2: Minimal Non-Root Runtime
# ==========================================
FROM python:3.11-slim AS runner

# Create a non-privileged user and group (UID/GID 1001)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Copy only pre-built Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code with non-root ownership
COPY --chown=appuser:appgroup ./app /app

# Switch to unprivileged user (Mandatory Security Standard)
USER 1001

# Environment configurations
ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Healthcheck for container runtime liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
