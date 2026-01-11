"""MQTT publisher for BLE advertisements."""

import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import paho.mqtt.client as mqtt

from .ble_scanner import Advertisement

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """MQTT publisher for BLE advertisements."""

    def __init__(
        self,
        broker: str,
        port: int,
        scanner_id: str,
        topic_prefix: str = "bt-mqtt",
        qos: int = 1,
        client_id: Optional[str] = None,
        keepalive: int = 60,
        username: Optional[str] = None,
        password: Optional[str] = None,
        on_connect_callback: Optional[Callable[[], None]] = None,
        on_disconnect_callback: Optional[Callable[[], None]] = None,
    ):
        """Initialize MQTT publisher.

        Args:
            broker: MQTT broker hostname
            port: MQTT broker port
            scanner_id: Unique scanner identifier
            topic_prefix: Topic prefix (default: "bt-mqtt")
            qos: MQTT QoS level (0, 1, or 2)
            client_id: MQTT client ID (auto-generated if None)
            keepalive: Connection keepalive seconds
            username: MQTT username (optional)
            password: MQTT password (optional)
            on_connect_callback: Called when connected
            on_disconnect_callback: Called when disconnected
        """
        self.broker = broker
        self.port = port
        self.scanner_id = scanner_id
        self.topic_prefix = topic_prefix
        self.qos = qos
        self.keepalive = keepalive
        self.on_connect_callback = on_connect_callback
        self.on_disconnect_callback = on_disconnect_callback

        # Generate client ID if not provided
        if client_id is None:
            client_id = f"scanner-{scanner_id}-{int(time.time())}"

        # Create MQTT client
        self._client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        # Set credentials if provided
        if username and password:
            self._client.username_pw_set(username, password)

        # Set callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish

        # Track connection state
        self._connected = False
        self._connect_time: Optional[float] = None

        # Statistics
        self._messages_sent = 0
        self._messages_failed = 0

    def connect(self) -> None:
        """Connect to MQTT broker."""
        try:
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}")
            self._client.connect(self.broker, self.port, self.keepalive)
            self._client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        logger.info("Disconnecting from MQTT broker")
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def publish_advertisement(self, advertisement: Advertisement) -> bool:
        """Publish BLE advertisement to MQTT.

        Args:
            advertisement: Advertisement to publish

        Returns:
            True if publish initiated successfully, False otherwise
        """
        if not self._connected:
            logger.warning("Cannot publish: not connected to MQTT broker")
            self._messages_failed += 1
            return False

        try:
            # Create topic: bt-mqtt/raw/{scanner_id}
            topic = f"{self.topic_prefix}/raw/{self.scanner_id}"

            # Convert advertisement to JSON
            payload = json.dumps(advertisement.to_dict())

            # Publish message
            result = self._client.publish(topic, payload, qos=self.qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published advertisement to {topic}")
                return True
            else:
                logger.error(f"Failed to publish: {mqtt.error_string(result.rc)}")
                self._messages_failed += 1
                return False

        except Exception as e:
            logger.error(f"Error publishing advertisement: {e}")
            self._messages_failed += 1
            return False

    def publish_status(self, status_data: Dict[str, Any]) -> bool:
        """Publish scanner status/heartbeat.

        Args:
            status_data: Status data to publish

        Returns:
            True if publish initiated successfully, False otherwise
        """
        if not self._connected:
            logger.warning("Cannot publish status: not connected to MQTT broker")
            return False

        try:
            # Create topic: bt-mqtt/scanner/{scanner_id}/status
            topic = f"{self.topic_prefix}/scanner/{self.scanner_id}/status"

            # Add standard fields
            status = {
                "version": "1.0",
                "scanner_id": self.scanner_id,
                **status_data,
            }

            payload = json.dumps(status)

            # Publish with retain flag so last status is always available
            result = self._client.publish(topic, payload, qos=self.qos, retain=True)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published status to {topic}")
                return True
            else:
                logger.error(f"Failed to publish status: {mqtt.error_string(result.rc)}")
                return False

        except Exception as e:
            logger.error(f"Error publishing status: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get publisher statistics.

        Returns:
            Dictionary with statistics
        """
        uptime = 0.0
        if self._connect_time:
            uptime = time.time() - self._connect_time

        return {
            "connected": self._connected,
            "uptime_seconds": int(uptime),
            "messages_sent": self._messages_sent,
            "messages_failed": self._messages_failed,
        }

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Dict[str, Any],
        rc: int,
    ) -> None:
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self._connected = True
            self._connect_time = time.time()
            if self.on_connect_callback:
                self.on_connect_callback()
        else:
            logger.error(f"Failed to connect to MQTT broker: {mqtt.connack_string(rc)}")
            self._connected = False

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """Callback for MQTT disconnection."""
        if rc == 0:
            logger.info("Disconnected from MQTT broker (clean)")
        else:
            logger.warning(f"Disconnected from MQTT broker: {mqtt.error_string(rc)}")

        self._connected = False

        if self.on_disconnect_callback:
            self.on_disconnect_callback()

    def _on_publish(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
    ) -> None:
        """Callback for successful publish."""
        self._messages_sent += 1
