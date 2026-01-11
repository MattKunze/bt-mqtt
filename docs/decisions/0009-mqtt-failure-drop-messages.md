# 0009. Drop Messages on MQTT Connection Failure

**Date:** 2026-01-11

**Status:** Accepted

## Context

The scanner agent continuously generates BLE advertisement data and publishes to MQTT. Network issues or MQTT broker outages can cause connection failures. We need to decide how to handle messages when MQTT is unavailable:

- Buffer messages locally and retry later
- Drop messages and continue scanning
- Stop scanning until connection restored
- Implement persistent queue

Considerations:
- Scanner runs on resource-constrained devices (Raspberry Pi)
- BLE advertisements are time-series data with high frequency
- Stale data (from hours/days ago) has limited value
- Scanner should be resilient and self-healing

## Decision

**Drop messages on MQTT connection failure.** Do not buffer or persist messages locally.

Behavior:
- Scanner continues scanning even when MQTT is disconnected
- Advertisement messages are dropped if MQTT client cannot send
- Scanner logs connection failures and dropped message counts
- Scanner automatically reconnects when MQTT becomes available
- Once reconnected, resume publishing new advertisements

Implementation:
```python
try:
    client.publish(topic, payload)
except Exception as e:
    logger.warning(f"Failed to publish, dropping message: {e}")
    # Continue scanning, don't buffer
```

## Consequences

### Positive

- **Resource efficiency**: No memory used for buffering on constrained devices
- **Simple implementation**: No queue management, persistence, or replay logic
- **No unbounded growth**: Can't run out of memory from buffer growth during long outages
- **Fast recovery**: Immediately resume normal operation when connection restored
- **Fresh data**: Only publish current/recent data, not stale backlog
- **Predictable behavior**: Easy to reason about system state
- **Self-healing**: Scanner doesn't need intervention after network issues

### Negative

- **Data loss**: Advertisements during outages are lost
- **Coverage gaps**: Missing data during MQTT downtime
- **No historical backfill**: Can't recover lost data after outage resolved

### Neutral

- **Time-series appropriate**: For monitoring/trending, gaps are acceptable (interpolation possible)
- **Depends on use case**: Appropriate for ambient monitoring, not for critical alarms

## Alternatives Considered

### Buffer messages in memory with size limit

- **Pros**: Preserves some data during brief outages, can replay on reconnect
- **Cons**: Memory usage grows during outage, buffer size limits are arbitrary, what to do when buffer fills? Still lose data in long outages, adds complexity

### Persist messages to local disk

- **Pros**: Survives long outages and scanner restarts
- **Cons**: Significant complexity (disk I/O, rotation, cleanup), wear on SD cards (Raspberry Pi), stale data on reconnect, database-like concerns on edge device, overkill for telemetry data

### Stop scanning during outage

- **Pros**: Simplest - don't generate data we can't send
- **Cons**: Couples scanning to MQTT availability, loses real-time monitoring capability, scanner appears "down" when MQTT is down

### Implement persistent queue (SQLite, etc.)

- **Pros**: Reliable message delivery, survives restarts
- **Cons**: Significant complexity, disk I/O overhead, database management, SD card wear, replay ordering concerns, overkill for telemetry

### Forward to backup MQTT broker

- **Pros**: High availability through redundancy
- **Cons**: Requires multiple MQTT brokers (added infrastructure), doesn't solve client-side network issues, configuration complexity

### Use MQTT QoS 1 with client buffering

- **Pros**: MQTT client handles retry logic
- **Cons**: Client buffer still consumes memory, doesn't solve long outage problem, acknowledgment overhead

## Use Case Analysis

This decision is appropriate for:
- Ambient environmental monitoring (temperature, humidity)
- Presence detection
- Trend analysis and dashboards
- Non-critical alerting

This decision is NOT appropriate for:
- Critical alarms that must never be missed
- Event counting where every event matters
- Compliance/audit logging
- Billing/metering data

For critical use cases, consider:
- Multiple redundant scanners
- Edge buffering with separate reliable queue service
- Different architecture (scanner writes to local DB, separate sync process)

## Monitoring and Observability

To mitigate data loss concerns:
- Log connection state changes (connected/disconnected)
- Log count of dropped messages during outages
- Expose metrics for monitoring:
  - Connection uptime percentage
  - Messages dropped counter
  - Time since last successful publish
- Alert on prolonged MQTT disconnection

This allows operators to:
- Detect MQTT issues quickly
- Understand data quality and gaps
- Correlate missing data with outage windows

## Future Enhancements

If use cases emerge that require guaranteed delivery:
1. Add optional buffering as configuration flag
2. Implement simple circular buffer with fixed size
3. Add metrics for buffer usage
4. Document when to enable buffering

Keep as opt-in to maintain default simplicity.
