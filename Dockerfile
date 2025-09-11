# GitHound Docker Image
# Multi-stage build for optimal image size and security

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install UV for faster dependency management
RUN pip install uv

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN uv pip install -e .

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
      org.opencontainers.image.licenses="MIT"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r githound && useradd -r -g githound -d /app -s /bin/bash githound

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=githound:githound . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/cache \
    && chown -R githound:githound /app

# Switch to non-root user
USER githound

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GITHOUND_DATA_DIR=/app/data \
    GITHOUND_LOG_DIR=/app/logs \
    GITHOUND_CACHE_DIR=/app/cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 3000

# Default command (can be overridden)
CMD ["uvicorn", "githound.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
