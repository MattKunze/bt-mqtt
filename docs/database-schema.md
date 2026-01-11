# Database Schema Documentation

**Last Updated:** 2026-01-11  
**Database:** PostgreSQL 14+  
**Query Builder:** Kysely (see [ADR-0008](decisions/0008-kysely-migrations.md))

## Overview

This document describes the PostgreSQL database schema for the bt-mqtt system. The schema is designed to efficiently store and query Bluetooth Low Energy (BLE) advertisement data with the following goals:

- **Time-series optimization**: Fast queries on recent data
- **Flexible data storage**: JSONB for varying device payloads
- **Data lineage**: Track raw advertisements to parsed sensor readings
- **Device registry**: Maintain device metadata and status
- **Scanner tracking**: Monitor scanner health and location

## Schema Diagram

```
┌─────────────────────┐
│     scanners        │
│  PK: scanner_id     │
└──────────┬──────────┘
           │
           │ (1:N)
           │
┌──────────▼──────────────────┐      ┌─────────────────────┐
│  raw_advertisements         │      │      devices        │
│  PK: id                     │      │  PK: address        │
│  FK: scanner_id             │      └──────────┬──────────┘
│  IDX: device_address        │                 │
└──────────┬──────────────────┘                 │
           │                                    │
           │ (1:N)                              │
           │                                    │
┌──────────▼──────────────────┐                 │
│   sensor_readings           │                 │
│  PK: id                     │                 │
│  FK: raw_advertisement_id   │◄────────────────┘
│  IDX: device_address        │       (1:N)
│  IDX: timestamp             │
└─────────────────────────────┘
```

## Table Definitions

### 1. `raw_advertisements`

Stores every BLE advertisement packet received by scanners. This is the primary data ingestion table.

#### CREATE TABLE Statement

```sql
CREATE TABLE raw_advertisements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scanner_id TEXT NOT NULL,
    device_address TEXT NOT NULL,
    device_name TEXT,
    rssi SMALLINT NOT NULL,
    raw_payload JSONB NOT NULL,
    
    CONSTRAINT raw_advertisements_rssi_range 
        CHECK (rssi >= -128 AND rssi <= 0)
);

-- Indexes
CREATE INDEX idx_raw_adv_received_at 
    ON raw_advertisements (received_at DESC);
    
CREATE INDEX idx_raw_adv_device_address 
    ON raw_advertisements (device_address, received_at DESC);
    
CREATE INDEX idx_raw_adv_scanner_id 
    ON raw_advertisements (scanner_id, received_at DESC);
    
CREATE INDEX idx_raw_adv_payload_gin 
    ON raw_advertisements USING GIN (raw_payload);

-- Foreign key
ALTER TABLE raw_advertisements 
    ADD CONSTRAINT fk_scanner 
    FOREIGN KEY (scanner_id) REFERENCES scanners(scanner_id) 
    ON DELETE CASCADE;
```

#### Column Details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | Primary key, auto-generated |
| `received_at` | TIMESTAMPTZ | NO | When the advertisement was received (with timezone) |
| `scanner_id` | TEXT | NO | Identifier of the scanner that received this advertisement |
| `device_address` | TEXT | NO | Bluetooth MAC address (e.g., "AA:BB:CC:DD:EE:FF") |
| `device_name` | TEXT | YES | Device name from advertisement (if present) |
| `rssi` | SMALLINT | NO | Signal strength in dBm (-128 to 0) |
| `raw_payload` | JSONB | NO | Complete advertisement data as JSON |

#### Kysely Type Definition

```typescript
export interface RawAdvertisement {
  id: Generated<string>;
  received_at: Generated<Date>;
  scanner_id: string;
  device_address: string;
  device_name: string | null;
  rssi: number;
  raw_payload: unknown; // JSONB
}

export interface RawAdvertisementInsert {
  id?: string;
  received_at?: Date;
  scanner_id: string;
  device_address: string;
  device_name?: string | null;
  rssi: number;
  raw_payload: unknown;
}

export interface RawAdvertisementUpdate {
  scanner_id?: string;
  device_address?: string;
  device_name?: string | null;
  rssi?: number;
  raw_payload?: unknown;
}
```

