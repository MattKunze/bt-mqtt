"""Tests for deduplicator module."""

import time

from scanner.deduplicator import Deduplicator


def test_deduplicator_first_device():
    """Test that first advertisement is always published."""
    dedup = Deduplicator(interval_seconds=30)
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is True


def test_deduplicator_blocks_duplicate():
    """Test that duplicate within interval is blocked."""
    dedup = Deduplicator(interval_seconds=1)

    # First should pass
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is True

    # Immediate duplicate should be blocked
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is False


def test_deduplicator_allows_after_interval():
    """Test that device is published again after interval."""
    dedup = Deduplicator(interval_seconds=1)

    # First publish
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is True

    # Wait for interval
    time.sleep(1.1)

    # Should be allowed again
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is True


def test_deduplicator_multiple_devices():
    """Test that different devices are tracked independently."""
    dedup = Deduplicator(interval_seconds=10)

    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is True
    assert dedup.should_publish("11:22:33:44:55:66") is True

    # Duplicates should be blocked
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is False
    assert dedup.should_publish("11:22:33:44:55:66") is False


def test_deduplicator_stats():
    """Test statistics tracking."""
    dedup = Deduplicator(interval_seconds=30)

    dedup.should_publish("AA:BB:CC:DD:EE:FF")
    dedup.should_publish("11:22:33:44:55:66")
    dedup.should_publish("AA:BB:CC:DD:EE:FF")  # Duplicate

    stats = dedup.get_stats()
    assert stats["unique_devices_seen"] == 2


def test_deduplicator_cleanup():
    """Test old entry cleanup."""
    dedup = Deduplicator(interval_seconds=1)

    # Add some devices
    dedup.should_publish("AA:BB:CC:DD:EE:FF")
    dedup.should_publish("11:22:33:44:55:66")

    # Wait and cleanup with very short max_age
    time.sleep(1.1)
    removed = dedup.clear_old_entries(max_age_seconds=1)

    assert removed == 2

    # After cleanup, devices should be treated as new
    assert dedup.should_publish("AA:BB:CC:DD:EE:FF") is True
