# Subscriber Service

MQTT subscriber that processes BLE advertisements and stores data in PostgreSQL.

## Overview

The subscriber service is a TypeScript/Node.js application that:
- Subscribes to MQTT topics for raw BLE advertisements
- Archives complete raw data in PostgreSQL
- Routes messages to appropriate parsers
- Extracts and stores sensor readings
- Maintains device registry

## Features

- **MQTT Subscription**: Subscribe to `bt-mqtt/raw/#`
- **Raw Archival**: Complete data preservation
- **Parser System**: Pluggable architecture for device types
- **Type-Safe Database**: Kysely for PostgreSQL
- **Error Handling**: Comprehensive error handling and retries
- **Logging**: Structured JSON logging

## Quick Start

### Prerequisites

- Node.js 20+
- PostgreSQL 16+
- MQTT broker accessible on network

### Installation

```bash
cd subscriber

# Install dependencies
npm install

# Copy and edit configuration
cp config/subscriber.example.yaml config/subscriber.yaml
# Edit config/subscriber.yaml with your settings

# Set database password
export DB_PASSWORD=btmqtt_dev

# Run migrations
npm run migrate:latest

# Start subscriber
npm run dev
```

### Configuration

Edit `config/subscriber.yaml`:

```yaml
mqtt:
  broker: mqtt.shypan.st
  port: 1883
  topic: bt-mqtt/raw/#
  qos: 1
  client_id: subscriber-main

database:
  host: localhost
  port: 5432
  database: bt_mqtt
  user: btmqtt
  password: ${DB_PASSWORD}  # From environment variable

parsers:
  environmental:
    enabled: true
  beacon:
    enabled: false

storage:
  raw_retention_days: 90
  batch_size: 100
  batch_flush_ms: 5000

logging:
  level: info
  format: json
```

## Database Setup

### Using devenv (local development)

```bash
# Start PostgreSQL service
devenv up

# Run migrations
npm run migrate:latest
```

### Using Docker Compose

```bash
# Start PostgreSQL
docker compose up -d postgres

# Run migrations
npm run migrate:latest
```

### Manual PostgreSQL setup

```bash
# Create database and user
createdb bt_mqtt
createuser btmqtt
psql -c "GRANT ALL PRIVILEGES ON DATABASE bt_mqtt TO btmqtt"

# Run migrations
npm run migrate:latest
```

## Development

```bash
# Install dependencies
npm install

# Run in development mode (with watch)
npm run dev

# Build TypeScript
npm run build

# Run production build
npm start

# Run tests
npm test

# Run migrations
npm run migrate:latest
npm run migrate:down
npm run migrate:list

# Type checking
npm run type-check

# Linting
npm run lint
```

## Project Structure

```
subscriber/
├── src/
│   ├── index.ts                 # Application entry point
│   ├── config.ts                # Configuration management
│   ├── mqtt/
│   │   ├── subscriber.ts        # MQTT subscription logic
│   │   └── message-handler.ts  # Message processing
│   ├── database/
│   │   ├── client.ts            # Kysely database client
│   │   ├── schema.ts            # TypeScript type definitions
│   │   ├── migrations/          # Database migrations
│   │   └── repositories/        # Data access layer
│   ├── parsers/
│   │   ├── parser-registry.ts   # Parser plugin system
│   │   ├── base-parser.ts       # Parser interface
│   │   └── environmental-parser.ts  # Example parser
│   └── storage/
│       ├── raw-storage.ts       # Archive raw messages
│       └── sensor-storage.ts    # Store parsed readings
├── config/
│   └── subscriber.example.yaml
├── tests/
├── package.json
├── tsconfig.json
└── README.md
```

## Adding a New Parser

```typescript
// src/parsers/my-parser.ts
import { BaseParser } from './base-parser';
import { RawAdvertisement, SensorReading } from '../database/schema';

export class MyParser extends BaseParser {
  canParse(advertisement: RawAdvertisement): boolean {
    // Check if this parser can handle the advertisement
    return advertisement.manufacturer_data?.['0x1234'] !== undefined;
  }

  async parse(advertisement: RawAdvertisement): Promise<SensorReading | null> {
    // Extract sensor data
    const data = this.decodeManufacturerData(advertisement);
    
    return {
      device_address: advertisement.device_address,
      sensor_type: 'my_sensor',
      timestamp: advertisement.received_at,
      readings: {
        value1: data.value1,
        value2: data.value2,
      },
      raw_advertisement_id: advertisement.id,
    };
  }
}

// Register in src/parsers/parser-registry.ts
import { MyParser } from './my-parser';

const registry = new ParserRegistry();
registry.register('my_sensor', new MyParser());
```

## Docker Deployment

```bash
# Build image
docker build -f ../docker/subscriber.Dockerfile -t bt-mqtt-subscriber .

# Run with Docker Compose
docker compose up -d subscriber
```

## Monitoring

### Logs

```bash
# View logs (development)
npm run dev

# View logs (Docker)
docker compose logs -f subscriber

# View logs (systemd - if deployed as service)
journalctl -u bt-mqtt-subscriber -f
```

### Database Queries

```sql
-- Check raw advertisement count
SELECT COUNT(*) FROM raw_advertisements;

-- Recent advertisements
SELECT * FROM raw_advertisements 
ORDER BY received_at DESC 
LIMIT 10;

-- Devices seen
SELECT DISTINCT device_address, device_name 
FROM raw_advertisements;

-- Sensor readings
SELECT * FROM sensor_readings 
ORDER BY timestamp DESC 
LIMIT 10;
```

## Troubleshooting

### MQTT connection issues

```bash
# Test MQTT subscription
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/raw/#' -v
```

### Database connection issues

```bash
# Test PostgreSQL connection
psql -h localhost -U btmqtt -d bt_mqtt

# Check if migrations ran
npm run migrate:list
```

### Parser not processing messages

1. Check logs for parser errors
2. Verify parser is registered in `parser-registry.ts`
3. Check `canParse()` logic matches advertisement format
4. Enable debug logging: `LOG_LEVEL=debug npm run dev`

## Documentation

- [Architecture](../docs/architecture.md)
- [Database Schema](../docs/database-schema.md)
- [Subscriber Design](../docs/subscriber.md)
- [Feature: MQTT Subscriber](../docs/features/phase-1/mqtt-subscriber.md)
- [Feature: Parser System](../docs/features/phase-2/parser-system.md)

## Related ADRs

- [ADR-0002: TypeScript Subscriber](../docs/decisions/0002-typescript-subscriber.md)
- [ADR-0004: Processing Pipeline](../docs/decisions/0004-processing-pipeline.md)
- [ADR-0006: Parser Plugin System](../docs/decisions/0006-parser-plugin-system.md)
- [ADR-0008: Kysely Migrations](../docs/decisions/0008-kysely-migrations.md)
- [ADR-0010: Parser Registration](../docs/decisions/0010-parser-manual-registration.md)
