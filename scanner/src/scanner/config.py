"""Configuration management for scanner."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class ScannerConfig:
    """Scanner identification and BLE adapter configuration."""

    id: str
    bluetooth_adapter: str = "hci0"


@dataclass
class MQTTConfig:
    """MQTT broker connection configuration."""

    broker: str
    port: int = 1883
    topic_prefix: str = "bt-mqtt"
    qos: int = 1
    client_id_prefix: str = "scanner"
    keepalive: int = 60
    reconnect_delay: int = 5
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class DeduplicationConfig:
    """Advertisement deduplication configuration."""

    enabled: bool = False
    interval_seconds: int = 30
    strategy: str = "time_based"


@dataclass
class BlocklistConfig:
    """Device filtering configuration."""

    enabled: bool = False
    devices: list[str] = field(default_factory=list)


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    file: Optional[str] = None


@dataclass
class HeartbeatConfig:
    """Scanner heartbeat configuration."""

    enabled: bool = True
    interval_seconds: int = 60


@dataclass
class Config:
    """Complete scanner configuration."""

    scanner: ScannerConfig
    mqtt: MQTTConfig
    deduplication: DeduplicationConfig
    blocklist: BlocklistConfig
    logging: LoggingConfig
    heartbeat: HeartbeatConfig

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Substitute environment variables in values
        data = cls._substitute_env_vars(data)

        return cls(
            scanner=ScannerConfig(**data.get("scanner", {})),
            mqtt=MQTTConfig(**data.get("mqtt", {})),
            deduplication=DeduplicationConfig(**data.get("deduplication", {})),
            blocklist=BlocklistConfig(**data.get("blocklist", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            heartbeat=HeartbeatConfig(**data.get("heartbeat", {})),
        )

    @staticmethod
    def _substitute_env_vars(data: Any) -> Any:
        """Recursively substitute ${VAR} patterns with environment variables."""
        if isinstance(data, dict):
            return {k: Config._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Config._substitute_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            var_name = data[2:-1]
            return os.getenv(var_name, data)
        return data
