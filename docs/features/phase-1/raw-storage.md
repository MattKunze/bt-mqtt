# Feature: Raw Storage

**Status:** In Progress  
**Milestone:** Phase 1 - Foundation  
**Owner:** TBD  
**Related ADRs:** [ADR-0004: Processing Pipeline](../../decisions/0004-processing-pipeline.md)

---

## Overview

Raw Storage is the foundational data persistence layer for the BT-MQTT system. It provides a comprehensive archive of all BLE advertisements received by the system, serving as both a data source for analytics and an audit trail for debugging and compliance.

### Motivation

Storing raw BLE advertisements enables:
- Complete audit trail of all devices detected
- Ability to reprocess data with new parsers
- Historical analysis and trend identification
- Debugging of device behavior and protocol issues
- Compliance with data retention requirements

### Goals

- Store all received BLE advertisements without data loss
- Maintain data integrity and consistency
- Provide efficient querying by device, time, and scanner
- Support high write throughput (100+ inserts/sec)
- Enable future data retention policies
- Serve as input for parser plugins (Phase 2)

### Non-Goals

- Parsed or processed data (separate tables in Phase 2)
- Real-time data aggregation
- Data transformation or normalization
- Automated data cleanup (manual in Phase 1)

---

## Requirements

### Functional Requirements

1. **FR-1**: Store all BLE advertisement fields received via MQTT
2. **FR-2**: Preserve original timestamp from scanner
3. **FR-3**: Record receipt timestamp for latency tracking
4. **FR-4**: Store complete raw payload as JSON for reprocessing
5. **FR-5**: Support querying by MAC address
6. **FR-6**: Support querying by time range
7. **FR-7**: Support querying by scanner ID
8. **FR-8**: Maintain referential integrity
9. **FR-9**: Handle concurrent inserts from multiple subscribers

### Non-Functional Requirements

1. **NFR-1**: **Performance**: Support 100+ inserts per second
2. **NFR-2**: **Storage Efficiency**: Optimize for time-series data patterns
3. **NFR-3**: **Query Performance**: Return results for single device <500ms
4. **NFR-4**: **Scalability**: Handle millions of records efficiently
5. **NFR-5**: **Availability**: Support hot backups without downtime
6. **NFR-6**: **Durability**: Zero data loss under normal operations
7. **NFR-7**: **Compliance**: Support data retention policies (Phase 2)

---

## Dependencies

### Prerequisites

- PostgreSQL 16+ database
- Database Setup (schema and migrations)
- Kysely migration system

### Blocked By

- Database Setup feature must be complete

### Blocks

- MQTT Subscriber (requires table to insert data)
- Parser System (Phase 2 - reads from raw_messages)
- Device Registry (Phase 2 - reads from raw_messages)

---

## Technical Design

### Architecture

