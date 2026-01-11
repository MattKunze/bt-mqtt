# Feature: BLE Scanner

**Status:** In Progress  
**Milestone:** Phase 1 - Foundation  
**Owner:** TBD  
**Related ADRs:** [ADR-0001: Python Scanner](../../decisions/0001-python-scanner.md)

---

## Overview

The BLE Scanner is the data ingestion component of the BT-MQTT system. It continuously scans for Bluetooth Low Energy (BLE) advertisements from nearby devices and prepares them for publishing to the MQTT broker. This component forms the foundation of the entire data pipeline.

### Motivation

BLE devices constantly broadcast advertisement packets containing identification and telemetry data. The BLE Scanner captures these packets to enable monitoring, tracking, and analysis of BLE-enabled devices without requiring active connections to them.

### Goals

- Continuously scan for BLE advertisements
- Capture raw advertisement data including MAC address, RSSI, and manufacturer data
- Provide stable, long-running operation
- Handle BLE adapter initialization and error recovery
- Prepare data for downstream MQTT publishing

### Non-Goals

- Device connection (only passive scanning)
- Data parsing or interpretation (handled by subscriber)
- Message deduplication (Phase 2 feature)
- Device filtering (Phase 2 feature)

---

## Requirements

### Functional Requirements

1. **FR-1**: Initialize BLE adapter on startup
2. **FR-2**: Scan continuously for BLE advertisements
3. **FR-3**: Capture advertisement data including:
   - MAC address
   - RSSI (signal strength)
   - Manufacturer data (raw bytes)
   - Service UUIDs
   - Local name (if present)
   - Timestamp of detection
4. **FR-4**: Handle multiple simultaneous advertisement detections
5. **FR-5**: Restart scanning automatically if adapter connection is lost
6. **FR-6**: Log scanning lifecycle events (start, stop, errors)
7. **FR-7**: Provide graceful shutdown on SIGTERM/SIGINT

### Non-Functional Requirements

1. **NFR-1**: **Reliability**: Run continuously for weeks without restart
2. **NFR-2**: **Performance**: Process 100+ advertisements per second
3. **NFR-3**: **Latency**: Detect advertisements within 1 second of broadcast
4. **NFR-4**: **Resource Usage**: Use <50MB RAM under normal load
5. **NFR-5**: **Compatibility**: Work with standard BLE adapters on Linux
6. **NFR-6**: **Logging**: Provide debug-level visibility into scanning operations
7. **NFR-7**: **Startup Time**: Initialize and begin scanning within 5 seconds

---

## Dependencies

### Prerequisites

- Python 3.11+ runtime
- `bleak` library for BLE operations
- Linux system with BlueZ stack (or macOS for development)
- BLE adapter (USB or built-in)

### Blocked By

- None (first component to implement)

### Blocks

- MQTT Publisher (requires scanner data)
- All downstream processing

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────┐
│         BLE Scanner                  │
│                                      │
│  ┌──────────────────────────────┐   │
│  │   Bleak BLE Client           │   │
│  │                              │   │
│  │  - Initialize adapter        │   │
│  │  - Start scanning            │   │
│  │  - Handle callbacks          │   │
│  └──────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  ┌──────────────────────────────┐   │
│  │   Advertisement Handler      │   │
│  │                              │   │
│  │  - Extract MAC address       │   │
│  │  - Capture RSSI              │   │
│  │  - Extract manufacturer data │   │
│  │  - Add timestamp             │   │
│  └──────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  ┌──────────────────────────────┐   │
│  │   Data Queue                 │   │
│  │   (for MQTT Publisher)       │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Key Components

#### 1. BLE Adapter Manager
- Initializes BLE adapter using `bleak`
- Handles adapter detection and selection
- Provides error recovery for adapter disconnection

#### 2. Advertisement Scanner
- Registers advertisement callback
- Processes incoming BLE advertisements
- Extracts relevant data fields
- Adds system timestamps

#### 3. Data Normalizer
- Converts advertisement data to standard format
- Handles missing or malformed fields
- Prepares data for MQTT publishing

### Data Flow

1. Scanner initializes BLE adapter
2. Advertisement callback registered
3. BLE device broadcasts advertisement
4. Callback receives advertisement data
5. Data normalized and timestamped
6. Data placed in queue for MQTT publisher
7. Process repeats continuously

### Data Format

