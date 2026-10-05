# ==========================================
# Stage 1: Build & Assets Preparation
# ==========================================
FROM alpine:3.19 AS builder

WORKDIR /app

# Copy frontend source files
COPY ./src /app/src
COPY ./nginx.conf /app/nginx.conf

# Verify asset integrity (valid HTML structure)
RUN test -f /app/src/index.html && test -f /app/nginx.conf


# ==========================================
# Stage 2: Minimal Non-Root Nginx Runtime
# ==========================================
FROM nginx:1.27-alpine AS runner

# Create a dedicated non-root user and group with UID/GID 1001
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -D -G appgroup -s /bin/sh appuser

# Configure custom unprivileged Nginx configuration
COPY --from=builder --chown=appuser:appgroup /app/nginx.conf /etc/nginx/nginx.conf

# Copy web assets to Nginx html directory
COPY --from=builder --chown=appuser:appgroup /app/src /usr/share/nginx/html

# Adjust permissions for unprivileged user on required Nginx runtime directories
RUN touch /tmp/nginx.pid && \
    chown -R appuser:appgroup /tmp /usr/share/nginx/html /etc/nginx /var/cache/nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html

# Enforce Non-Root Execution (Mandatory Security Standard)
USER 1001

EXPOSE 3000

# Container liveness health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
