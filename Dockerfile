# GitHound Docker Image
# Multi-stage build for optimal image size and security

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for building
# Combine update, install, and cleanup in single layer for smaller image
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Install UV for faster dependency management (cache this layer)
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies only (without source code for better caching)
RUN uv pip install --no-cache .

# Production stage
FROM python:3.11-slim as production

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG GITHOUND_VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF

# Add labels for metadata
LABEL org.opencontainers.image.title="GitHound" \
      org.opencontainers.image.description="Advanced Git repository analysis tool with MCP server capabilities" \
      org.opencontainers.image.version="${GITHOUND_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/AstroAir/GitHound" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="GitHound Contributors" \
      org.opencontainers.image.documentation="https://github.com/AstroAir/GitHound/blob/main/README.md"

# Install runtime system dependencies (minimal set for production)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Create non-root user for security
RUN groupadd -r githound && useradd -r -g githound -d /app -s /bin/bash githound

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create necessary directories first (before copying code)
RUN mkdir -p /app/data /app/logs /app/cache \
    && chown -R githound:githound /app

# Copy application code (do this after creating directories for better caching)
COPY --chown=githound:githound githound/ ./githound/
COPY --chown=githound:githound pyproject.toml README.md LICENSE ./

# Switch to non-root user
USER githound

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GITHOUND_DATA_DIR=/app/data \
    GITHOUND_LOG_DIR=/app/logs \
    GITHOUND_CACHE_DIR=/app/cache

# Health check with improved configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports (document both web and MCP server ports)
EXPOSE 8000 3000

# Default command (can be overridden)
# Use exec form for better signal handling
CMD ["uvicorn", "githound.web.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# Development stage (for local development with hot reload)
FROM production as development

# Switch back to root to install development dependencies
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install development Python dependencies
RUN pip install --no-cache-dir \
    watchfiles \
    debugpy

# Switch back to githound user
USER githound

# Override command for development with hot reload
CMD ["uvicorn", "githound.web.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
