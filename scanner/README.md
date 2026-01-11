# Scanner Agent

BLE advertisement scanner that publishes to MQTT.

## Overview

The scanner agent is a lightweight Python service that runs on Raspberry Pi Zero W (or any Linux system with Bluetooth). It passively scans for BLE advertisements and publishes them to MQTT for processing.

## Features

- **BLE Scanning**: Passive scanning using `bleak` library
- **MQTT Publishing**: Publishes to `bt-mqtt/raw/{scanner_id}`
- **Deduplication**: Reduces message volume (time-based)
- **Blocklist**: Filter unwanted devices
- **Heartbeat**: Periodic health/status messages
- **Configuration**: YAML-based configuration

## Quick Start

### Prerequisites

- Python 3.11+
- Bluetooth adapter (built-in or USB)
- MQTT broker accessible on network

### Installation

```bash
cd scanner

# Install dependencies with uv
uv sync

# Copy and edit configuration
cp config/scanner.example.yaml config/scanner.yaml
# Edit config/scanner.yaml with your settings

# Run scanner
uv run python -m scanner
```

### Configuration

Edit `config/scanner.yaml`:

```yaml
scanner:
  id: pi-zero-living-room  # Unique identifier
  bluetooth_adapter: hci0

mqtt:
  broker: mqtt.shypan.st
  port: 1883
  topic_prefix: bt-mqtt
  qos: 1

deduplication:
  enabled: true
  interval_seconds: 30

blocklist:
  enabled: true
  devices: []

logging:
  level: INFO
  format: json
```

## Deployment

### Raspberry Pi (systemd service)

```bash
# Copy service file
sudo cp scanner.service /etc/systemd/system/bt-mqtt-scanner.service

# Edit service file with correct paths
sudo systemctl edit bt-mqtt-scanner.service

# Enable and start
sudo systemctl enable bt-mqtt-scanner
sudo systemctl start bt-mqtt-scanner

# Check status
sudo systemctl status bt-mqtt-scanner
```

### Docker (alternative)

```bash
# Build image
docker build -f ../docker/scanner.Dockerfile -t bt-mqtt-scanner .

# Run with Bluetooth access
docker run -d \
  --name bt-mqtt-scanner \
  --privileged \
  -v $(pwd)/config/scanner.yaml:/app/config/scanner.yaml:ro \
  bt-mqtt-scanner
```

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Type checking
uv run mypy src

# Linting
uv run ruff check src
```

## Project Structure

```
scanner/
├── src/
│   └── scanner/
│       ├── __init__.py
│       ├── ble_scanner.py      # BLE scanning logic
│       ├── mqtt_client.py      # MQTT publishing
│       ├── deduplicator.py     # Advertisement deduplication
│       ├── blocklist.py        # Device filtering
│       └── config.py           # Configuration management
├── config/
│   └── scanner.example.yaml
├── tests/
├── pyproject.toml
└── README.md
```

## Troubleshooting

### Bluetooth permission errors

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Or run with sudo (not recommended for production)
sudo uv run python -m scanner
```

### Can't find Bluetooth adapter

```bash
# List adapters
hciconfig

# If adapter is down
sudo hciconfig hci0 up
```

### MQTT connection issues

```bash
# Test MQTT connection
mosquitto_pub -h mqtt.shypan.st -t test -m "hello"

# Check scanner logs
journalctl -u bt-mqtt-scanner -f
```

## Documentation

- [Architecture](../docs/architecture.md)
- [MQTT Schema](../docs/mqtt-schema.md)
- [Scanner Design](../docs/scanner.md)
- [Feature: BLE Scanner](../docs/features/phase-1/ble-scanner.md)
- [Feature: MQTT Publisher](../docs/features/phase-1/mqtt-publisher.md)

## Related ADRs

- [ADR-0001: Python Scanner](../docs/decisions/0001-python-scanner.md)
- [ADR-0005: Deduplication Strategy](../docs/decisions/0005-deduplication-strategy.md)
- [ADR-0007: Scanner ID Configuration](../docs/decisions/0007-scanner-id-manual-config.md)
- [ADR-0009: MQTT Failure Handling](../docs/decisions/0009-mqtt-failure-drop-messages.md)
