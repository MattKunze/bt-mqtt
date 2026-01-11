"""BLE advertisement scanner using bleak."""

import asyncio
import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

logger = logging.getLogger(__name__)


@dataclass
class Advertisement:
    """Parsed BLE advertisement data."""

    version: str
    timestamp: str
    scanner_id: str
    device_address: str
    device_address_type: str
    device_name: Optional[str]
    rssi: int
    manufacturer_data: Dict[str, str]
    service_data: Dict[str, str]
    service_uuids: list[str]
    raw_data: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "version": self.version,
            "timestamp": self.timestamp,
            "scanner_id": self.scanner_id,
            "device": {
                "address": self.device_address,
                "address_type": self.device_address_type,
                "rssi": self.rssi,
            },
        }

        if self.device_name:
            result["device"]["name"] = self.device_name

        if self.manufacturer_data:
            result["manufacturer_data"] = self.manufacturer_data

        if self.service_data:
            result["service_data"] = self.service_data

        if self.service_uuids:
            result["service_uuids"] = self.service_uuids

        result["raw_data"] = self.raw_data

        return result


class BLEScanner:
    """BLE advertisement scanner."""

    def __init__(
        self,
        scanner_id: str,
        adapter: str = "hci0",
        callback: Optional[Callable[[Advertisement], None]] = None,
    ):
        """Initialize BLE scanner.

        Args:
            scanner_id: Unique identifier for this scanner
            adapter: Bluetooth adapter name (e.g., "hci0")
            callback: Function to call when advertisement is received
        """
        self.scanner_id = scanner_id
        self.adapter = adapter
        self.callback = callback
        self._scanner: Optional[BleakScanner] = None
        self._running = False
        self._scan_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Start BLE scanning."""
        if self._running:
            logger.warning("Scanner already running")
            return

        logger.info(f"Starting BLE scanner on adapter {self.adapter}")

        try:
            self._scanner = BleakScanner(
                detection_callback=self._handle_advertisement,
                adapter=self.adapter,
            )

            self._running = True
            self._scan_task = asyncio.create_task(self._scan_loop())
            logger.info("BLE scanner started successfully")

        except Exception as e:
            logger.error(f"Failed to start BLE scanner: {e}")
            raise

    async def stop(self) -> None:
        """Stop BLE scanning."""
        if not self._running:
            return

        logger.info("Stopping BLE scanner")
        self._running = False

        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass

        if self._scanner:
            try:
                await self._scanner.stop()
            except Exception as e:
                logger.warning(f"Error stopping scanner: {e}")

        logger.info("BLE scanner stopped")

    async def _scan_loop(self) -> None:
        """Main scanning loop with retry logic."""
        retry_count = 0
        max_retries = 10

        while self._running:
            try:
                if self._scanner:
                    logger.debug(f"Starting BLE scan (attempt {retry_count + 1})")
                    await self._scanner.start()
                    retry_count = 0  # Reset on successful start

                    # Keep scanning until stopped
                    # Use a stop event instead of polling every second
                    stop_event = asyncio.Event()

                    def check_running():
                        if not self._running:
                            stop_event.set()

                    # Check every 5 seconds instead of every 1 second
                    while self._running:
                        try:
                            await asyncio.wait_for(stop_event.wait(), timeout=5.0)
                            break
                        except asyncio.TimeoutError:
                            continue

                    await self._scanner.stop()

            except asyncio.CancelledError:
                break
            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                # Provide helpful error messages
                if "Resource Not Ready" in error_msg:
                    logger.error(
                        f"Bluetooth adapter not ready (attempt {retry_count}/{max_retries}). "
                        f"Try: sudo hciconfig {self.adapter} down && sudo hciconfig {self.adapter} up"
                    )
                elif "Permission denied" in error_msg:
                    logger.error(
                        f"Permission denied accessing Bluetooth adapter. "
                        f"Try: sudo usermod -a -G bluetooth $USER (then logout/login)"
                    )
                else:
                    logger.error(f"Scanner error: {e}")

                if retry_count >= max_retries:
                    logger.critical(
                        f"Failed to start scanner after {max_retries} attempts. Giving up."
                    )
                    self._running = False
                    break

                if self._running:
                    # Exponential backoff: 5, 10, 15, 20, 30, 30, ...
                    wait_time = min(5 * retry_count, 30)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

    def _handle_advertisement(
        self, device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Handle received BLE advertisement.

        Args:
            device: BLE device information
            advertisement_data: Advertisement data
        """
        try:
            # Create timestamp
            timestamp = datetime.now(timezone.utc).isoformat()

            # Format manufacturer data
            manufacturer_data = {}
            if advertisement_data.manufacturer_data:
                for company_id, data in advertisement_data.manufacturer_data.items():
                    # Format company ID as hex string with 0x prefix
                    key = f"0x{company_id:04x}"
                    # Encode binary data as base64
                    manufacturer_data[key] = base64.b64encode(bytes(data)).decode()

            # Format service data
            service_data = {}
            if advertisement_data.service_data:
                for uuid, data in advertisement_data.service_data.items():
                    # Encode binary data as base64
                    service_data[uuid] = base64.b64encode(bytes(data)).decode()

            # Get service UUIDs
            service_uuids = (
                list(advertisement_data.service_uuids) if advertisement_data.service_uuids else []
            )

            # Encode raw advertisement data
            # Note: bleak doesn't provide raw bytes, so we'll encode what we have
            raw_data = base64.b64encode(b"").decode()  # Placeholder

            # Create advertisement object
            advertisement = Advertisement(
                version="1.0",
                timestamp=timestamp,
                scanner_id=self.scanner_id,
                device_address=device.address.upper(),
                device_address_type="public",  # bleak doesn't expose this easily
                device_name=advertisement_data.local_name,
                rssi=advertisement_data.rssi,
                manufacturer_data=manufacturer_data,
                service_data=service_data,
                service_uuids=service_uuids,
                raw_data=raw_data,
            )

            logger.debug(
                f"Advertisement from {device.address}: "
                f"RSSI={advertisement_data.rssi}, "
                f"Name={advertisement_data.local_name}"
            )

            # Call callback if provided
            if self.callback:
                self.callback(advertisement)

        except Exception as e:
            logger.error(f"Error processing advertisement from {device.address}: {e}")