### 2. `sensor_readings`

Stores parsed sensor data extracted from advertisements. Each reading references its source advertisement.

#### CREATE TABLE Statement

```sql
CREATE TABLE sensor_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    device_address TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    readings JSONB NOT NULL,
    raw_advertisement_id UUID NOT NULL,
    
    CONSTRAINT sensor_readings_sensor_type_valid 
        CHECK (sensor_type IN (
            'temperature', 'humidity', 'pressure', 'battery',
            'motion', 'light', 'door', 'button', 'acceleration',
            'gyroscope', 'magnetometer', 'energy', 'power',
            'voltage', 'current', 'co2', 'tvoc', 'pm25', 'custom'
        ))
);

-- Indexes
CREATE INDEX idx_sensor_readings_timestamp 
    ON sensor_readings (timestamp DESC);
    
CREATE INDEX idx_sensor_readings_device_address 
    ON sensor_readings (device_address, timestamp DESC);
    
CREATE INDEX idx_sensor_readings_sensor_type 
    ON sensor_readings (sensor_type, timestamp DESC);
    
CREATE INDEX idx_sensor_readings_device_sensor 
    ON sensor_readings (device_address, sensor_type, timestamp DESC);
    
CREATE INDEX idx_sensor_readings_readings_gin 
    ON sensor_readings USING GIN (readings);

-- Foreign key
ALTER TABLE sensor_readings 
    ADD CONSTRAINT fk_raw_advertisement 
    FOREIGN KEY (raw_advertisement_id) 
    REFERENCES raw_advertisements(id) 
    ON DELETE CASCADE;
```

#### Column Details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | Primary key, auto-generated |
| `timestamp` | TIMESTAMPTZ | NO | When the reading was taken (from device or received_at) |
| `device_address` | TEXT | NO | Bluetooth MAC address |
| `sensor_type` | TEXT | NO | Type of sensor (enum constraint) |
| `readings` | JSONB | NO | Sensor data (structure varies by sensor_type) |
| `raw_advertisement_id` | UUID | NO | Reference to source advertisement |

#### Kysely Type Definition

```typescript
export type SensorType = 
  | 'temperature'
  | 'humidity'
  | 'pressure'
  | 'battery'
  | 'motion'
  | 'light'
  | 'door'
  | 'button'
  | 'acceleration'
  | 'gyroscope'
  | 'magnetometer'
  | 'energy'
  | 'power'
  | 'voltage'
  | 'current'
  | 'co2'
  | 'tvoc'
  | 'pm25'
  | 'custom';

export interface SensorReading {
  id: Generated<string>;
  timestamp: Date;
  device_address: string;
  sensor_type: SensorType;
  readings: unknown; // JSONB
  raw_advertisement_id: string;
}

export interface SensorReadingInsert {
  id?: string;
  timestamp: Date;
  device_address: string;
  sensor_type: SensorType;
  readings: unknown;
  raw_advertisement_id: string;
}

export interface SensorReadingUpdate {
  timestamp?: Date;
  device_address?: string;
  sensor_type?: SensorType;
  readings?: unknown;
  raw_advertisement_id?: string;
}
```

### 3. `devices`

Registry of all discovered BLE devices with metadata and tracking information.

#### CREATE TABLE Statement

```sql
CREATE TABLE devices (
    address TEXT PRIMARY KEY,
    name TEXT,
    device_type TEXT,
    manufacturer TEXT,
    parser_type TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    
    CONSTRAINT devices_last_seen_after_first 
        CHECK (last_seen >= first_seen)
);

-- Indexes
CREATE INDEX idx_devices_last_seen 
    ON devices (last_seen DESC);
    
CREATE INDEX idx_devices_manufacturer 
    ON devices (manufacturer) 
    WHERE manufacturer IS NOT NULL;
    
CREATE INDEX idx_devices_device_type 
    ON devices (device_type) 
    WHERE device_type IS NOT NULL;
    
CREATE INDEX idx_devices_parser_type 
    ON devices (parser_type) 
    WHERE parser_type IS NOT NULL;
    
CREATE INDEX idx_devices_blocked 
    ON devices (is_blocked) 
    WHERE is_blocked = TRUE;
    
CREATE INDEX idx_devices_metadata_gin 
    ON devices USING GIN (metadata);
```