```python
{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "rssi": -67,
    "timestamp": "2026-01-11T10:30:45.123Z",
    "manufacturer_data": {
        "4c00": "02150123..."  # Company ID: hex data
    },
    "service_uuids": ["0000180f-0000-1000-8000-00805f9b34fb"],
    "local_name": "TempSensor_01",
    "raw_data": "..."  # Full advertisement packet
}
```

### Error Handling

- **Adapter Not Found**: Log error and retry with exponential backoff
- **Scan Start Failure**: Attempt restart up to 3 times
- **Advertisement Parse Error**: Log warning and skip malformed packet
- **Callback Exception**: Log error but continue scanning

### Configuration

```yaml
scanner:
  adapter_name: "hci0"  # BLE adapter to use
  scan_interval: 0.1    # Seconds between scan windows
  scan_window: 0.1      # Duration of each scan window
  passive_scan: true    # Use passive scanning (no scan requests)
  log_level: "info"     # Logging verbosity
```

---

## Testing Strategy

### Unit Tests

- [ ] Test adapter initialization with valid adapter
- [ ] Test adapter initialization with missing adapter
- [ ] Test advertisement data extraction
- [ ] Test data normalization for various advertisement formats
- [ ] Test timestamp generation
- [ ] Test graceful shutdown

### Integration Tests

- [ ] Test scanning with real BLE adapter
- [ ] Test advertisement detection from test beacon
- [ ] Test continuous scanning for 5+ minutes
- [ ] Test adapter reconnection after disconnect
- [ ] Test signal handler (SIGTERM/SIGINT)

### Performance Tests

- [ ] Measure CPU usage under continuous scanning
- [ ] Measure memory usage over 1-hour scan
- [ ] Verify 100+ advertisements/sec handling
- [ ] Test with 50+ devices in range simultaneously

### Manual Tests

- [ ] Verify scanning on target hardware (Raspberry Pi, Linux PC)
- [ ] Test with various BLE devices (beacons, sensors, phones)
- [ ] Verify RSSI accuracy
- [ ] Test adapter selection with multiple adapters

---

## Open Questions

1. **Q**: Should we support Windows BLE adapters?
   - **A**: Deferred - Focus on Linux first, Windows support if needed

2. **Q**: How to handle BLE extended advertisements (>31 bytes)?
   - **A**: TBD - Research bleak support for extended advertisements

3. **Q**: Should we filter by signal strength at scanner level?
   - **A**: No - Filter in Phase 2 deduplication, keep scanner simple

4. **Q**: How to handle duplicate adapter names?
   - **A**: Use adapter MAC address as fallback identifier

---

## Implementation Checklist

### Setup
- [ ] Install bleak library
- [ ] Create scanner package structure
- [ ] Set up logging configuration
- [ ] Create configuration schema

### Core Functionality
- [ ] Implement BLE adapter initialization
- [ ] Implement advertisement callback handler
- [ ] Implement data extraction and normalization
- [ ] Implement timestamp generation
- [ ] Create data queue for MQTT publisher

### Error Handling
- [ ] Add adapter initialization retry logic
- [ ] Add scan restart on failure
- [ ] Add exception handling in callback
- [ ] Implement graceful shutdown

### Testing
- [ ] Write unit tests for data extraction
- [ ] Write integration tests with test beacon
- [ ] Perform performance testing
- [ ] Test on target hardware

### Documentation
- [ ] Document adapter requirements
- [ ] Document supported platforms
- [ ] Add troubleshooting guide
- [ ] Document configuration options

### Deployment
- [ ] Create Dockerfile (if containerizing scanner)
- [ ] Document installation steps
- [ ] Create systemd service file
- [ ] Add health check mechanism

---

## Acceptance Criteria

- [ ] Scanner initializes BLE adapter successfully
- [ ] Scanner detects advertisements from test beacon
- [ ] Advertisement data includes MAC, RSSI, timestamp, manufacturer data
- [ ] Scanner runs continuously for 1+ hour without errors
- [ ] Scanner handles graceful shutdown on SIGTERM
- [ ] Unit test coverage >80%
- [ ] Integration tests pass with real BLE adapter
- [ ] Documentation complete and reviewed

---

## Related Features

- [MQTT Publisher](mqtt-publisher.md) - Consumes scanner data
- [Deduplication](../phase-2/deduplication.md) - Phase 2 enhancement
- [Blocklist](../phase-2/blocklist.md) - Phase 2 filtering

---

## References

- [bleak documentation](https://bleak.readthedocs.io/)
- [BLE Advertisement Specification](https://www.bluetooth.com/specifications/specs/core-specification/)
- [ADR-0001: Python Scanner](../../decisions/0001-python-scanner.md)
