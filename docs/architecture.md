# Architecture

**Last Updated:** 2026-01-11

## Overview

BT-MQTT is a data pipeline system for capturing Bluetooth Low Energy (BLE) advertisements and processing them into structured, queryable data. The system follows a clean separation of concerns with three main components:

1. **Scanner Agent** - Captures raw BLE advertisements
2. **MQTT Broker** - Streams data in real-time
3. **Subscriber Service** - Processes and stores data

## System Architecture

```
┌─────────────────────────────────────────────────┐
│         BLE Devices (Environmental Sensors,      │
│         Beacons, Proximity Sensors, etc.)        │
└──────────────────┬──────────────────────────────┘
                   │ BLE Advertisements
                   │ (Broadcast, ~every 1-5 seconds)
                   ↓
┌─────────────────────────────────────────────────┐
│  Scanner Agent (Raspberry Pi Zero W)            │
│  ┌───────────────────────────────────────────┐  │
│  │ BLE Scanner (Python/bleak)                │  │
│  │ - Passive scanning                        │  │
│  │ - Deduplication (time-based)              │  │
│  │ - Blocklist filtering                     │  │
│  └───────────┬───────────────────────────────┘  │
│              │                                   │
│  ┌───────────▼───────────────────────────────┐  │
│  │ MQTT Publisher                            │  │
│  │ - Publish to bt-mqtt/raw/{scanner_id}     │  │
│  │ - Heartbeat to bt-mqtt/scanner/{id}/status│  │
│  └───────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────┘
                   │ MQTT (QoS 1)
                   │ External Broker: mqtt.shypan.st
                   ↓
┌─────────────────────────────────────────────────┐
│  Subscriber Service (Docker Container)          │
│  ┌───────────────────────────────────────────┐  │
│  │ MQTT Subscriber (TypeScript)              │  │
│  │ - Subscribe to bt-mqtt/raw/#              │  │
│  │ - Message validation                      │  │
│  └───────────┬───────────────────────────────┘  │
│              │                                   │
│  ┌───────────▼───────────────────────────────┐  │
│  │ Raw Archival Storage                      │  │
│  │ - Complete message preservation           │  │
│  │ - INSERT into raw_advertisements          │  │
│  └───────────┬───────────────────────────────┘  │
│              │                                   │
│  ┌───────────▼───────────────────────────────┐  │
│  │ Parser Registry                           │  │
│  │ - Device type detection                   │  │
│  │ - Route to appropriate parser             │  │
│  └───────────┬───────────────────────────────┘  │
│              │                                   │
│  ┌───────────▼───────────────────────────────┐  │
│  │ Device Parsers (Pluggable)                │  │
│  │ - Environmental: temp, humidity, pressure │  │
│  │ - Beacon: proximity, battery              │  │
│  │ - Custom: extensible                      │  │
│  └───────────┬───────────────────────────────┘  │
│              │                                   │
│  ┌───────────▼───────────────────────────────┐  │
│  │ Processed Data Storage                    │  │
│  │ - INSERT into sensor_readings             │  │
│  │ - UPDATE devices registry                 │  │
│  └───────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────┘
                   │ PostgreSQL (Kysely)
                   ↓
┌─────────────────────────────────────────────────┐
│  PostgreSQL Database                            │
│  ┌─────────────────────────────────────────┐    │
│  │ raw_advertisements (Archival)           │    │
│  │ - Complete MQTT payload (JSONB)         │    │
│  │ - Never deleted, full history           │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ sensor_readings (Time-Series)           │    │
│  │ - Parsed sensor values                  │    │
│  │ - Optimized for queries                 │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ devices (Registry)                      │    │
│  │ - Device metadata and state             │    │
│  │ - Parser type mapping                   │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ scanners (Agent Registry)               │    │
│  │ - Scanner locations and health          │    │
│  └─────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────┘
                   │ (Future Phase)
                   ↓
┌─────────────────────────────────────────────────┐
│  Visualization & Analytics                      │
│  - Grafana Dashboards (time-series)             │
│  - Custom Web App (Vite + React)                │
│  - Real-time monitoring                         │
└─────────────────────────────────────────────────┘
```

## Component Details

### Scanner Agent

**Technology:** Python 3.11+ with `bleak` library
**Deployment:** Raspberry Pi Zero W (or any Linux system with Bluetooth)
**Purpose:** Lightweight BLE data collection

**Responsibilities:**
- Passive BLE scanning (no device connections)
- Extract advertisement data (manufacturer data, service UUIDs, RSSI)
- Apply deduplication to reduce message volume
- Filter devices via blocklist
- Publish to MQTT with minimal processing
- Send periodic heartbeat messages