#### Column Details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `address` | TEXT | NO | Bluetooth MAC address (primary key) |
| `name` | TEXT | YES | Human-readable device name |
| `device_type` | TEXT | YES | Device category (e.g., "thermometer", "beacon") |
| `manufacturer` | TEXT | YES | Device manufacturer |
| `parser_type` | TEXT | YES | Parser to use for this device's data |
| `metadata` | JSONB | NO | Additional device information |
| `first_seen` | TIMESTAMPTZ | NO | First time device was detected |
| `last_seen` | TIMESTAMPTZ | NO | Most recent detection |
| `is_blocked` | BOOLEAN | NO | Whether to ignore advertisements from this device |

#### Kysely Type Definition

```typescript
export interface Device {
  address: string;
  name: string | null;
  device_type: string | null;
  manufacturer: string | null;
  parser_type: string | null;
  metadata: unknown; // JSONB
  first_seen: Generated<Date>;
  last_seen: Generated<Date>;
  is_blocked: Generated<boolean>;
}

export interface DeviceInsert {
  address: string;
  name?: string | null;
  device_type?: string | null;
  manufacturer?: string | null;
  parser_type?: string | null;
  metadata?: unknown;
  first_seen?: Date;
  last_seen?: Date;
  is_blocked?: boolean;
}

export interface DeviceUpdate {
  name?: string | null;
  device_type?: string | null;
  manufacturer?: string | null;
  parser_type?: string | null;
  metadata?: unknown;
  last_seen?: Date;
  is_blocked?: boolean;
}
```

### 4. `scanners`

Registry of all BLE scanners with health monitoring and location tracking.

#### CREATE TABLE Statement

```sql
CREATE TABLE scanners (
    scanner_id TEXT PRIMARY KEY,
    location TEXT,
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT scanners_status_valid 
        CHECK (status IN ('active', 'inactive', 'error', 'maintenance'))
);

-- Indexes
CREATE INDEX idx_scanners_last_heartbeat 
    ON scanners (last_heartbeat DESC);
    
CREATE INDEX idx_scanners_status 
    ON scanners (status);
    
CREATE INDEX idx_scanners_location 
    ON scanners (location) 
    WHERE location IS NOT NULL;
    
CREATE INDEX idx_scanners_metadata_gin 
    ON scanners USING GIN (metadata);
```

#### Column Details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `scanner_id` | TEXT | NO | Unique scanner identifier (primary key) |
| `location` | TEXT | YES | Physical location description |
| `last_heartbeat` | TIMESTAMPTZ | NO | Last health check timestamp |
| `status` | TEXT | NO | Operational status (enum constraint) |
| `metadata` | JSONB | NO | Additional scanner configuration and info |

#### Kysely Type Definition

```typescript
export type ScannerStatus = 'active' | 'inactive' | 'error' | 'maintenance';

export interface Scanner {
  scanner_id: string;
  location: string | null;
  last_heartbeat: Generated<Date>;
  status: Generated<ScannerStatus>;
  metadata: unknown; // JSONB
}

export interface ScannerInsert {
  scanner_id: string;
  location?: string | null;
  last_heartbeat?: Date;
  status?: ScannerStatus;
  metadata?: unknown;
}

export interface ScannerUpdate {
  location?: string | null;
  last_heartbeat?: Date;
  status?: ScannerStatus;
  metadata?: unknown;
}
```

## Complete Kysely Database Interface

