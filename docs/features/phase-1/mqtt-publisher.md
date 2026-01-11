# Feature: MQTT Publisher

**Status:** In Progress  
**Milestone:** Phase 1 - Foundation  
**Owner:** TBD  
**Related ADRs:** [ADR-0003: MQTT Topic Structure](../../decisions/0003-mqtt-topic-structure.md), [ADR-0009: MQTT Failure Drop Messages](../../decisions/0009-mqtt-failure-drop-messages.md)

---

## Overview

The MQTT Publisher is responsible for taking BLE advertisement data from the scanner and publishing it to the MQTT broker. It acts as the bridge between the BLE scanning component and the rest of the distributed system.

### Motivation

MQTT provides a lightweight, reliable publish-subscribe messaging pattern that decouples the scanner from data processing components. This allows multiple subscribers to consume scanner data independently and enables horizontal scaling of the system.

### Goals

- Publish BLE advertisement data to MQTT broker
- Implement reliable connection management
- Support configurable topic routing
- Provide message delivery confirmation
- Handle connection failures gracefully
- Maintain high message throughput

### Non-Goals

- Message transformation or parsing (handled by subscriber)
- Message persistence (broker responsibility)
- Authentication/authorization (handled by broker)
- Message ordering guarantees (best-effort delivery)

---

## Requirements

### Functional Requirements

1. **FR-1**: Connect to MQTT broker on startup
2. **FR-2**: Publish each BLE advertisement as separate MQTT message
3. **FR-3**: Use topic structure: `ble/raw/{scanner_id}/{mac_address}`
4. **FR-4**: Include scanner identifier in message metadata
5. **FR-5**: Serialize message payload as JSON
6. **FR-6**: Implement automatic reconnection on connection loss
7. **FR-7**: Drop messages if broker is unavailable (no local buffering)
8. **FR-8**: Log successful publishes at debug level
9. **FR-9**: Log failed publishes at error level
10. **FR-10**: Provide graceful shutdown with connection cleanup

### Non-Functional Requirements

1. **NFR-1**: **Reliability**: Reconnect automatically within 10 seconds
2. **NFR-2**: **Performance**: Publish 100+ messages per second
3. **NFR-3**: **Latency**: Publish messages within 100ms of scanner detection
4. **NFR-4**: **Resource Usage**: Use <10MB RAM
5. **NFR-5**: **QoS**: Support MQTT QoS 0 (at most once) and QoS 1 (at least once)
6. **NFR-6**: **Compatibility**: Work with MQTT 3.1.1 brokers
7. **NFR-7**: **Backpressure**: Handle broker slowdown without blocking scanner

---

## Dependencies

### Prerequisites

- MQTT broker (Mosquitto, HiveMQ, etc.)
- Python MQTT client library (`paho-mqtt`)
- BLE Scanner component running

### Blocked By

- BLE Scanner (provides data to publish)
- MQTT broker availability

### Blocks

- MQTT Subscriber (needs published messages)
- All downstream processing

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────┐
│         MQTT Publisher                   │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   Connection Manager               │ │
│  │                                    │ │
│  │  - Establish connection            │ │
│  │  - Handle reconnection             │ │
│  │  - Monitor connection health       │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │   Message Publisher                │ │
│  │                                    │ │
│  │  - Format message payload          │ │
│  │  - Determine topic                 │ │
│  │  - Publish with QoS                │ │
│  │  - Handle publish callbacks        │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│        [MQTT Broker]                     │
└─────────────────────────────────────────┘
```

### Key Components

#### 1. Connection Manager
- Establishes MQTT connection with credentials
- Configures client ID, keep-alive, clean session
- Implements reconnection with exponential backoff
- Monitors connection state
- Handles connection callbacks (on_connect, on_disconnect)

#### 2. Message Publisher
- Receives advertisement data from scanner queue
- Formats JSON payload
- Determines topic based on MAC address and scanner ID
- Publishes with configured QoS level
- Tracks publish success/failure

#### 3. Message Formatter
- Serializes advertisement data to JSON
- Adds publisher metadata (timestamp, scanner_id)
- Validates message structure
- Handles encoding edge cases

### Data Flow

1. Advertisement received from scanner queue
2. Message formatter creates JSON payload
3. Topic determined from MAC address and scanner ID
4. Message published to broker with QoS level
5. Publish callback confirms delivery (QoS 1) or fire-and-forget (QoS 0)
6. Success/failure logged
7. Process repeats for next advertisement

### Message Format

```json
{
  "scanner_id": "scanner-01",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "rssi": -67,
  "timestamp": "2026-01-11T10:30:45.123Z",
  "manufacturer_data": {
    "4c00": "02150123..."
  },
  "service_uuids": ["0000180f-0000-1000-8000-00805f9b34fb"],
  "local_name": "TempSensor_01"
}
```

### Topic Structure

- **Base Topic**: `ble/raw/`
- **Full Topic**: `ble/raw/{scanner_id}/{mac_address}`
- **Example**: `ble/raw/scanner-01/AA:BB:CC:DD:EE:FF`

Rationale (from ADR-0003):
- Enables filtering by scanner
- Enables filtering by device
- Supports wildcards (`ble/raw/#` for all messages)

