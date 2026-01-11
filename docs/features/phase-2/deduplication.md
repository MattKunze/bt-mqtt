# Feature: Time-Based Deduplication

**Status:** Planned  
**Milestone:** Phase 2 - Core Features  
**Owner:** TBD  
**Related ADRs:** [ADR-0005: Deduplication Strategy](../../decisions/0005-deduplication-strategy.md)

---

## Overview

Time-Based Deduplication reduces message volume and storage requirements by preventing the same BLE device from being published multiple times within a configurable time window. This feature significantly reduces MQTT traffic and database writes while maintaining data accuracy.

### Motivation

BLE devices continuously broadcast advertisements, often multiple times per second. Without deduplication:
- MQTT broker receives 10-100 messages/sec per device
- Database grows unnecessarily large
- Downstream processing wastes resources
- No meaningful additional information gained

Time-based deduplication ensures each device is reported at a reasonable interval (e.g., once per minute) while still capturing device presence and signal strength changes.

### Goals

- Reduce MQTT message volume by 90%+
- Implement configurable deduplication window
- Track last-seen timestamp per device
- Maintain in-memory deduplication cache
- Support scanner restart without data loss
- Provide deduplication statistics

### Non-Goals

- Content-based deduplication (comparing payload)
- Cross-scanner deduplication (each scanner independent)
- Persistence of deduplication state across restarts
- Deduplication at subscriber level

---

## Requirements

### Functional Requirements

1. **FR-1**: Track last publish timestamp for each MAC address
2. **FR-2**: Publish device only if time since last publish exceeds window
3. **FR-3**: Support configurable deduplication window (default: 60 seconds)
4. **FR-4**: Update RSSI if significantly changed even within window (optional)
5. **FR-5**: Clear cache entries for devices not seen in 24 hours
6. **FR-6**: Log deduplication statistics (messages blocked/allowed)
7. **FR-7**: Support disabling deduplication via configuration
8. **FR-8**: Include deduplication metadata in published messages

### Non-Functional Requirements

1. **NFR-1**: **Performance**: Add <1ms latency per advertisement
2. **NFR-2**: **Memory**: Use <10MB for 1000 devices
3. **NFR-3**: **Accuracy**: No false positives (never block unique messages)
4. **NFR-4**: **Reliability**: Handle cache overflow gracefully
5. **NFR-5**: **Configurability**: Runtime configuration updates
6. **NFR-6**: **Observability**: Expose deduplication metrics

---

## Dependencies

### Prerequisites

- BLE Scanner (Phase 1)
- MQTT Publisher (Phase 1)

### Blocked By

- None (extends Phase 1 features)

### Blocks

- None (independent enhancement)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────┐
│         Scanner with Deduplication       │
│                                          │
│  [BLE Advertisement] ──────────┐         │
│                                 ▼         │
│  ┌────────────────────────────────────┐ │
│  │   Deduplication Filter             │ │
│  │                                    │ │
│  │  - Check last seen timestamp      │ │
│  │  - Calculate time delta           │ │
│  │  - Apply deduplication window     │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│         ┌───────┴────────┐               │
│         ▼                ▼               │
│    [Allow]          [Block]              │
│         │                │               │
│         ▼                ▼               │
│  [Update Cache]   [Increment Counter]   │
│         │                                │
│         ▼                                │
│  [MQTT Publisher]                        │
└─────────────────────────────────────────┘
```

### Key Components

#### 1. Deduplication Cache
- In-memory dictionary: `MAC address → last seen timestamp`
- LRU eviction for memory management
- Periodic cleanup of stale entries
- Thread-safe access

#### 2. Deduplication Filter
- Receives advertisement from scanner
- Checks cache for MAC address
- Calculates time since last publish
- Applies deduplication window
- Updates cache on publish decision
- Tracks statistics

#### 3. Cache Manager
- Manages cache size limits
- Evicts least recently used entries
- Cleans up entries older than 24 hours
- Provides cache statistics

### Data Structures

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class DeviceCache:
    """Cached device information for deduplication"""
    mac_address: str
    last_published: datetime
    last_rssi: int
    publish_count: int

class DeduplicationFilter:
    def __init__(self, window_seconds: int = 60, max_cache_size: int = 10000):
        self.window_seconds = window_seconds
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, DeviceCache] = {}
        self.blocked_count = 0
        self.allowed_count = 0
        
    def should_publish(
        self, 
        mac_address: str, 
        rssi: int, 
        now: datetime
    ) -> bool:
        """Determine if advertisement should be published"""
        cached = self.cache.get(mac_address)
        
        # First time seeing device - always publish
        if cached is None:
            self._add_to_cache(mac_address, rssi, now)
            self.allowed_count += 1
            return True
        
        # Calculate time since last publish
        time_delta = (now - cached.last_published).total_seconds()
        
        # Check if window has elapsed
        if time_delta >= self.window_seconds:
            self._update_cache(mac_address, rssi, now)
            self.allowed_count += 1
            return True
        
        # Within window - block
        self.blocked_count += 1
        return False
    
    def _add_to_cache(self, mac_address: str, rssi: int, now: datetime):
        # Check cache size limit
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        self.cache[mac_address] = DeviceCache(
            mac_address=mac_address,
            last_published=now,
            last_rssi=rssi,
            publish_count=1
        )
    
    def _update_cache(self, mac_address: str, rssi: int, now: datetime):
        cached = self.cache[mac_address]
        cached.last_published = now
        cached.last_rssi = rssi
        cached.publish_count += 1
    
    def _evict_oldest(self):
        """Evict least recently published entry"""
        if not self.cache:
            return
        
        oldest_mac = min(
            self.cache.keys(), 
            key=lambda k: self.cache[k].last_published
        )
        del self.cache[oldest_mac]
    
    def cleanup_stale_entries(self, max_age_seconds: int = 86400):
        """Remove entries not seen in 24 hours"""
        now = datetime.now()
        stale_macs = [
            mac for mac, cached in self.cache.items()
            if (now - cached.last_published).total_seconds() > max_age_seconds
        ]
        for mac in stale_macs:
            del self.cache[mac]
    
    def get_statistics(self) -> dict:
        """Return deduplication statistics"""
        total = self.allowed_count + self.blocked_count
        block_rate = self.blocked_count / total if total > 0 else 0
        
        return {
            "allowed": self.allowed_count,
            "blocked": self.blocked_count,
            "total": total,
            "block_rate": block_rate,
            "cache_size": len(self.cache),
            "cache_limit": self.max_cache_size
        }
```