```typescript
import { Kysely, PostgresDialect, Generated } from 'kysely';
import { Pool } from 'pg';

// Interface definitions (from above)
// ... (include all interface definitions)

export interface Database {
  raw_advertisements: RawAdvertisement;
  sensor_readings: SensorReading;
  devices: Device;
  scanners: Scanner;
}

// Create database instance
export function createDatabase(config: {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}): Kysely<Database> {
  const dialect = new PostgresDialect({
    pool: new Pool(config),
  });

  return new Kysely<Database>({ dialect });
}
```

## Schema Rationale and Design Decisions

### 1. UUID Primary Keys

**Decision:** Use UUIDs for `raw_advertisements` and `sensor_readings` tables.

**Rationale:**
- Enables distributed generation without coordination
- Prevents enumeration attacks
- Supports future sharding if needed
- PostgreSQL `gen_random_uuid()` has good performance

### 2. TIMESTAMPTZ for All Timestamps

**Decision:** Use `TIMESTAMPTZ` instead of `TIMESTAMP`.

**Rationale:**
- Stores absolute point in time regardless of server timezone
- Automatically handles daylight saving time
- Critical for distributed systems with scanners in different timezones
- Standard PostgreSQL best practice

### 3. JSONB for Flexible Data

**Decision:** Use JSONB columns for `raw_payload`, `readings`, and `metadata`.

**Rationale:**
- BLE advertisement formats vary significantly by device
- Sensor data structure differs by sensor type
- Allows schema evolution without migrations
- GIN indexes enable fast JSON queries
- JSONB is binary format with better performance than JSON

### 4. Denormalized device_address

**Decision:** Store `device_address` in both `raw_advertisements` and `sensor_readings`.

**Rationale:**
- Optimizes time-series queries (no joins needed)
- Minimal storage overhead (text strings are cheap)
- Improves query performance for device-specific queries
- Follows time-series database best practices

### 5. Foreign Keys with CASCADE DELETE

**Decision:** Use `ON DELETE CASCADE` for foreign keys.

**Rationale:**
- Ensures referential integrity
- Simplifies data retention cleanup
- Automatically removes dependent records
- Prevents orphaned sensor readings

### 6. Partial Indexes

**Decision:** Create partial indexes on filtered columns.

**Rationale:**
- Reduces index size and maintenance cost
- Speeds up specific queries (e.g., blocked devices)
- Only indexes relevant rows
- Example: `WHERE is_blocked = TRUE` only indexes blocked devices

### 7. Composite Indexes for Time-Series

**Decision:** Create composite indexes with `(entity, timestamp DESC)`.

**Rationale:**
- Optimizes common query patterns
- Supports efficient range scans
- DESC ordering optimizes recent data queries
- Covers multiple query variations

## Migration Strategy

### Using Kysely Migrations

See [ADR-0008](decisions/0008-kysely-migrations.md) for the decision to use Kysely for type-safe migrations.

### Migration File Structure

```
src/
└── database/
    └── migrations/
        ├── 001_create_scanners.ts
        ├── 002_create_raw_advertisements.ts
        ├── 003_create_devices.ts
        ├── 004_create_sensor_readings.ts
        └── 005_create_indexes.ts
```

### Example Migration: Create Scanners Table

```typescript
// src/database/migrations/001_create_scanners.ts
import { Kysely, sql } from 'kysely';

export async function up(db: Kysely<any>): Promise<void> {
  await db.schema
    .createTable('scanners')
    .addColumn('scanner_id', 'text', (col) => col.primaryKey())
    .addColumn('location', 'text')
    .addColumn('last_heartbeat', 'timestamptz', (col) =>
      col.notNull().defaultTo(sql`NOW()`)
    )
    .addColumn('status', 'text', (col) =>
      col.notNull().defaultTo('active').check(
        sql`status IN ('active', 'inactive', 'error', 'maintenance')`
      )
    )
    .addColumn('metadata', 'jsonb', (col) =>
      col.notNull().defaultTo(sql`'{}'::jsonb`)
    )
    .execute();

  // Create indexes
  await db.schema
    .createIndex('idx_scanners_last_heartbeat')
    .on('scanners')
    .column('last_heartbeat')
    .execute();

  await db.schema
    .createIndex('idx_scanners_status')
    .on('scanners')
    .column('status')
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('scanners').execute();
}
```

