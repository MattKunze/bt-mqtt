# Feature: MQTT Subscriber

**Status:** In Progress  
**Milestone:** Phase 1 - Foundation  
**Owner:** TBD  
**Related ADRs:** [ADR-0002: TypeScript Subscriber](../../decisions/0002-typescript-subscriber.md), [ADR-0003: MQTT Topic Structure](../../decisions/0003-mqtt-topic-structure.md), [ADR-0004: Processing Pipeline](../../decisions/0004-processing-pipeline.md)

---

## Overview

The MQTT Subscriber is the data processing component that consumes BLE advertisement messages from the MQTT broker and stores them in PostgreSQL. It serves as the bridge between the message bus and persistent storage, forming the foundation for all data analysis and visualization.

### Motivation

The subscriber decouples data ingestion from data processing, allowing the scanner to operate independently of database availability. It provides a reliable entry point for all BLE data into the storage layer and sets up the processing pipeline for future parser plugins.

### Goals

- Subscribe to all BLE advertisement topics
- Parse and validate incoming MQTT messages
- Store raw advertisement data in PostgreSQL
- Provide reliable message processing
- Handle database connection failures gracefully
- Enable future parser plugin integration
- Monitor and log processing metrics

### Non-Goals

- Data parsing or transformation (Phase 2 parser system)
- Device identification or registry (Phase 2 feature)
- Real-time alerting or notifications
- Data aggregation or analytics

---

## Requirements

### Functional Requirements

1. **FR-1**: Connect to MQTT broker on startup
2. **FR-2**: Subscribe to `ble/raw/#` topic pattern (all scanners and devices)
3. **FR-3**: Parse JSON message payloads
4. **FR-4**: Validate message schema
5. **FR-5**: Insert raw messages into `raw_messages` table
6. **FR-6**: Handle duplicate messages gracefully (idempotent inserts if possible)
7. **FR-7**: Reconnect to MQTT broker automatically on disconnection
8. **FR-8**: Reconnect to database automatically on connection loss
9. **FR-9**: Log processing statistics (messages/sec, errors)
10. **FR-10**: Provide graceful shutdown with connection cleanup

### Non-Functional Requirements

1. **NFR-1**: **Reliability**: Process 100% of received messages under normal conditions
2. **NFR-2**: **Performance**: Process 100+ messages per second
3. **NFR-3**: **Latency**: Store messages in database within 500ms of receipt
4. **NFR-4**: **Resource Usage**: Use <100MB RAM under normal load
5. **NFR-5**: **Availability**: Recover from failures within 30 seconds
6. **NFR-6**: **Data Integrity**: Never lose messages due to database errors
7. **NFR-7**: **Observability**: Provide detailed logging and error reporting

---

## Dependencies

### Prerequisites

- TypeScript 5.0+ runtime (Node.js)
- MQTT broker with published messages
- PostgreSQL 16+ database
- MQTT client library (`mqtt` npm package)
- Kysely for database operations

### Blocked By

- MQTT Publisher (must publish messages first)
- Database Setup (tables must exist)

### Blocks

