# 0003. MQTT Topic Naming Structure

**Date:** 2026-01-11

**Status:** Accepted

## Context

The system uses MQTT as a message bus between scanner agents and the subscriber. We need a topic naming convention that:

- Clearly identifies the data type (raw BLE advertisements)
- Allows filtering by scanner when multiple scanners are deployed
- Supports future expansion (e.g., processed data, control messages)
- Follows MQTT best practices for hierarchical topic structures
- Enables efficient subscriber filtering using MQTT wildcards

The topic structure impacts system scalability, debugging, and future extensibility.

## Decision

We will use the topic structure: `bt-mqtt/raw/{scanner_id}`

Where:
- `bt-mqtt` is the root namespace for all topics in this system
- `raw` indicates unprocessed BLE advertisement data
- `{scanner_id}` is a unique identifier for each scanner agent

Example: `bt-mqtt/raw/pi-living-room`

## Consequences

### Positive

- **Clear data type**: The `raw` segment immediately identifies this as unprocessed advertisement data
- **Scanner identification**: Each scanner publishes to its own topic, enabling per-scanner monitoring and debugging
- **Wildcard subscription**: Subscriber can use `bt-mqtt/raw/+` to receive from all scanners
- **Namespace isolation**: The `bt-mqtt` prefix prevents collision with other MQTT applications
- **Future extensibility**: Easy to add new topic types:
  - `bt-mqtt/processed/{device_type}` for parsed data
  - `bt-mqtt/control/{scanner_id}` for scanner commands
  - `bt-mqtt/status/{scanner_id}` for health/metrics
- **Debugging friendly**: Topic structure makes it easy to use MQTT tools to inspect specific scanner output
- **Multi-tenant ready**: Could add tenant prefix if needed: `{tenant}/bt-mqtt/raw/{scanner_id}`

### Negative

- **Topic proliferation**: Each scanner gets its own topic, which could be many topics in large deployments
- **No device filtering**: Cannot subscribe to specific device types at the topic level (filtering happens in subscriber)

### Neutral

- **Scanner ID required**: Scanners must be configured with an ID (see ADR-0007)
- **Topic per scanner**: Not topic per device, which keeps topic count manageable

## Alternatives Considered

### Flat structure: `bt-mqtt/{scanner_id}`

- **Pros**: Simpler structure
- **Cons**: No room for data types, processed data, or control messages. Doesn't scale.

### Device-level topics: `bt-mqtt/raw/{device_type}/{mac_address}`

- **Pros**: More granular subscription control
- **Cons**: Topic explosion (one per device), scanner can't determine device type, violates single responsibility

### Single topic: `bt-mqtt/raw`

- **Pros**: Simplest possible structure
- **Cons**: No scanner identification, can't filter by scanner, harder debugging, no per-scanner QoS control

### Reverse DNS: `ai/btmqtt/raw/{scanner_id}`

- **Pros**: Industry standard for namespacing
- **Cons**: Overly formal for this use case, less readable, doesn't add value

### Action-based: `bt-mqtt/advertisements/{scanner_id}`

- **Pros**: More descriptive noun
- **Cons**: Verbose, `raw` is clearer about processing state
