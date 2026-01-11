# MQTT Schema

**Last Updated:** 2026-01-11

## Overview

This document defines the MQTT topic structure, message formats, and conventions for the BT-MQTT system.

## Topic Structure

### Topic Hierarchy

```
bt-mqtt/
├── raw/{scanner_id}              # Raw BLE advertisements
├── scanner/{scanner_id}/status   # Scanner heartbeat/health
└── command/{scanner_id}          # Optional: Commands to scanner
```

### Topic Details

#### `bt-mqtt/raw/{scanner_id}`

**Purpose:** Raw BLE advertisement data from a scanner agent

**Publisher:** Scanner agent
**Subscriber:** Subscriber service
**QoS:** 1 (at least once delivery)
**Retained:** No

**Example Topics:**
- `bt-mqtt/raw/pi-zero-living-room`
- `bt-mqtt/raw/pi-zero-bedroom`
- `bt-mqtt/raw/pi-zero-basement`

**Subscription Pattern:**
- Subscriber uses wildcard: `bt-mqtt/raw/#` to receive all scanner messages

#### `bt-mqtt/scanner/{scanner_id}/status`

**Purpose:** Scanner health, metrics, and heartbeat

**Publisher:** Scanner agent
**Subscriber:** Subscriber service (optional monitoring)
**QoS:** 1
**Retained:** Yes (last status always available)
**Frequency:** Every 60 seconds

**Example Topics:**
- `bt-mqtt/scanner/pi-zero-living-room/status`

#### `bt-mqtt/command/{scanner_id}`

**Purpose:** Send commands to scanner (future feature)

**Publisher:** Management UI or API
**Subscriber:** Scanner agent
**QoS:** 1
**Retained:** No

**Potential Commands:**
- Pause/resume scanning
- Update blocklist
- Update deduplication interval
- Trigger restart

## Message Formats

### Raw Advertisement Message

Published to: `bt-mqtt/raw/{scanner_id}`