### Example Migration: Create Raw Advertisements Table

```typescript
// src/database/migrations/002_create_raw_advertisements.ts
import { Kysely, sql } from 'kysely';

export async function up(db: Kysely<any>): Promise<void> {
  await db.schema
    .createTable('raw_advertisements')
    .addColumn('id', 'uuid', (col) =>
      col.primaryKey().defaultTo(sql`gen_random_uuid()`)
    )
    .addColumn('received_at', 'timestamptz', (col) =>
      col.notNull().defaultTo(sql`NOW()`)
    )
    .addColumn('scanner_id', 'text', (col) =>
      col.notNull().references('scanners.scanner_id').onDelete('cascade')
    )
    .addColumn('device_address', 'text', (col) => col.notNull())
    .addColumn('device_name', 'text')
    .addColumn('rssi', 'smallint', (col) =>
      col.notNull().check(sql`rssi >= -128 AND rssi <= 0`)
    )
    .addColumn('raw_payload', 'jsonb', (col) => col.notNull())
    .execute();

  // Create indexes
  await db.schema
    .createIndex('idx_raw_adv_received_at')
    .on('raw_advertisements')
    .column('received_at')
    .execute();

  await db.schema
    .createIndex('idx_raw_adv_device_address')
    .on('raw_advertisements')
    .columns(['device_address', 'received_at'])
    .execute();

  await db.schema
    .createIndex('idx_raw_adv_scanner_id')
    .on('raw_advertisements')
    .columns(['scanner_id', 'received_at'])
    .execute();

  // GIN index for JSONB
  await sql`CREATE INDEX idx_raw_adv_payload_gin 
    ON raw_advertisements USING GIN (raw_payload)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('raw_advertisements').execute();
}
```

### Running Migrations

```typescript
// src/database/migrator.ts
import { Kysely, Migrator, FileMigrationProvider } from 'kysely';
import { promises as fs } from 'fs';
import path from 'path';

