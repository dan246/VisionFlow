# Enhanced VisionFlow Web Service with Modern Features
FROM node:18-alpine AS frontend-builder

# Build modern frontend assets
WORKDIR /frontend
COPY package*.json ./
RUN npm ci --only=production

FROM python:3.11-slim

# Set environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies with security updates
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    for i in 1 2 3; do \
        apt-get update && break || \
        (echo "Retry $i failed, waiting 10 seconds..." && sleep 10); \
    done && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p logs static/dist && \
    chown -R app:app /app && \
    chmod 755 /app/logs

# Create a startup script to handle permissions
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'mkdir -p /app/logs' >> /start.sh && \
    echo 'chown -R app:app /app/logs' >> /start.sh && \
    echo 'chmod 755 /app/logs' >> /start.sh && \
    echo 'exec "$@"' >> /start.sh && \
    chmod +x /start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import redis; r=redis.Redis(host='${REDIS_HOST:-redis}', port=${REDIS_PORT:-6379}); r.ping()" || exit 1

# Set entrypoint to handle permissions first
ENTRYPOINT ["/start.sh"]

# Run application
CMD ["su", "-s", "/bin/sh", "app", "-c", "python app.py"]
