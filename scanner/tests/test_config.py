"""Tests for configuration module."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from scanner.config import Config


def test_config_from_file():
    """Test loading configuration from file."""
    config_content = """
scanner:
  id: test-scanner
  bluetooth_adapter: hci0

mqtt:
  broker: mqtt.example.com
  port: 1883
  topic_prefix: bt-mqtt
  qos: 1

deduplication:
  enabled: false
  interval_seconds: 30

blocklist:
  enabled: false
  devices: []

logging:
  level: INFO
  format: json

heartbeat:
  enabled: false
  interval_seconds: 60
"""

    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        config_path = Path(f.name)

    try:
        config = Config.from_file(config_path)

        assert config.scanner.id == "test-scanner"
        assert config.scanner.bluetooth_adapter == "hci0"
        assert config.mqtt.broker == "mqtt.example.com"
        assert config.mqtt.port == 1883
        assert config.deduplication.enabled is False
        assert config.blocklist.enabled is False
        assert config.logging.level == "INFO"
        assert config.heartbeat.enabled is False
    finally:
        config_path.unlink()


def test_config_file_not_found():
    """Test error when configuration file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        Config.from_file(Path("nonexistent.yaml"))