export async function migrateToLatest(db: Kysely<any>) {
  const migrator = new Migrator({
    db,
    provider: new FileMigrationProvider({
      fs,
      path,
      migrationFolder: path.join(__dirname, 'migrations'),
    }),
  });

  const { error, results } = await migrator.migrateToLatest();

  results?.forEach((result) => {
    if (result.status === 'Success') {
      console.log(`Migration "${result.migrationName}" executed successfully`);
    } else if (result.status === 'Error') {
      console.error(`Failed to execute migration "${result.migrationName}"`);
    }
  });

  if (error) {
    console.error('Failed to migrate:', error);
    process.exit(1);
  }
}
```

## Query Patterns and Examples

### Pattern 1: Insert Raw Advertisement

```typescript
async function insertAdvertisement(
  db: Kysely<Database>,
  data: {
    scanner_id: string;
    device_address: string;
    device_name?: string;
    rssi: number;
    raw_payload: unknown;
  }
): Promise<string> {
  const result = await db
    .insertInto('raw_advertisements')
    .values({
      scanner_id: data.scanner_id,
      device_address: data.device_address,
      device_name: data.device_name ?? null,
      rssi: data.rssi,
      raw_payload: data.raw_payload,
    })
    .returning('id')
    .executeTakeFirstOrThrow();

  return result.id;
}
```

### Pattern 2: Query Recent Advertisements for Device

```typescript
async function getRecentAdvertisements(
  db: Kysely<Database>,
  deviceAddress: string,
  hoursBack: number = 24
): Promise<RawAdvertisement[]> {
  const cutoff = new Date(Date.now() - hoursBack * 60 * 60 * 1000);

  return db
    .selectFrom('raw_advertisements')
    .selectAll()
    .where('device_address', '=', deviceAddress)
    .where('received_at', '>=', cutoff)
    .orderBy('received_at', 'desc')
    .limit(1000)
    .execute();
}
```

### Pattern 3: Insert Sensor Reading with Device Update

```typescript
async function insertSensorReading(
  db: Kysely<Database>,
  reading: {
    timestamp: Date;
    device_address: string;
    sensor_type: SensorType;
    readings: unknown;
    raw_advertisement_id: string;
  }
): Promise<void> {
  await db.transaction().execute(async (trx) => {
    // Insert sensor reading
    await trx
      .insertInto('sensor_readings')
      .values(reading)
      .execute();

    // Update device last_seen
    await trx
      .insertInto('devices')
      .values({
        address: reading.device_address,
        last_seen: reading.timestamp,
      })
      .onConflict((oc) =>
        oc.column('address').doUpdateSet({
          last_seen: reading.timestamp,
        })
      )
      .execute();
  });
}
```

### Pattern 4: Query Sensor Readings Time Series

```typescript
async function getSensorTimeSeries(
  db: Kysely<Database>,
  deviceAddress: string,
  sensorType: SensorType,
  startTime: Date,
  endTime: Date
): Promise<Array<{ timestamp: Date; readings: unknown }>> {
  return db
    .selectFrom('sensor_readings')
    .select(['timestamp', 'readings'])
    .where('device_address', '=', deviceAddress)
    .where('sensor_type', '=', sensorType)
    .where('timestamp', '>=', startTime)
    .where('timestamp', '<=', endTime)
    .orderBy('timestamp', 'asc')
    .execute();
}
```

### Pattern 5: Query Latest Reading Per Sensor Type

```typescript
async function getLatestReadings(
  db: Kysely<Database>,
  deviceAddress: string
): Promise<Array<SensorReading>> {
  // Using DISTINCT ON (PostgreSQL-specific)
  return db
    .selectFrom('sensor_readings')
    .selectAll()
    .where('device_address', '=', deviceAddress)
    .distinctOn('sensor_type')
    .orderBy('sensor_type')
    .orderBy('timestamp', 'desc')
    .execute();
}
```

### Pattern 6: Query JSONB Fields

```typescript
async function findDevicesWithFirmwareVersion(
  db: Kysely<Database>,
  version: string
): Promise<Device[]> {
  return db
    .selectFrom('devices')
    .selectAll()
    .where(
      sql`metadata->>'firmware_version'`,
      '=',
      version
    )
    .execute();
}

async function queryByServiceUUID(
  db: Kysely<Database>,
  serviceUuid: string
): Promise<RawAdvertisement[]> {
  return db
    .selectFrom('raw_advertisements')
    .selectAll()
    .where(
      sql`raw_payload->'serviceUuids' @> ${JSON.stringify([serviceUuid])}::jsonb`
    )
    .execute();
}
```

### Pattern 7: Update Device Registry

```typescript
async function upsertDevice(
  db: Kysely<Database>,
  device: DeviceInsert
): Promise<void> {
  await db
    .insertInto('devices')
    .values(device)
    .onConflict((oc) =>
      oc.column('address').doUpdateSet({
        name: device.name,
        device_type: device.device_type,
        manufacturer: device.manufacturer,
        parser_type: device.parser_type,
        metadata: device.metadata,
        last_seen: device.last_seen ?? new Date(),
      })
    )
    .execute();
}
```

### Pattern 8: Scanner Health Check

```typescript
async function updateScannerHeartbeat(
  db: Kysely<Database>,
  scannerId: string,
  status: ScannerStatus = 'active'
): Promise<void> {
  await db
    .updateTable('scanners')
    .set({
      last_heartbeat: new Date(),
      status,
    })
    .where('scanner_id', '=', scannerId)
    .execute();
}