### Configuration

```yaml
scanner:
  deduplication:
    enabled: true
    window_seconds: 60        # Don't republish same device within 60s
    max_cache_size: 10000     # Maximum devices to track
    cleanup_interval: 3600    # Clean stale entries every hour
    stats_interval: 60        # Log statistics every 60s
```

### Integration with Scanner

```python
# Scanner main loop
async def scan_loop():
    scanner = BLEScanner()
    dedup_filter = DeduplicationFilter(
        window_seconds=config.deduplication.window_seconds,
        max_cache_size=config.deduplication.max_cache_size
    )
    
    async for advertisement in scanner.scan():
        # Apply deduplication filter
        if dedup_filter.should_publish(
            advertisement.mac_address,
            advertisement.rssi,
            datetime.now()
        ):
            await mqtt_publisher.publish(advertisement)
        
        # Periodic statistics
        if should_log_stats():
            stats = dedup_filter.get_statistics()
            logger.info(f"Deduplication stats: {stats}")
    
    # Periodic cleanup
    if should_cleanup():
        dedup_filter.cleanup_stale_entries()
```

### Enhanced Message Format

```json
{
  "scanner_id": "scanner-01",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "rssi": -67,
  "timestamp": "2026-01-11T10:30:45.123Z",
  "deduplication": {
    "first_seen": "2026-01-11T10:29:30.000Z",
    "publish_count": 5
  },
  "manufacturer_data": {...},
  "service_uuids": [...],
  "local_name": "TempSensor_01"
}
```

---

## Testing Strategy

### Unit Tests

- [ ] Test first advertisement always published
- [ ] Test within-window advertisements blocked
- [ ] Test post-window advertisements published
- [ ] Test cache eviction with size limit
- [ ] Test stale entry cleanup
- [ ] Test statistics calculation
- [ ] Test disabled deduplication

### Integration Tests

- [ ] Test with simulated advertisement stream
- [ ] Verify message reduction rate
- [ ] Test cache persistence across function calls
- [ ] Test with 1000+ devices
- [ ] Verify MQTT traffic reduction

### Performance Tests

- [ ] Measure filter overhead (<1ms per check)
- [ ] Test with high advertisement rate (1000/sec)
- [ ] Measure memory usage (1000 devices)
- [ ] Test cache eviction performance

### Manual Tests

- [ ] Verify reduced MQTT traffic in broker
- [ ] Monitor cache size over time
- [ ] Verify device reappearance after window
- [ ] Test configuration changes

---

## Open Questions

1. **Q**: Should we support RSSI-based republishing (significant change)?
   - **A**: Not in Phase 2 - simple time-based only

2. **Q**: Should deduplication state persist across restarts?
   - **A**: No - in-memory only for simplicity

3. **Q**: Should we support per-device deduplication windows?
   - **A**: No - global window for all devices

4. **Q**: How to handle clock skew between scanner and devices?
   - **A**: Use scanner's clock only, ignore device timestamps

---

## Implementation Checklist

### Core Implementation
- [ ] Create DeduplicationFilter class
- [ ] Implement cache management
- [ ] Implement should_publish logic
- [ ] Add cache eviction (LRU)
- [ ] Add stale entry cleanup
- [ ] Implement statistics tracking

### Integration
- [ ] Integrate with BLE scanner loop
- [ ] Add configuration support
- [ ] Implement periodic cleanup task
- [ ] Add statistics logging
- [ ] Update message format with dedup metadata

### Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Perform load testing
- [ ] Verify memory usage

### Documentation
- [ ] Document configuration options
- [ ] Document behavior and trade-offs
- [ ] Add performance characteristics
- [ ] Create troubleshooting guide

---

## Acceptance Criteria

- [ ] Deduplication reduces message volume by 90%+
- [ ] Filter adds <1ms latency per advertisement
- [ ] Memory usage <10MB for 1000 devices
- [ ] Statistics logged periodically
- [ ] Configuration changes apply without restart
- [ ] Unit test coverage >80%
- [ ] No messages lost (false positives)
- [ ] Documentation complete

---

## Related Features

- [BLE Scanner](../phase-1/ble-scanner.md) - Enhanced with deduplication
- [MQTT Publisher](../phase-1/mqtt-publisher.md) - Receives filtered messages
- [Blocklist](blocklist.md) - Complementary filtering

---

## References

- [ADR-0005: Deduplication Strategy](../../decisions/0005-deduplication-strategy.md)
- [LRU Cache Implementation](https://docs.python.org/3/library/functools.html#functools.lru_cache)
