# 0005. Time-Based Deduplication at Scanner Level

**Date:** 2026-01-11

**Status:** Accepted

## Context

BLE devices advertise frequently (often multiple times per second). For many use cases, we don't need every single advertisement - we need periodic samples to track device state changes. Without deduplication:

- MQTT broker receives excessive message volume
- Network bandwidth is wasted on redundant data
- Subscriber processes duplicate advertisements
- Database grows with redundant records
- Costs increase for MQTT and storage

We need a deduplication strategy that balances data freshness with system efficiency.

## Decision

Implement **time-based deduplication at the scanner level** with a configurable interval (default 60 seconds).

The scanner will:
- Maintain an in-memory map of `{mac_address: last_published_timestamp}`
- Only publish an advertisement if no advertisement from that MAC has been published in the last N seconds
- Clean up stale entries periodically (e.g., devices not seen in 1 hour)

Configuration:
```python
DEDUP_INTERVAL_SECONDS = 60  # Configurable via environment variable
```

## Consequences

### Positive

- **Reduced MQTT traffic**: 95%+ reduction in message volume for typical BLE devices advertising every 1-5 seconds
- **Lower bandwidth costs**: Especially important for cellular or metered connections
- **Reduced processing load**: Subscriber processes fewer messages
- **Smaller database**: Fewer redundant records to store
- **Configurable granularity**: Can tune interval based on use case (fast-changing sensors vs. presence detection)
- **Early filtering**: Deduplication happens at the edge before data enters the system
- **Simple implementation**: In-memory map with timestamp comparison is straightforward

### Negative

- **Missed rapid changes**: Won't capture device state changes that occur within the deduplication window
- **Scanner memory usage**: Must maintain map of seen devices (minimal impact: ~100 bytes per device)
- **No cross-scanner deduplication**: Multiple scanners may publish the same device (acceptable tradeoff)
- **RSSI fluctuations ignored**: Won't capture RSSI changes within deduplication window (acceptable for most use cases)

### Neutral

- **Per-scanner configuration**: Each scanner can have different intervals if needed
- **Not content-aware**: Doesn't detect if advertisement data actually changed (could enhance later)

## Alternatives Considered

### No deduplication

- **Pros**: Captures all data, simplest implementation
- **Cons**: Excessive message volume, wasted resources, doesn't scale, high costs

### Deduplication in subscriber

- **Pros**: Centralized logic, could be cross-scanner
- **Cons**: Wastes MQTT bandwidth, subscriber must handle high message volume, defeats purpose of edge filtering

### Content-based deduplication (only publish if data changed)

- **Pros**: Only publishes meaningful changes
- **Cons**: More complex implementation, must parse manufacturer data in scanner (violates ADR-0004), difficult to implement generically for unknown devices, still need time-based backup for devices that always send same data

### Database-level deduplication

- **Pros**: Handles cross-scanner duplicates
- **Cons**: All data still flows through MQTT and subscriber, wasted processing, doesn't reduce upstream costs

### Adaptive deduplication (adjust interval based on device behavior)

- **Pros**: Optimal for each device type
- **Cons**: Complex to implement, requires device classification in scanner (violates ADR-0004), premature optimization

### Fixed message rate limiting (max N messages/minute per device)

- **Pros**: Predictable rate
- **Cons**: More complex than time window, could miss bursty important changes, harder to reason about

## Future Enhancements

Could add content-aware deduplication later:
- Compare manufacturer data payload
- Only publish if data changed OR time threshold exceeded
- Requires lightweight parser in scanner (tradeoff against ADR-0004)
