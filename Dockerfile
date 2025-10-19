# Dockerfile - With proper Chrome support
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    postgresql-client \
    redis-tools \
    chromium \
    chromium-driver \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python entrypoint
COPY docker-entrypoint.py /usr/local/bin/docker-entrypoint.py
RUN chmod +x /usr/local/bin/docker-entrypoint.py

# Copy application
COPY app/ ./app/

# Create directories with proper permissions
RUN mkdir -p /app/data/csvs && \
    mkdir -p /tmp/.X11-unix && \
    mkdir -p /root/.cache/selenium && \
    chmod -R 777 /app/data && \
    chmod -R 777 /tmp && \
    chmod -R 777 /root/.cache

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    DISPLAY=:99

# Use Python entrypoint
ENTRYPOINT ["python3", "/usr/local/bin/docker-entrypoint.py"]

# Default command
CMD ["python", "-m", "app.main"]
