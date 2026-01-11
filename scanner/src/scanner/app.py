"""Main scanner application."""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .ble_scanner import Advertisement, BLEScanner
from .config import Config
from .logging_config import setup_logging
from .mqtt_publisher import MQTTPublisher

logger = logging.getLogger(__name__)


class ScannerApp:
    """Main scanner application."""

    def __init__(self, config: Config):
        """Initialize scanner application.

        Args:
            config: Application configuration
        """
        self.config = config
        self.mqtt_publisher: Optional[MQTTPublisher] = None
        self.ble_scanner: Optional[BLEScanner] = None
        self._shutdown_event = asyncio.Event()
        self._start_time = time.time()
        self._devices_seen: set[str] = set()
        self._messages_published = 0
        self._heartbeat_task: Optional[asyncio.Task[None]] = None

    async def run(self) -> None:
        """Run the scanner application."""
        logger.info(f"Starting BT-MQTT Scanner (ID: {self.config.scanner.id})")

        try:
            # Initialize MQTT publisher
            self.mqtt_publisher = MQTTPublisher(
                broker=self.config.mqtt.broker,
                port=self.config.mqtt.port,
                scanner_id=self.config.scanner.id,
                topic_prefix=self.config.mqtt.topic_prefix,
                qos=self.config.mqtt.qos,
                client_id=f"{self.config.mqtt.client_id_prefix}-{self.config.scanner.id}",
                keepalive=self.config.mqtt.keepalive,
                username=self.config.mqtt.username,
                password=self.config.mqtt.password,
                on_connect_callback=self._on_mqtt_connect,
                on_disconnect_callback=self._on_mqtt_disconnect,
            )

            # Connect to MQTT broker
            self.mqtt_publisher.connect()

            # Wait for MQTT connection
            await asyncio.sleep(2)

            # Initialize BLE scanner
            self.ble_scanner = BLEScanner(
                scanner_id=self.config.scanner.id,
                adapter=self.config.scanner.bluetooth_adapter,
                callback=self._handle_advertisement,
            )

            # Start BLE scanning
            await self.ble_scanner.start()

            # Start heartbeat if enabled
            if self.config.heartbeat.enabled:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Wait for shutdown signal
            await self._shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        logger.info("Shutting down scanner")

        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Stop BLE scanner
        if self.ble_scanner:
            await self.ble_scanner.stop()

        # Disconnect MQTT
        if self.mqtt_publisher:
            self.mqtt_publisher.disconnect()

        logger.info("Scanner shutdown complete")

    def _handle_advertisement(self, advertisement: Advertisement) -> None:
        """Handle received BLE advertisement.

        Args:
            advertisement: Received advertisement
        """
        # Track device
        self._devices_seen.add(advertisement.device_address)

        # Check blocklist
        if self.config.blocklist.enabled:
            if advertisement.device_address in self.config.blocklist.devices:
                logger.debug(f"Blocked device: {advertisement.device_address}")
                return

        # Publish to MQTT
        if self.mqtt_publisher:
            success = self.mqtt_publisher.publish_advertisement(advertisement)
            if success:
                self._messages_published += 1

    def _on_mqtt_connect(self) -> None:
        """Called when MQTT connection established."""
        logger.info("MQTT connected - publishing will begin")
        # Send initial status
        asyncio.create_task(self._publish_status())

    def _on_mqtt_disconnect(self) -> None:
        """Called when MQTT connection lost."""
        logger.warning("MQTT disconnected - messages will be dropped until reconnected")

    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat/status publishing."""
        interval = self.config.heartbeat.interval_seconds

        while True:
            try:
                await asyncio.sleep(interval)
                await self._publish_status()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _publish_status(self) -> None:
        """Publish scanner status."""
        if not self.mqtt_publisher:
            return

        uptime = int(time.time() - self._start_time)
        mqtt_stats = self.mqtt_publisher.get_statistics()

        status_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
            "uptime_seconds": uptime,
            "metrics": {
                "messages_sent": self._messages_published,
                "messages_dropped": mqtt_stats["messages_failed"],
                "devices_seen": len(self._devices_seen),
                "devices_blocked": 0,  # TODO: track blocked count
            },
            "bluetooth": {
                "adapter": self.config.scanner.bluetooth_adapter,
                "status": "scanning",
                "errors": 0,  # TODO: track errors
            },
            "mqtt": {
                "connected": mqtt_stats["connected"],
                "reconnections": 0,  # TODO: track reconnections
            },
            "config": {
                "deduplication_enabled": self.config.deduplication.enabled,
                "deduplication_interval": self.config.deduplication.interval_seconds,
                "blocklist_count": len(self.config.blocklist.devices),
            },
        }

        self.mqtt_publisher.publish_status(status_data)

    def request_shutdown(self) -> None:
        """Request application shutdown."""
        logger.info("Shutdown requested")
        self._shutdown_event.set()


def main() -> None:
    """Main entry point."""
    # Find configuration file
    config_paths = [
        Path("config/scanner.yaml"),
        Path("/etc/bt-mqtt-scanner/scanner.yaml"),
        Path.home() / ".config" / "bt-mqtt-scanner" / "scanner.yaml",
    ]

    config_path = None
    for path in config_paths:
        if path.exists():
            config_path = path
            break

    if not config_path:
        print("Error: No configuration file found. Please create config/scanner.yaml")
        print("See config/scanner.example.yaml for reference")
        sys.exit(1)

    try:
        # Load configuration
        config = Config.from_file(config_path)

        # Setup logging
        setup_logging(
            level=config.logging.level,
            format_type=config.logging.format,
            log_file=config.logging.file,
        )

        # Create application
        app = ScannerApp(config)

        # Setup signal handlers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def signal_handler(sig: int, frame: object) -> None:
            logger.info(f"Received signal {sig}")
            app.request_shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run application
        loop.run_until_complete(app.run())

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
