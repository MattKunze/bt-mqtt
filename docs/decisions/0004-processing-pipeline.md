# 0004. Raw Capture vs Processing Split

**Date:** 2026-01-11

**Status:** Accepted

## Context

BLE advertisement data needs to be captured, parsed, and stored. We need to decide where in the system to perform parsing and data transformation. Key considerations:

- Scanner agents run on potentially resource-constrained hardware (Raspberry Pi)
- Different device types require different parsing logic (Govee, SwitchBot, iBeacon, etc.)
- Parsing logic will evolve and requires updates
- Some advertisements are from unknown/unsupported devices
- System should be debuggable and allow replaying raw data

We need to decide the responsibility boundary between scanner and subscriber.

## Decision

The scanner agent will capture and publish **raw, unprocessed** BLE advertisement data to MQTT. All parsing, interpretation, and transformation will occur in the subscriber component.

Scanner responsibilities:
- Scan for BLE advertisements
- Basic deduplication (time-based, see ADR-0005)
- Publish raw advertisement data (MAC, RSSI, manufacturer data) as JSON to MQTT
- No device-specific parsing or interpretation

Subscriber responsibilities:
- Receive raw advertisements from MQTT
- Route advertisements to appropriate parsers based on manufacturer ID or MAC prefix
- Parse manufacturer-specific data formats
- Store parsed data in PostgreSQL

## Consequences

### Positive

- **Simple scanner**: Scanner code remains minimal and stable, reducing need for updates
- **Centralized parsing**: All device-specific logic lives in one place (subscriber)
- **Easy parser updates**: Can update parsing logic without touching scanners or MQTT infrastructure
- **Raw data preservation**: Can replay raw MQTT messages for debugging or reprocessing
- **Resource efficiency**: Keeps CPU/memory usage low on scanner devices
- **Unknown device handling**: Scanner doesn't need to know about supported devices
- **Testing**: Can test parsers independently with captured raw data
- **Multiple parsers**: Can run multiple subscriber instances with different parser sets if needed
- **Audit trail**: Raw advertisements can be logged for compliance or debugging

### Negative

- **Network bandwidth**: Sends all raw advertisements over MQTT, including unsupported devices
- **Subscriber complexity**: Subscriber is more complex than if scanners did parsing
- **Duplicate effort**: Some processing (MAC validation) might happen in both components

### Neutral

- **Latency**: Adds minimal latency (milliseconds) for MQTT hop and parsing
- **Coupling**: Scanner and subscriber are loosely coupled via JSON schema

## Alternatives Considered

### Parse in scanner, publish structured data

- **Pros**: Lower MQTT bandwidth, simpler subscriber
- **Cons**: Parser updates require scanner updates, harder to debug, can't replay raw data, scanner needs device-specific logic, more complex scanner code

### Hybrid: Basic parsing in scanner, advanced in subscriber

- **Pros**: Some bandwidth reduction, some flexibility
- **Cons**: Unclear responsibility boundary, complexity in both places, harder to maintain

### Parse in separate service (scanner → raw → parser → structured → subscriber)

- **Pros**: Maximum separation of concerns
- **Cons**: Additional complexity, another component to deploy, added latency, overkill for this use case

### Stream processing (Kafka, etc.)

- **Pros**: Better for high-volume scenarios, replay capabilities
- **Cons**: Significant infrastructure overhead, unnecessary complexity for BLE advertisement volumes
