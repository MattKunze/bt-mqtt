# Scanner Development Guide

This guide covers local development and testing of the BLE scanner agent.

## Prerequisites

- Python 3.11+
- `uv` package manager
- Bluetooth adapter (for actual scanning)
- MQTT broker (mqtt.shypan.st or local Mosquitto)

## Setup

### 1. Install dependencies

```bash
cd scanner

# Install all dependencies including dev tools
uv sync --all-extras
```

### 2. Create configuration

```bash
# Copy example configuration
cp config/scanner.example.yaml config/scanner.yaml

# Edit configuration
# Set scanner.id to a unique identifier
# Update mqtt.broker if using local broker
nano config/scanner.yaml
```

### 3. Test without Bluetooth (optional)

For development without Bluetooth hardware, you can mock the scanner or test individual components.

## Running the Scanner

### Basic usage

```bash
# Run scanner (will look for config/scanner.yaml)
uv run python -m scanner

# Run with custom config path
# (not yet implemented - uses standard paths)
```

### Expected output

```
{"asctime": "2026-01-11 12:00:00", "name": "scanner.app", "levelname": "INFO", "message": "Starting BT-MQTT Scanner (ID: scanner-01)"}
{"asctime": "2026-01-11 12:00:00", "name": "scanner.mqtt_publisher", "levelname": "INFO", "message": "Connecting to MQTT broker mqtt.shypan.st:1883"}
{"asctime": "2026-01-11 12:00:01", "name": "scanner.mqtt_publisher", "levelname": "INFO", "message": "Connected to MQTT broker"}
{"asctime": "2026-01-11 12:00:01", "name": "scanner.ble_scanner", "levelname": "INFO", "message": "Starting BLE scanner on adapter hci0"}
{"asctime": "2026-01-11 12:00:01", "name": "scanner.ble_scanner", "levelname": "INFO", "message": "BLE scanner started successfully"}
```

### Stopping the scanner

Press `Ctrl+C` or send `SIGTERM`:

```
{"asctime": "2026-01-11 12:05:00", "name": "scanner.app", "levelname": "INFO", "message": "Shutdown requested"}
{"asctime": "2026-01-11 12:05:00", "name": "scanner.app", "levelname": "INFO", "message": "Shutting down scanner"}
{"asctime": "2026-01-11 12:05:00", "name": "scanner.ble_scanner", "levelname": "INFO", "message": "Stopping BLE scanner"}
{"asctime": "2026-01-11 12:05:00", "name": "scanner.app", "levelname": "INFO", "message": "Scanner shutdown complete"}
```

## Development Workflow

### Type checking

```bash
uv run mypy src
```

### Linting

```bash
uv run ruff check src
```

### Auto-fixing lint issues

```bash
uv run ruff check --fix src
```

### Running tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=scanner

# Run specific test
uv run pytest tests/test_config.py

# Run with verbose output
uv run pytest -v
```

## Testing with MQTT

### Using mosquitto command-line tools

Subscribe to all scanner messages:

```bash
# Subscribe to raw advertisements
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/raw/#' -v

# Subscribe to status messages (when heartbeat enabled)
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/scanner/+/status' -v
```

### Expected MQTT messages

Raw advertisement on topic `bt-mqtt/raw/scanner-01`:

```json
{
  "version": "1.0",
  "timestamp": "2026-01-11T12:34:56.789Z",
  "scanner_id": "scanner-01",
  "device": {
    "address": "AA:BB:CC:DD:EE:FF",
    "address_type": "public",
    "rssi": -65,
    "name": "Sensor-01"
  },
  "manufacturer_data": {
    "0x004c": "AgEGGwP/TAANAX4M8g=="
  },
  "service_data": {},
  "service_uuids": [],
  "raw_data": ""
}
```

## Troubleshooting

### Bluetooth permission errors

On Linux, you may need Bluetooth permissions:

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Log out and back in for group changes to take effect

# Or run with sudo (not recommended for development)
sudo uv run python -m scanner
```

### Cannot find Bluetooth adapter

```bash
# List available adapters
hciconfig

# Check if adapter is up
hciconfig hci0

# Bring adapter up if needed
sudo hciconfig hci0 up
```

### MQTT connection fails

```bash
# Test MQTT connection
mosquitto_pub -h mqtt.shypan.st -t test -m "hello"

# Check if broker is accessible
ping mqtt.shypan.st

# Try with local broker instead
# 1. Install mosquitto: apt install mosquitto
# 2. Update config/scanner.yaml:
#    mqtt:
#      broker: localhost
```

### No advertisements received

- Check that Bluetooth devices are nearby and advertising
- Try with your phone's Bluetooth on
- Enable debug logging in config/scanner.yaml:
  ```yaml
  logging:
    level: DEBUG
  ```
- Check scanner logs for BLE errors

### Import errors

```bash
# Make sure dependencies are installed
uv sync

# Check Python version
python --version  # Should be 3.11+
```

## Project Structure

```
scanner/
├── src/
│   └── scanner/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # Entry point
│       ├── app.py               # Main application
│       ├── ble_scanner.py       # BLE scanning logic
│       ├── mqtt_publisher.py    # MQTT publishing
│       ├── config.py            # Configuration management
│       └── logging_config.py    # Logging setup
├── tests/
│   ├── __init__.py
│   └── test_config.py           # Configuration tests
├── config/
│   ├── scanner.example.yaml     # Example config
│   └── scanner.yaml             # Your config (gitignored)
├── pyproject.toml               # Project metadata and deps
└── README.md                    # User documentation
```

## Next Steps

- Test scanner with real Bluetooth devices
- Set up subscriber service to receive MQTT messages
- Implement Phase 2 features (deduplication, blocklist, heartbeat)

## Related Documentation

- [Scanner Feature Spec](../docs/features/phase-1/ble-scanner.md)
- [MQTT Publisher Feature Spec](../docs/features/phase-1/mqtt-publisher.md)
- [MQTT Schema](../docs/mqtt-schema.md)
- [Architecture Overview](../docs/architecture.md)