**Design Principles:**
- Keep it simple - this runs on constrained hardware
- No business logic - just data collection
- Resilient to MQTT disconnections (drop messages, no buffering)
- Configurable via YAML file

**Related Documentation:**
- [Scanner Design](scanner.md)
- [ADR-0001: Python Scanner](decisions/0001-python-scanner.md)
- [ADR-0005: Deduplication Strategy](decisions/0005-deduplication-strategy.md)
- [ADR-0009: MQTT Failure Handling](decisions/0009-mqtt-failure-drop-messages.md)

### MQTT Broker

**Technology:** Mosquitto (external deployment at mqtt.shypan.st)
**Purpose:** Real-time message streaming

**Topics:**
- `bt-mqtt/raw/{scanner_id}` - Raw BLE advertisements
- `bt-mqtt/scanner/{scanner_id}/status` - Scanner health/heartbeat
- `bt-mqtt/command/{scanner_id}` - Optional: Commands to scanner

**Configuration:**
- QoS 1 (at least once delivery)
- No authentication required
- No TLS (internal network)

**Related Documentation:**
- [MQTT Schema](mqtt-schema.md)
- [ADR-0003: MQTT Topic Structure](decisions/0003-mqtt-topic-structure.md)

### Subscriber Service

**Technology:** TypeScript/Node.js 20+ with Kysely
**Deployment:** Docker container
**Purpose:** Data processing and persistence

**Responsibilities:**
- Subscribe to all raw advertisement topics
- Validate incoming messages
- Archive complete raw data (never loses information)
- Route messages to appropriate parsers
- Extract and store sensor readings
- Maintain device registry
- Track scanner health

**Design Principles:**
- Separation of raw archival from processing
- Pluggable parser system for extensibility
- Type-safe database access with Kysely
- Comprehensive error handling and logging
- All business logic lives here (not in scanner)

**Related Documentation:**
- [Subscriber Design](subscriber.md)
- [ADR-0002: TypeScript Subscriber](decisions/0002-typescript-subscriber.md)
- [ADR-0004: Processing Pipeline](decisions/0004-processing-pipeline.md)
- [ADR-0006: Parser Plugin System](decisions/0006-parser-plugin-system.md)

### PostgreSQL Database

**Technology:** PostgreSQL 16+
**Deployment:** Docker container
**Purpose:** Persistent storage for raw and processed data

**Schema Design:**
- **raw_advertisements**: Complete archival of all MQTT messages
- **sensor_readings**: Parsed time-series sensor data
- **devices**: Device registry with metadata and parser mapping
- **scanners**: Scanner agent registry and health tracking

**Key Features:**
- JSONB columns for flexible schemas
- Indexes optimized for time-series queries
- Kysely migrations for schema evolution
- Retention policies (configurable, e.g., 90 days for raw data)

**Related Documentation:**
- [Database Schema](database-schema.md)
- [ADR-0008: Kysely Migrations](decisions/0008-kysely-migrations.md)

## Data Flow

### Raw Advertisement Flow

```
1. BLE Device broadcasts advertisement
2. Scanner receives advertisement via Bluetooth
3. Scanner checks deduplication cache
   - If seen recently → drop
   - If not seen → continue
4. Scanner checks blocklist
   - If blocked → drop
   - If allowed → continue
5. Scanner publishes to MQTT: bt-mqtt/raw/{scanner_id}
6. Subscriber receives message
7. Subscriber validates message format
8. Subscriber inserts into raw_advertisements table
9. Subscriber routes to parser registry
10. Parser extracts sensor data (if applicable)
11. Subscriber inserts into sensor_readings table
12. Subscriber updates devices registry
```

### Scanner Heartbeat Flow

```
1. Scanner timer triggers (every 60 seconds)
2. Scanner collects metrics:
   - Uptime
   - Messages sent
   - Devices seen
   - Bluetooth adapter status
3. Scanner publishes to bt-mqtt/scanner/{scanner_id}/status
4. Subscriber receives heartbeat
5. Subscriber updates scanners table
6. Optional: Trigger alerts if scanner goes offline
```

## Deployment Architecture

### Development Environment

```
Laptop/Desktop (devenv)
├── PostgreSQL (Docker)
├── Subscriber (Node.js, running locally)
└── Scanner (Python, requires Bluetooth adapter or mocked)
```

### Production Environment

```
Home Server
├── Docker Compose Stack
│   ├── PostgreSQL container
│   └── Subscriber container
│
Raspberry Pi Zero W (separate device)
└── Scanner agent (systemd service)
```

**Network:**
- MQTT Broker: mqtt.shypan.st (external, accessible to all)
- PostgreSQL: Internal to Docker network
- Scanner: WiFi connection to network, publishes to MQTT broker

## Key Design Decisions

