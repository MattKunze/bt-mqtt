"""Advertisement deduplication."""

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class Deduplicator:
    """Time-based advertisement deduplication."""

    def __init__(self, interval_seconds: int = 30):
        """Initialize deduplicator.

        Args:
            interval_seconds: Minimum seconds between publishing same device
        """
        self.interval_seconds = interval_seconds
        self._last_seen: Dict[str, float] = {}

    def should_publish(self, device_address: str) -> bool:
        """Check if advertisement should be published.

        Args:
            device_address: MAC address of device

        Returns:
            True if should publish, False if duplicate
        """
        now = time.time()
        last_seen = self._last_seen.get(device_address)

        if last_seen is None:
            # First time seeing this device
            self._last_seen[device_address] = now
            return True

        elapsed = now - last_seen

        if elapsed >= self.interval_seconds:
            # Enough time has passed
            self._last_seen[device_address] = now
            return True

        # Too soon, deduplicate
        logger.debug(
            f"Deduplicating {device_address}: "
            f"last seen {elapsed:.1f}s ago (threshold: {self.interval_seconds}s)"
        )
        return False

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "unique_devices_seen": len(self._last_seen),
        }

    def clear_old_entries(self, max_age_seconds: int = 3600) -> int:
        """Remove entries older than max_age to prevent memory growth.

        Args:
            max_age_seconds: Remove entries not seen in this many seconds

        Returns:
            Number of entries removed
        """
        now = time.time()
        old_keys = [
            addr for addr, last_seen in self._last_seen.items() if now - last_seen > max_age_seconds
        ]

        for key in old_keys:
            del self._last_seen[key]

        if old_keys:
            logger.debug(f"Cleared {len(old_keys)} old deduplication entries")

        return len(old_keys)