```json
{
  "version": "1.0",
  "timestamp": "2026-01-11T12:34:56.789Z",
  "scanner_id": "pi-zero-living-room",
  "device": {
    "address": "AA:BB:CC:DD:EE:FF",
    "address_type": "public",
    "name": "Sensor-01",
    "rssi": -65
  },
  "manufacturer_data": {
    "0x004c": "AgEGGwP/TAANAX4M8g=="
  },
  "service_data": {
    "0000181a-0000-1000-8000-00805f9b34fb": "VGVtcDoyMi41QyBI"
  },
  "service_uuids": [
    "0000181a-0000-1000-8000-00805f9b34fb"
  ],
  "raw_data": "AgEGGwP/TAANAX4M8g=="
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Message schema version (semver) |
| `timestamp` | string (ISO 8601) | Yes | UTC timestamp when advertisement was received |
| `scanner_id` | string | Yes | Unique scanner identifier |
| `device.address` | string | Yes | Bluetooth MAC address (uppercase, colon-separated) |
| `device.address_type` | string | Yes | `"public"` or `"random"` |
| `device.name` | string | No | Device name from advertisement (if present) |
| `device.rssi` | integer | Yes | Received Signal Strength Indicator (dBm) |
| `manufacturer_data` | object | No | Map of company ID (hex string) to base64-encoded data |
| `service_data` | object | No | Map of service UUID to base64-encoded data |
| `service_uuids` | array[string] | No | List of advertised service UUIDs |
| `raw_data` | string | Yes | Complete advertisement payload (base64-encoded) |

#### Notes

- **Timestamp Format**: ISO 8601 with milliseconds, UTC timezone
- **MAC Address Format**: Uppercase hex with colon separators (e.g., `AA:BB:CC:DD:EE:FF`)
- **Company IDs**: Lowercase hex string with `0x` prefix (e.g., `0x004c` for Apple)
- **Service UUIDs**: Lowercase, full 128-bit UUID format
- **Base64 Encoding**: Standard base64 encoding for all binary data

### Scanner Status Message

Published to: `bt-mqtt/scanner/{scanner_id}/status`

```json
{
  "version": "1.0",
  "timestamp": "2026-01-11T12:34:56.789Z",
  "scanner_id": "pi-zero-living-room",
  "status": "online",
  "uptime_seconds": 3600,
  "metrics": {
    "messages_sent": 1234,
    "messages_dropped": 5,
    "devices_seen": 15,
    "devices_blocked": 2
  },
  "bluetooth": {
    "adapter": "hci0",
    "status": "scanning",
    "errors": 0
  },
  "mqtt": {
    "connected": true,
    "reconnections": 1
  },
  "config": {
    "deduplication_interval": 30,
    "blocklist_count": 3
  }
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Message schema version |
| `timestamp` | string (ISO 8601) | Yes | Status message timestamp |
| `scanner_id` | string | Yes | Unique scanner identifier |
| `status` | string | Yes | `"online"`, `"degraded"`, or `"offline"` |
| `uptime_seconds` | integer | Yes | Seconds since scanner started |
| `metrics.messages_sent` | integer | Yes | Total messages published to MQTT |
| `metrics.messages_dropped` | integer | Yes | Messages dropped (deduplication or errors) |
| `metrics.devices_seen` | integer | Yes | Unique devices seen this session |
| `metrics.devices_blocked` | integer | Yes | Messages blocked by blocklist |
| `bluetooth.adapter` | string | Yes | Bluetooth adapter name (e.g., `"hci0"`) |
| `bluetooth.status` | string | Yes | `"scanning"`, `"stopped"`, or `"error"` |
| `bluetooth.errors` | integer | Yes | BLE error count |
| `mqtt.connected` | boolean | Yes | Current MQTT connection status |
| `mqtt.reconnections` | integer | Yes | Number of MQTT reconnections |
| `config.*` | various | No | Current configuration snapshot |

### Command Message (Future)

Published to: `bt-mqtt/command/{scanner_id}`

```json
{
  "version": "1.0",
  "command": "pause",
  "timestamp": "2026-01-11T12:34:56.789Z",
  "parameters": {}
}
```

**Potential Commands:**
- `pause` - Stop scanning
- `resume` - Resume scanning
- `reload_config` - Reload configuration file
- `update_blocklist` - Update device blocklist

## Message Size Limits

- **Raw Advertisement**: Typically 200-500 bytes
- **Status Message**: ~400-600 bytes
- **Maximum MQTT Payload**: 256 MB (MQTT spec), but keep < 10 KB for practical limits

## QoS Strategy

### QoS 1 (At Least Once)

Used for all messages:
- **Rationale**: Balance between reliability and performance
- **Guarantees**: Messages delivered at least once (may duplicate)
- **Network**: Survives temporary network issues

### Why Not QoS 0?

- Too unreliable for data pipeline
- May lose messages silently

### Why Not QoS 2?

- Overkill for continuous data stream
- Performance overhead not justified
- Duplicates handled by deduplication at database level

**Related:** [ADR-0003: MQTT Topic Structure](decisions/0003-mqtt-topic-structure.md)

## Retained Messages

- **Raw Advertisements**: NOT retained (high volume, transient data)
- **Status Messages**: RETAINED (last known state always available)
- **Command Messages**: NOT retained (one-time actions)

## Message Ordering

MQTT guarantees message ordering per topic, per publisher. In our system:
- Messages from same scanner arrive in order
- Messages from different scanners may interleave
- Subscriber must handle out-of-order messages across scanners

## Error Scenarios

### Invalid Message Format

If subscriber receives malformed JSON:
1. Log validation error with raw payload
2. Increment error counter
3. Discard message
4. Continue processing

### Missing Required Fields

If message missing required fields:
1. Log warning with message and missing fields
2. Attempt to process with defaults (if sensible)
3. Or discard if critical field missing

### Schema Version Mismatch

If subscriber receives unexpected schema version:
1. Check if backward compatible
2. If compatible: process with warnings
3. If incompatible: log error and discard
4. Alert for scanner update needed

## Example Message Flows

### Typical Advertisement Flow

```
1. Scanner receives BLE advertisement
2. Scanner publishes to: bt-mqtt/raw/pi-zero-living-room
   Payload: {...device data...}
3. Subscriber receives from: bt-mqtt/raw/#
4. Subscriber processes and stores
```

### Heartbeat Flow

```
1. Scanner timer triggers (every 60 seconds)
2. Scanner publishes to: bt-mqtt/scanner/pi-zero-living-room/status
   Payload: {...status data...}
   Retained: true
3. Subscriber receives and updates scanner health
4. Monitoring system checks last heartbeat timestamp
```

## Testing Messages

For development and testing, you can publish messages manually:

```bash
# Publish test advertisement
mosquitto_pub -h mqtt.shypan.st -t bt-mqtt/raw/test-scanner -m '{
  "version": "1.0",
  "timestamp": "2026-01-11T12:00:00.000Z",
  "scanner_id": "test-scanner",
  "device": {
    "address": "AA:BB:CC:DD:EE:FF",
    "address_type": "public",
    "rssi": -65
  },
  "raw_data": "dGVzdA=="
}'

# Subscribe to all raw messages
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/raw/#' -v

# Subscribe to all status messages
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/scanner/+/status' -v
```

## Schema Evolution

### Versioning Strategy

- Use semantic versioning in `version` field
- **Major version** change: Breaking changes (incompatible schema)
- **Minor version** change: Backward-compatible additions
- **Patch version** change: Clarifications, no schema change

### Adding Fields

New optional fields can be added without version change:
- Subscriber must handle missing fields gracefully
- Old scanners continue working without new fields

### Removing Fields

Requires major version bump:
- Coordinate scanner and subscriber updates
- Support both versions during transition

### Example Evolution

**v1.0 → v1.1: Add optional field**
```json
{
  "version": "1.1",
  ...
  "device": {
    ...
    "tx_power": -10  // New optional field
  }
}
```

**v1.x → v2.0: Breaking change**
```json
{
  "version": "2.0",
  ...
  "device": {
    "mac": "AA:BB:CC:DD:EE:FF",  // Renamed from "address"
    ...
  }
}
```

## Best Practices

### Scanner (Publisher)

1. Use ISO 8601 timestamps with milliseconds
2. Uppercase MAC addresses with colons
3. Include all available advertisement data
4. Don't parse or interpret data (leave to subscriber)
5. Send heartbeats regularly

### Subscriber

1. Validate all incoming messages
2. Handle schema version differences gracefully
3. Log malformed messages for debugging
4. Use wildcard subscriptions for scalability
5. Process messages asynchronously

### General

1. Keep messages < 10 KB
2. Use JSON for human readability
3. Base64-encode binary data
4. Include metadata (version, timestamp) in all messages
5. Document schema changes

## Related Documentation

- [Architecture](architecture.md)
- [Scanner Design](scanner.md)
- [Subscriber Design](subscriber.md)
- [ADR-0003: MQTT Topic Structure](decisions/0003-mqtt-topic-structure.md)