### Why Separate Scanner from Processing?

**Rationale:**
1. **Simplicity** - Scanner runs on constrained hardware (Pi Zero W)
2. **Maintainability** - Update parsers without redeploying scanner
3. **Reprocessing** - Can reprocess historical raw data with new parsers
4. **Resilience** - Scanner failure doesn't lose processing logic

**Trade-off:** Adds complexity of MQTT as intermediary, but provides flexibility.

**Related:** [ADR-0004: Processing Pipeline](decisions/0004-processing-pipeline.md)

### Why Archive Raw Data?

**Rationale:**
1. **Completeness** - Never lose information from devices
2. **Debugging** - Investigate issues with original data
3. **Reprocessing** - Improve parsers and reprocess historical data
4. **Discovery** - Analyze unknown device types

**Trade-off:** Storage costs, but acceptable for 90-day retention.

### Why No MQTT Buffering on Scanner?

**Rationale:**
1. **Simplicity** - Avoids complex buffering logic
2. **Storage** - Pi Zero W has limited storage
3. **Acceptable Loss** - Data is continuous stream, brief outages OK
4. **Resilience** - No risk of buffer overflow or disk full

**Trade-off:** May lose messages during MQTT broker outages, but deemed acceptable.

**Related:** [ADR-0009: MQTT Failure Handling](decisions/0009-mqtt-failure-drop-messages.md)

## Scalability Considerations

### Current Design (Single Scanner)

- **Scanner**: One Raspberry Pi Zero W
- **Subscriber**: Single instance, handles ~100-1000 messages/sec
- **Database**: Single PostgreSQL instance

### Future Scaling (Multiple Scanners)

The architecture supports multiple scanners:
- Each scanner has unique `scanner_id`
- Each publishes to separate topic: `bt-mqtt/raw/{scanner_id}`
- Subscriber subscribes to wildcard: `bt-mqtt/raw/#`
- Database stores scanner_id for all records

### Future Scaling (High Volume)

If volume exceeds single subscriber capacity:
- **Option 1**: Multiple subscriber instances with topic partitioning
- **Option 2**: Use MQTT broker with message queuing
- **Option 3**: Add message queue between MQTT and processing

Current design supports ~1000 messages/sec, sufficient for initial deployment.

## Security Considerations

### Current Security Posture

- **MQTT**: No authentication, internal network only
- **PostgreSQL**: Password authentication, Docker network only
- **Scanner**: No sensitive data, read-only BLE scanning

### Production Hardening (Future)

If deploying to untrusted networks:
1. Add MQTT TLS and authentication
2. Use PostgreSQL TLS connections
3. Implement API authentication for query/visualization layer
4. Network segmentation (VLANs)

## Monitoring & Observability

### Current Approach

- **Logging**: JSON-formatted logs from both scanner and subscriber
- **Scanner Health**: Heartbeat messages every 60 seconds
- **Database**: Standard PostgreSQL logging

### Future Enhancements

- Metrics export (Prometheus)
- Distributed tracing (OpenTelemetry)
- Alerting (e.g., scanner offline > 5 minutes)
- Grafana dashboards for system health

## Error Handling Philosophy

### Scanner

- **BLE Errors**: Log and continue scanning
- **MQTT Disconnection**: Drop messages, attempt reconnection
- **Configuration Errors**: Fail fast on startup

### Subscriber

- **MQTT Disconnection**: Automatic reconnection by library
- **Database Errors**: Retry with exponential backoff
- **Parser Errors**: Log error, skip message, continue processing
- **Invalid Messages**: Log validation error, discard message

### Database

- **Connection Loss**: Connection pool handles reconnection
- **Constraint Violations**: Log and skip (e.g., duplicate keys)
- **Disk Full**: Critical error, alert required

## Technology Choices

See individual ADRs for detailed rationale:

- [ADR-0001: Python for Scanner](decisions/0001-python-scanner.md)
- [ADR-0002: TypeScript for Subscriber](decisions/0002-typescript-subscriber.md)
- [ADR-0008: Kysely for Database](decisions/0008-kysely-migrations.md)

## Future Architecture Considerations

### Phase 3+: Analytics & Aggregation

May add dedicated analytics service:
```
PostgreSQL → Analytics Service → Aggregated Views/Tables
                                → API for Queries
```

### Phase 4: Visualization

Add visualization layer:
```
PostgreSQL → Grafana (time-series dashboards)
           → Web App (Vite + React, custom UI)
```

## Related Documentation

- [MQTT Schema](mqtt-schema.md)
- [Database Schema](database-schema.md)
- [Scanner Design](scanner.md)
- [Subscriber Design](subscriber.md)
- [Deployment Guide](deployment.md)
- [All ADRs](decisions/)
