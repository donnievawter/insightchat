# Use Python 3.11 slim as base image
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/opt/uv-cache \
    UV_LINK_MODE=copy

# Install system dependencies (git needed for pip install from GitHub)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create app directory
WORKDIR /app

# Copy and install dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/opt/uv-cache,uid=1000,gid=1000 \
    uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create non-root user with home directory and uv directories
RUN groupadd -r appuser && useradd -r -g appuser -m appuser && \
    mkdir -p /opt/uv-cache /home/appuser/.local/share/uv && \
    chown -R appuser:appuser /app /opt/uv-cache /home/appuser
USER appuser

# Expose port
EXPOSE 5030

# Health check (using Python instead of curl for lightweight image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5030/chat')" || exit 1

# Set working directory to flask app
WORKDIR /app/flask-chat-app/src

# Run the application
CMD ["uv", "run", "app.py"]