```
┌──────────────────────────────────────────┐
│         Raw Storage Layer                 │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │   raw_messages Table                │ │
│  │                                     │ │
│  │  - id (BIGSERIAL)                   │ │
│  │  - scanner_id                       │ │
│  │  - mac_address                      │ │
│  │  - rssi                             │ │
│  │  - timestamp (scanner time)         │ │
│  │  - received_at (DB time)            │ │
│  │  - manufacturer_data (JSONB)        │ │
│  │  - service_uuids (TEXT[])           │ │
│  │  - local_name                       │ │
│  │  - raw_payload (JSONB)              │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │   Indexes                           │ │
│  │                                     │ │
│  │  - PK: id                           │ │
│  │  - idx: mac_address                 │ │
│  │  - idx: timestamp                   │ │
│  │  - idx: scanner_id                  │ │
│  │  - idx: received_at                 │ │
│  └─────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### Database Schema

```sql
CREATE TABLE raw_messages (
  -- Primary key
  id BIGSERIAL PRIMARY KEY,
  
  -- Message metadata
  scanner_id VARCHAR(255) NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  -- Device identification
  mac_address VARCHAR(17) NOT NULL,  -- Format: AA:BB:CC:DD:EE:FF
  
  -- Advertisement data
  rssi INTEGER NOT NULL,  -- Signal strength in dBm
  timestamp TIMESTAMPTZ NOT NULL,  -- Scanner timestamp
  
  -- Optional BLE data
  manufacturer_data JSONB,  -- Company ID -> hex data mapping
  service_uuids TEXT[],  -- Array of service UUIDs
  local_name VARCHAR(255),  -- Advertised device name
  
  -- Complete raw message for reprocessing
  raw_payload JSONB NOT NULL,
  
  -- Constraints
  CONSTRAINT rssi_range CHECK (rssi BETWEEN -128 AND 0),
  CONSTRAINT valid_mac CHECK (mac_address ~ '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
);

-- Performance indexes
CREATE INDEX idx_raw_messages_mac ON raw_messages(mac_address);
CREATE INDEX idx_raw_messages_timestamp ON raw_messages(timestamp);
CREATE INDEX idx_raw_messages_scanner ON raw_messages(scanner_id);
CREATE INDEX idx_raw_messages_received ON raw_messages(received_at);

-- Composite index for common query pattern
CREATE INDEX idx_raw_messages_mac_time ON raw_messages(mac_address, timestamp DESC);

-- GIN index for JSONB queries (optional, for advanced querying)
CREATE INDEX idx_raw_messages_manufacturer ON raw_messages USING GIN(manufacturer_data);

-- Comment the table
COMMENT ON TABLE raw_messages IS 'Raw BLE advertisement messages as received from scanners';
COMMENT ON COLUMN raw_messages.timestamp IS 'Timestamp from scanner when advertisement was detected';
COMMENT ON COLUMN raw_messages.received_at IS 'Timestamp when message was received by subscriber';
COMMENT ON COLUMN raw_messages.raw_payload IS 'Complete original message for reprocessing';
```

### Data Types and Constraints

| Column | Type | Nullable | Constraint | Purpose |
|--------|------|----------|------------|---------|
| `id` | BIGSERIAL | No | PK | Unique identifier, auto-increment |
| `scanner_id` | VARCHAR(255) | No | - | Identifies source scanner |
| `mac_address` | VARCHAR(17) | No | Format check | BLE device MAC address |
| `rssi` | INTEGER | No | -128 to 0 | Signal strength |
| `timestamp` | TIMESTAMPTZ | No | - | Scanner detection time |
| `received_at` | TIMESTAMPTZ | No | Default NOW() | DB receipt time |
| `manufacturer_data` | JSONB | Yes | - | Company-specific data |
| `service_uuids` | TEXT[] | Yes | - | Advertised services |
| `local_name` | VARCHAR(255) | Yes | - | Device name |
| `raw_payload` | JSONB | No | - | Full message backup |

### Index Strategy

1. **Primary Key (`id`)**: Auto-created, for unique identification
2. **MAC Address Index**: Most common filter, enables fast device lookups
3. **Timestamp Index**: Time-range queries, data retention cleanup
4. **Scanner Index**: Filter by scanner, troubleshooting
5. **Received At Index**: Monitoring, latency analysis
6. **Composite Index (mac + timestamp)**: Optimizes device history queries
7. **GIN Index (manufacturer_data)**: Advanced JSONB queries (optional)

### Common Query Patterns

#### Get Recent Messages for Device
```sql
SELECT * FROM raw_messages
WHERE mac_address = 'AA:BB:CC:DD:EE:FF'
ORDER BY timestamp DESC
LIMIT 100;
```

#### Get Messages in Time Range
```sql
SELECT * FROM raw_messages
WHERE timestamp BETWEEN '2026-01-11 00:00:00' AND '2026-01-11 23:59:59'
ORDER BY timestamp;
```

#### Get Messages from Scanner
```sql
SELECT * FROM raw_messages
WHERE scanner_id = 'scanner-01'
AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

#### Count Messages per Device
```sql
SELECT mac_address, COUNT(*) as message_count
FROM raw_messages
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY mac_address
ORDER BY message_count DESC;
```

### Storage Estimates

Assumptions:
- Average message size: 500 bytes (JSON + indexes)
- 50 devices in range
- 1 message per device per minute (after deduplication)
- = 50 messages/min = 3,000 messages/hour = 72,000 messages/day

Storage per day: 72,000 × 500 bytes = 36 MB/day ≈ 1 GB/month

For 100 devices: ≈ 2 GB/month
For 1000 devices: ≈ 20 GB/month

### Data Retention Strategy (Phase 2)

Future implementation will include:
- Retention policy (e.g., keep 90 days)
- Automated cleanup job
- Archive to cold storage
- Partitioning by time range

---

## Testing Strategy

### Unit Tests

- [ ] Test schema validation constraints (MAC format, RSSI range)
- [ ] Test default value generation (received_at)
- [ ] Test JSONB serialization/deserialization
- [ ] Test NULL handling for optional fields

### Integration Tests

- [ ] Test insert with all fields
- [ ] Test insert with minimal fields (only required)
- [ ] Test bulk insert performance (1000 records)
- [ ] Test concurrent inserts (10 connections)
- [ ] Test index effectiveness (query plans)
- [ ] Test constraint violations

### Performance Tests

- [ ] Measure insert throughput (inserts/sec)
- [ ] Measure query performance for common patterns
- [ ] Test with 1M+ records
- [ ] Measure storage growth over time
- [ ] Test index maintenance overhead

### Data Integrity Tests

- [ ] Verify no data loss during inserts
- [ ] Test rollback on constraint violation
- [ ] Verify timestamps are in correct timezone
- [ ] Test JSONB data integrity

---

## Open Questions

1. **Q**: Should we partition the table by time for better performance?
   - **A**: Not in Phase 1 - consider when data exceeds 10M records

2. **Q**: Should we enforce unique constraints on (mac, timestamp, scanner)?
   - **A**: No - allow duplicates in Phase 1 for simplicity

3. **Q**: Should we compress old data?
   - **A**: Defer to Phase 2 retention policy

4. **Q**: Should we separate manufacturer_data into a related table?
   - **A**: No - JSONB keeps schema simple and flexible

5. **Q**: Should we use BRIN indexes for time-series data?
   - **A**: Start with B-tree, evaluate BRIN if data exceeds 100M records

---

## Implementation Checklist

### Schema Design
- [x] Define table structure
- [x] Define column types and constraints
- [x] Design index strategy
- [x] Plan query patterns
- [ ] Document schema decisions

### Migration Creation
- [ ] Create Kysely migration file
- [ ] Implement `up` migration (create table)
- [ ] Implement `down` migration (drop table)
- [ ] Create indexes in migration
- [ ] Add table and column comments

### Testing
- [ ] Write schema validation tests
- [ ] Test insert operations
- [ ] Test query performance
- [ ] Test constraint violations
- [ ] Load test with realistic data

### Documentation
- [ ] Document table structure
- [ ] Document query patterns
- [ ] Document storage estimates
- [ ] Create ER diagram
- [ ] Add migration guide

### Optimization
- [ ] Analyze query plans
- [ ] Verify index usage
- [ ] Configure autovacuum settings
- [ ] Set table statistics targets

---

## Acceptance Criteria

- [ ] Table created successfully via migration
- [ ] All columns have correct types and constraints
- [ ] All indexes created and functional
- [ ] Insert operation succeeds with valid data
- [ ] Insert operation fails with invalid data (constraints work)
- [ ] Common queries execute in <500ms with 100K records
- [ ] System handles 100+ inserts/sec sustained
- [ ] No data loss or corruption under normal load
- [ ] Schema documented in database-schema.md
- [ ] Migration tested with up/down operations

---

## Related Features

- [Database Setup](database-setup.md) - Migration system
- [MQTT Subscriber](mqtt-subscriber.md) - Inserts data
- [Parser System](../phase-2/parser-system.md) - Reads data
- [Data Aggregation](../phase-3/data-aggregation.md) - Queries data

---

## References

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/16/datatype-json.html)
- [PostgreSQL Indexing Documentation](https://www.postgresql.org/docs/16/indexes.html)
- [Time-Series Data in PostgreSQL](https://www.timescale.com/blog/time-series-data-postgresql-10-vs-timescaledb-816/)
- [Database Schema Documentation](../../database-schema.md)