- Parser System (Phase 2)
- Device Registry (Phase 2)
- All downstream data processing

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────┐
│       MQTT Subscriber                    │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   MQTT Client                      │ │
│  │                                    │ │
│  │  - Connect to broker               │ │
│  │  - Subscribe to topics             │ │
│  │  - Handle reconnection             │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │   Message Handler                  │ │
│  │                                    │ │
│  │  - Parse JSON payload              │ │
│  │  - Validate schema                 │ │
│  │  - Extract metadata                │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │   Database Writer                  │ │
│  │                                    │ │
│  │  - Insert raw messages             │ │
│  │  - Handle constraints              │ │
│  │  - Retry on errors                 │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│        [PostgreSQL]                      │
└─────────────────────────────────────────┘
```

### Key Components

#### 1. MQTT Connection Manager
- Establishes connection to broker
- Subscribes to topic patterns
- Handles automatic reconnection
- Monitors connection health
- Processes incoming messages

#### 2. Message Parser
- Parses JSON payloads
- Validates against schema
- Extracts required fields
- Handles malformed messages
- Adds receipt timestamp

#### 3. Database Writer
- Inserts records into `raw_messages` table
- Uses Kysely for type-safe queries
- Implements connection pooling
- Handles database errors
- Provides retry logic

#### 4. Metrics Collector
- Tracks messages received
- Tracks messages processed successfully
- Tracks errors and failures
- Calculates processing rates
- Logs periodic statistics

### Data Flow

1. MQTT client receives message on subscribed topic
2. Message payload parsed as JSON
3. Schema validation performed
4. Message data extracted and normalized
5. Database insert operation executed
6. Success/failure logged
7. Metrics updated
8. Process repeats for next message

### Message Schema Validation

Expected message format (matches MQTT Publisher):
```typescript
interface RawAdvertisement {
  scanner_id: string;
  mac_address: string;
  rssi: number;
  timestamp: string; // ISO 8601
  manufacturer_data?: Record<string, string>;
  service_uuids?: string[];
  local_name?: string;
}
```

### Database Schema (Phase 1)

```sql
CREATE TABLE raw_messages (
  id BIGSERIAL PRIMARY KEY,
  scanner_id VARCHAR(255) NOT NULL,
  mac_address VARCHAR(17) NOT NULL,
  rssi INTEGER NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  manufacturer_data JSONB,
  service_uuids TEXT[],
  local_name VARCHAR(255),
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_payload JSONB NOT NULL
);

CREATE INDEX idx_raw_messages_mac ON raw_messages(mac_address);
CREATE INDEX idx_raw_messages_timestamp ON raw_messages(timestamp);
CREATE INDEX idx_raw_messages_scanner ON raw_messages(scanner_id);
```

### Configuration

```yaml
mqtt:
  broker:
    host: "localhost"
    port: 1883
    username: null
    password: null
  client:
    client_id: "bt-mqtt-subscriber-01"
    keep_alive: 60
    clean_session: true
  topics:
    - "ble/raw/#"

database:
  host: "localhost"
  port: 5432
  database: "btmqtt"
  user: "btmqtt"
  password: "password"
  pool:
    min: 2
    max: 10
    idle_timeout: 30000

logging:
  level: "info"
  format: "json"
  stats_interval: 60  # Log stats every 60 seconds