async function getInactiveScanners(
  db: Kysely<Database>,
  minutesThreshold: number = 5
): Promise<Scanner[]> {
  const cutoff = new Date(Date.now() - minutesThreshold * 60 * 1000);

  return db
    .selectFrom('scanners')
    .selectAll()
    .where('last_heartbeat', '<', cutoff)
    .where('status', '=', 'active')
    .execute();
}
```

### Pattern 9: Block/Unblock Devices

```typescript
async function blockDevice(
  db: Kysely<Database>,
  deviceAddress: string
): Promise<void> {
  await db
    .updateTable('devices')
    .set({ is_blocked: true })
    .where('address', '=', deviceAddress)
    .execute();
}

async function getBlockedDevices(
  db: Kysely<Database>
): Promise<Device[]> {
  return db
    .selectFrom('devices')
    .selectAll()
    .where('is_blocked', '=', true)
    .execute();
}
```

### Pattern 10: Aggregate Queries

```typescript
async function getAdvertisementStats(
  db: Kysely<Database>,
  startTime: Date,
  endTime: Date
): Promise<{
  total: number;
  by_scanner: Array<{ scanner_id: string; count: number }>;
  by_device: Array<{ device_address: string; count: number }>;
}> {
  const total = await db
    .selectFrom('raw_advertisements')
    .select(sql<number>`count(*)::int`.as('count'))
    .where('received_at', '>=', startTime)
    .where('received_at', '<=', endTime)
    .executeTakeFirstOrThrow();

  const by_scanner = await db
    .selectFrom('raw_advertisements')
    .select(['scanner_id', sql<number>`count(*)::int`.as('count')])
    .where('received_at', '>=', startTime)
    .where('received_at', '<=', endTime)
    .groupBy('scanner_id')
    .orderBy('count', 'desc')
    .execute();

  const by_device = await db
    .selectFrom('raw_advertisements')
    .select(['device_address', sql<number>`count(*)::int`.as('count')])
    .where('received_at', '>=', startTime)
    .where('received_at', '<=', endTime)
    .groupBy('device_address')
    .orderBy('count', 'desc')
    .limit(100)
    .execute();

  return {
    total: total.count,
    by_scanner,
    by_device,
  };
}
```

## Data Retention Policies

### Overview

Time-series data grows continuously and requires retention policies to manage storage costs and maintain performance.

### Recommended Retention Periods

| Table | Retention Period | Rationale |
|-------|------------------|-----------|
| `raw_advertisements` | 7-30 days | Debug and reprocessing buffer |
| `sensor_readings` | 365 days (1 year) | Historical analysis and trends |
| `devices` | Indefinite | Small table, useful registry |
| `scanners` | Indefinite | Small table, configuration data |

### Implementation Strategies

#### Strategy 1: Scheduled Deletion (Simple)

```typescript
async function cleanupOldData(
  db: Kysely<Database>,
  retentionDays: { raw_advertisements: number; sensor_readings: number }
): Promise<{ raw_ads_deleted: number; readings_deleted: number }> {
  const rawAdCutoff = new Date(
    Date.now() - retentionDays.raw_advertisements * 24 * 60 * 60 * 1000
  );
  const readingsCutoff = new Date(
    Date.now() - retentionDays.sensor_readings * 24 * 60 * 60 * 1000
  );

  const rawAdsResult = await db
    .deleteFrom('raw_advertisements')
    .where('received_at', '<', rawAdCutoff)
    .execute();

  const readingsResult = await db
    .deleteFrom('sensor_readings')
    .where('timestamp', '<', readingsCutoff)
    .execute();

  return {
    raw_ads_deleted: Number(rawAdsResult.numDeletedRows),
    readings_deleted: Number(readingsResult.numDeletedRows),
  };
}
```

Run this function daily via cron job or scheduler.

#### Strategy 2: PostgreSQL Partitioning (Advanced)

For high-volume systems, use table partitioning by time range:

```sql
-- Convert to partitioned table
CREATE TABLE raw_advertisements_partitioned (
    LIKE raw_advertisements INCLUDING ALL
) PARTITION BY RANGE (received_at);

