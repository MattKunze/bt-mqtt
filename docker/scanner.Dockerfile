# Dockerfile for scanner agent (Raspberry Pi deployment)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Bluetooth
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bluetooth \
        bluez \
        libbluetooth-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY scanner/pyproject.toml scanner/uv.lock ./

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --frozen

# Copy application code
COPY scanner/src ./src

# Copy config directory (will be overridden by volume mount)
RUN mkdir -p /app/config

# Scanner needs access to Bluetooth hardware
# Run with: --privileged or --device /dev/bus/usb

CMD ["uv", "run", "python", "-m", "scanner"]