```

### Error Handling

- **MQTT Connection Failed**: Retry with exponential backoff
- **Invalid JSON**: Log error, skip message, increment error counter
- **Schema Validation Failed**: Log error, optionally store in error table
- **Database Connection Lost**: Buffer messages temporarily, reconnect
- **Insert Failed**: Log error, optionally dead-letter queue
- **Shutdown Signal**: Finish processing current message, then exit

### Graceful Shutdown

1. Receive SIGTERM/SIGINT
2. Stop accepting new messages
3. Wait for in-flight messages to complete (max 5 seconds)
4. Close MQTT connection
5. Close database connections
6. Log final statistics
7. Exit with code 0

---

## Testing Strategy

### Unit Tests

- [ ] Test JSON parsing with valid messages
- [ ] Test JSON parsing with invalid messages
- [ ] Test schema validation for required fields
- [ ] Test schema validation for optional fields
- [ ] Test database insert query generation
- [ ] Test message rate calculation

### Integration Tests

- [ ] Test MQTT subscription to broker
- [ ] Test message receipt and parsing
- [ ] Test database insert end-to-end
- [ ] Test reconnection to MQTT broker
- [ ] Test reconnection to database
- [ ] Test graceful shutdown
- [ ] Test handling of malformed messages

### Performance Tests

- [ ] Measure processing throughput (messages/sec)
- [ ] Measure end-to-end latency (MQTT to DB)
- [ ] Test with 100+ messages/sec sustained load
- [ ] Measure memory usage over 1-hour run
- [ ] Test with 10,000+ messages in rapid burst

### Manual Tests

- [ ] Verify data in database matches MQTT messages
- [ ] Test with multiple concurrent subscribers
- [ ] Verify message ordering (within single topic)
- [ ] Test with broker restart during operation
- [ ] Test with database restart during operation

---

## Open Questions

1. **Q**: Should we buffer messages in memory during database downtime?
   - **A**: Small buffer (100 messages) acceptable, drop if buffer full

2. **Q**: How to handle duplicate messages with same timestamp?
   - **A**: Allow duplicates in Phase 1, add deduplication in Phase 2

3. **Q**: Should we store invalid messages for debugging?
   - **A**: Yes - create `error_messages` table for failed parses

4. **Q**: What to do with messages from unknown scanners?
   - **A**: Store normally - no scanner validation in Phase 1

5. **Q**: Should we use database transactions for inserts?
   - **A**: Not necessary for single inserts, consider for batch inserts

---

## Implementation Checklist

### Setup
- [ ] Initialize TypeScript package
- [ ] Install dependencies (mqtt, kysely, pg)
- [ ] Set up project structure
- [ ] Configure TypeScript compiler
- [ ] Set up logging (winston or pino)

### MQTT Integration
- [ ] Implement MQTT client connection
- [ ] Implement topic subscription
- [ ] Add connection event handlers
- [ ] Implement reconnection logic
- [ ] Add message callback handler

### Message Processing
- [ ] Implement JSON parser
- [ ] Create message schema validation
- [ ] Add error handling for malformed messages
- [ ] Implement message normalization
- [ ] Add metrics tracking

### Database Integration
- [ ] Set up Kysely database client
- [ ] Configure connection pool
- [ ] Implement insert query
- [ ] Add database error handling
- [ ] Implement reconnection logic

### Application Lifecycle
- [ ] Implement startup sequence
- [ ] Add configuration loading
- [ ] Implement graceful shutdown
- [ ] Add signal handlers (SIGTERM/SIGINT)
- [ ] Add periodic stats logging

### Testing
- [ ] Write unit tests for parser
- [ ] Write integration tests
- [ ] Perform load testing
- [ ] Test error scenarios

### Documentation
- [ ] Document configuration options
- [ ] Document message schema
- [ ] Add troubleshooting guide
- [ ] Create deployment guide

### Deployment
- [ ] Create Dockerfile
- [ ] Add to docker-compose.yml
- [ ] Configure environment variables
- [ ] Add health check endpoint

---

## Acceptance Criteria

- [ ] Subscriber connects to MQTT broker successfully
- [ ] Subscriber receives messages on `ble/raw/#` topic
- [ ] Messages stored in database with all fields
- [ ] Invalid messages logged without crashing
- [ ] Subscriber processes 100+ messages/sec
- [ ] Subscriber reconnects after broker restart
- [ ] Subscriber reconnects after database restart
- [ ] Graceful shutdown completes without data loss
- [ ] Unit test coverage >80%
- [ ] Integration tests pass with broker and database
- [ ] Documentation complete and reviewed

---

## Related Features

- [MQTT Publisher](mqtt-publisher.md) - Produces messages consumed here
- [Raw Storage](raw-storage.md) - Database table structure
- [Database Setup](database-setup.md) - Schema and migrations
- [Parser System](../phase-2/parser-system.md) - Phase 2 enhancement

---

## References

- [mqtt npm package](https://github.com/mqttjs/MQTT.js)
- [Kysely documentation](https://kysely.dev/)
- [ADR-0002: TypeScript Subscriber](../../decisions/0002-typescript-subscriber.md)
- [ADR-0004: Processing Pipeline](../../decisions/0004-processing-pipeline.md)
- [MQTT Schema Documentation](../../mqtt-schema.md)