-- Create monthly partitions
CREATE TABLE raw_advertisements_2026_01 
    PARTITION OF raw_advertisements_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE raw_advertisements_2026_02 
    PARTITION OF raw_advertisements_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

Drop old partitions instead of DELETE:

```sql
-- Much faster than DELETE
DROP TABLE raw_advertisements_2025_12;
```

#### Strategy 3: TimescaleDB (Production Scale)

For production deployments with high write volumes, consider [TimescaleDB](https://www.timescale.com/):

```sql
-- Convert to hypertable
SELECT create_hypertable('raw_advertisements', 'received_at');

-- Automatic retention policy
SELECT add_retention_policy('raw_advertisements', INTERVAL '30 days');
```

### Configuration

```typescript
// src/config/retention.ts
export const RETENTION_POLICIES = {
  raw_advertisements: {
    days: parseInt(process.env.RETENTION_RAW_ADS_DAYS ?? '30'),
    enabled: process.env.RETENTION_ENABLED !== 'false',
  },
  sensor_readings: {
    days: parseInt(process.env.RETENTION_READINGS_DAYS ?? '365'),
    enabled: process.env.RETENTION_ENABLED !== 'false',
  },
};
```

### Monitoring

Track deletion metrics to ensure retention is working:

```typescript
interface RetentionMetrics {
  table: string;
  deleted_rows: number;
  execution_time_ms: number;
  oldest_remaining: Date;
  timestamp: Date;
}

async function trackRetentionRun(
  db: Kysely<Database>,
  metrics: RetentionMetrics
): Promise<void> {
  // Store in monitoring system or metrics table
  console.log('Retention run completed:', metrics);
}
```

## Performance Considerations

### Index Maintenance

PostgreSQL indexes require maintenance:

```sql
-- Reindex monthly for optimal performance
REINDEX TABLE raw_advertisements;
REINDEX TABLE sensor_readings;

-- Or use VACUUM ANALYZE after large deletions
VACUUM ANALYZE raw_advertisements;
VACUUM ANALYZE sensor_readings;
```

### Connection Pooling

Configure pg pool appropriately:

```typescript
const pool = new Pool({
  host: config.host,
  port: config.port,
  database: config.database,
  user: config.user,
  password: config.password,
  max: 20, // Maximum pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

### Query Optimization Tips

1. **Use EXPLAIN ANALYZE**: Understand query plans
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM sensor_readings
   WHERE device_address = 'AA:BB:CC:DD:EE:FF'
   AND timestamp > NOW() - INTERVAL '1 day';
   ```

2. **Limit result sets**: Always use LIMIT for large queries

3. **Use prepared statements**: Kysely handles this automatically

4. **Batch inserts**: Insert multiple rows in single query
   ```typescript
   await db
     .insertInto('raw_advertisements')
     .values([ad1, ad2, ad3, ...])
     .execute();
   ```

5. **Use transactions**: Group related operations
   ```typescript
   await db.transaction().execute(async (trx) => {
     // Multiple operations
   });
   ```

## Backup and Recovery

### Backup Strategy

```bash
# Full database backup
pg_dump -h localhost -U user -d bt_mqtt > backup.sql

# Backup with compression
pg_dump -h localhost -U user -d bt_mqtt | gzip > backup.sql.gz

# Table-specific backup
pg_dump -h localhost -U user -d bt_mqtt -t devices > devices_backup.sql
```

### Restore

```bash
# Restore full database
psql -h localhost -U user -d bt_mqtt < backup.sql

# Restore from compressed
gunzip -c backup.sql.gz | psql -h localhost -U user -d bt_mqtt
```

### Continuous Archiving

Configure PostgreSQL WAL archiving for point-in-time recovery (see PostgreSQL documentation).

## Related Documentation

- [Architecture Overview](architecture.md)
- [MQTT Schema](mqtt-schema.md)
- [ADR-0008: Kysely Migrations](decisions/0008-kysely-migrations.md)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Kysely Documentation](https://kysely.dev/)

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-11 | 1.0.0 | Initial schema documentation |