### Connection Configuration

```yaml
mqtt:
  broker:
    host: "localhost"
    port: 1883
    username: null        # Optional
    password: null        # Optional
  client:
    client_id: "bt-mqtt-scanner-01"
    keep_alive: 60        # Seconds
    clean_session: true
    qos: 0                # 0 = at most once, 1 = at least once
  reconnect:
    initial_delay: 1      # Seconds
    max_delay: 60         # Seconds
    exponential_backoff: true
```

### Error Handling

- **Connection Failed**: Retry with exponential backoff (1s, 2s, 4s, ..., 60s)
- **Publish Failed**: Log error and **drop message** (per ADR-0009)
- **Network Timeout**: Trigger reconnection
- **Broker Unavailable**: Continue retrying indefinitely
- **Invalid Data**: Log error and skip message

---

## Testing Strategy

### Unit Tests

- [ ] Test message formatter with various advertisement formats
- [ ] Test topic generation for different MAC addresses
- [ ] Test connection configuration parsing
- [ ] Test exponential backoff calculation
- [ ] Test message serialization edge cases

### Integration Tests

- [ ] Test connection to local MQTT broker
- [ ] Test message publishing end-to-end
- [ ] Test reconnection after broker restart
- [ ] Test QoS 0 and QoS 1 message delivery
- [ ] Test graceful shutdown and cleanup
- [ ] Test handling of broker unavailability

### Performance Tests

- [ ] Measure publish throughput (messages/sec)
- [ ] Measure publish latency (scanner to broker)
- [ ] Test with 100+ messages/sec load
- [ ] Measure memory usage over 1-hour run
- [ ] Test backpressure handling when broker is slow

### Manual Tests

- [ ] Verify message format in MQTT broker
- [ ] Test with multiple subscribers
- [ ] Verify topic wildcards work correctly
- [ ] Test authentication with username/password
- [ ] Test TLS connection (if implemented)

---

## Open Questions

1. **Q**: Should we implement local message buffering for brief disconnections?
   - **A**: No - ADR-0009 decided to drop messages to prevent memory issues

2. **Q**: What QoS level should be default?
   - **A**: QoS 0 for performance, configurable to QoS 1 if needed

3. **Q**: Should we support MQTT 5.0 features?
   - **A**: Not in Phase 1 - start with MQTT 3.1.1, upgrade if needed

4. **Q**: How to handle scanner_id configuration?
   - **A**: Manual configuration per ADR-0007

5. **Q**: Should we include publish statistics in logs?
   - **A**: Yes - log message rate every 60 seconds at info level

---

## Implementation Checklist

### Setup
- [ ] Install paho-mqtt library
- [ ] Create publisher module structure
- [ ] Set up logging configuration
- [ ] Create configuration schema

### Connection Management
- [ ] Implement MQTT client initialization
- [ ] Implement connection with credentials
- [ ] Add connection callbacks (on_connect, on_disconnect)
- [ ] Implement exponential backoff reconnection
- [ ] Add connection state monitoring

### Message Publishing
- [ ] Implement message formatter (JSON serialization)
- [ ] Implement topic generation
- [ ] Implement publish function with QoS support
- [ ] Add publish callbacks (on_publish)
- [ ] Implement message rate statistics

### Integration
- [ ] Connect scanner queue to publisher
- [ ] Implement message consumption loop
- [ ] Add graceful shutdown handling
- [ ] Implement signal handlers

### Error Handling
- [ ] Add connection error handling
- [ ] Add publish error handling
- [ ] Add timeout handling
- [ ] Add malformed data handling

### Testing
- [ ] Write unit tests for formatter
- [ ] Write integration tests with broker
- [ ] Perform performance testing
- [ ] Test reconnection scenarios

### Documentation
- [ ] Document broker requirements
- [ ] Document topic structure
- [ ] Document configuration options
- [ ] Add troubleshooting guide

---

## Acceptance Criteria

- [ ] Publisher connects to MQTT broker successfully
- [ ] Messages published with correct topic structure
- [ ] Message payload is valid JSON matching schema
- [ ] Publisher reconnects automatically after broker restart
- [ ] Publisher handles 100+ messages/sec
- [ ] Publish latency <100ms under normal load
- [ ] Messages dropped gracefully when broker unavailable
- [ ] Unit test coverage >80%
- [ ] Integration tests pass with Mosquitto broker
- [ ] Documentation complete and reviewed

---

## Related Features

- [BLE Scanner](ble-scanner.md) - Provides data to publish
- [MQTT Subscriber](mqtt-subscriber.md) - Consumes published messages
- [Scanner Heartbeat](../phase-2/scanner-heartbeat.md) - Health monitoring

---

## References

- [paho-mqtt documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
- [MQTT 3.1.1 Specification](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
- [ADR-0003: MQTT Topic Structure](../../decisions/0003-mqtt-topic-structure.md)
- [ADR-0009: MQTT Failure Drop Messages](../../decisions/0009-mqtt-failure-drop-messages.md)
- [MQTT Schema Documentation](../../mqtt-schema.md)
