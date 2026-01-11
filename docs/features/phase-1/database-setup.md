# Feature: Database Setup

**Status:** In Progress  
**Milestone:** Phase 1 - Foundation  
**Owner:** TBD  
**Related ADRs:** [ADR-0008: Kysely Migrations](../../decisions/0008-kysely-migrations.md)

---

## Overview

Database Setup establishes the foundational data persistence layer for the BT-MQTT system. It provides a type-safe, version-controlled database schema management system using Kysely migrations, ensuring consistent database state across development, testing, and production environments.

### Motivation

A robust database migration system is critical for:
- Tracking schema changes over time
- Safely deploying schema updates to production
- Enabling team collaboration without conflicts
- Providing rollback capability for failed migrations
- Maintaining type safety between application and database

### Goals

- Implement Kysely-based migration system
- Create initial database schema
- Provide type-safe database client configuration
- Support multiple environments (dev, test, prod)
- Enable CI/CD integration for automated migrations
- Document schema evolution strategy

### Non-Goals

- Database clustering or replication setup
- Performance tuning (covered in Phase 3)
- Backup and recovery procedures (operations concern)
- Data seeding or fixtures (test concern)

---

## Requirements

### Functional Requirements

1. **FR-1**: Initialize PostgreSQL database with required extensions
2. **FR-2**: Create and apply migrations using Kysely
3. **FR-3**: Support migration rollback (down migrations)
4. **FR-4**: Generate TypeScript types from database schema
5. **FR-5**: Provide database connection pooling configuration
6. **FR-6**: Support environment-specific database configuration
7. **FR-7**: Track migration history in database
8. **FR-8**: Validate migrations before applying
9. **FR-9**: Provide CLI commands for migration operations
10. **FR-10**: Document schema changes in migrations

### Non-Functional Requirements

1. **NFR-1**: **Type Safety**: 100% type coverage for database operations
2. **NFR-2**: **Reliability**: Migrations must be idempotent where possible
3. **NFR-3**: **Performance**: Migrations execute in <30 seconds
4. **NFR-4**: **Maintainability**: Clear migration naming and documentation
5. **NFR-5**: **Testability**: Migrations testable in isolated environments
6. **NFR-6**: **Security**: No credentials in migration files
7. **NFR-7**: **Automation**: Support CI/CD pipeline integration

---

## Dependencies

### Prerequisites

- PostgreSQL 16+ server
- Node.js 20+ runtime
- TypeScript 5.0+
- Kysely library
- pg (PostgreSQL client library)

### Blocked By

- None (first database component)

### Blocks

- Raw Storage (requires migrations)
- MQTT Subscriber (requires database connection)
- All data persistence features

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────┐
│       Database Setup                     │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   Migration System                 │ │
│  │                                    │ │
│  │  - Migration files                 │ │
│  │  - Migration runner                │ │
│  │  - Migration history               │ │
│  └────────────────────────────────────┘ │
│                │                         │
│                ▼                         │
│  ┌────────────────────────────────────┐ │
│  │   Kysely Client                    │ │
│  │                                    │ │
│  │  - Type-safe query builder         │ │
│  │  - Connection pool                 │ │
│  │  - Schema introspection            │ │
│  └────────────────────────────────────┘ │
│                │                         │
│                ▼                         │
│        [PostgreSQL 16]                   │
└─────────────────────────────────────────┘
```

### Directory Structure

```
packages/subscriber/
├── src/
│   ├── db/
│   │   ├── migrations/
│   │   │   ├── 001_initial_schema.ts
│   │   │   ├── 002_add_indexes.ts
│   │   │   └── ...
│   │   ├── types.ts          # Generated types
│   │   ├── client.ts         # Database client
│   │   └── migrator.ts       # Migration runner
│   └── ...
├── scripts/
│   ├── migrate-latest.ts     # Apply pending migrations
│   ├── migrate-up.ts         # Apply one migration
│   ├── migrate-down.ts       # Rollback one migration
│   └── generate-types.ts     # Generate TypeScript types
└── ...
```

### Migration File Structure

```typescript
// src/db/migrations/001_initial_schema.ts
import { Kysely, sql } from 'kysely';

export async function up(db: Kysely<any>): Promise<void> {
  // Create raw_messages table
  await db.schema
    .createTable('raw_messages')
    .addColumn('id', 'bigserial', (col) => col.primaryKey())
    .addColumn('scanner_id', 'varchar(255)', (col) => col.notNull())
    .addColumn('mac_address', 'varchar(17)', (col) => col.notNull())
    .addColumn('rssi', 'integer', (col) => col.notNull())
    .addColumn('timestamp', 'timestamptz', (col) => col.notNull())
    .addColumn('received_at', 'timestamptz', (col) => 
      col.notNull().defaultTo(sql`NOW()`)
    )
    .addColumn('manufacturer_data', 'jsonb')
    .addColumn('service_uuids', sql`text[]`)
    .addColumn('local_name', 'varchar(255)')
    .addColumn('raw_payload', 'jsonb', (col) => col.notNull())
    .execute();

  // Add constraints
  await db.schema
    .alterTable('raw_messages')
    .addCheckConstraint('rssi_range', sql`rssi BETWEEN -128 AND 0`)
    .execute();

  await db.schema
    .alterTable('raw_messages')
    .addCheckConstraint(
      'valid_mac', 
      sql`mac_address ~ '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'`
    )
    .execute();

  // Create indexes
  await db.schema
    .createIndex('idx_raw_messages_mac')
    .on('raw_messages')
    .column('mac_address')
    .execute();

  await db.schema
    .createIndex('idx_raw_messages_timestamp')
    .on('raw_messages')
    .column('timestamp')
    .execute();

  await db.schema
    .createIndex('idx_raw_messages_scanner')
    .on('raw_messages')
    .column('scanner_id')
    .execute();

  await db.schema
    .createIndex('idx_raw_messages_received')
    .on('raw_messages')
    .column('received_at')
    .execute();

  // Composite index
  await db.schema
    .createIndex('idx_raw_messages_mac_time')
    .on('raw_messages')
    .columns(['mac_address', 'timestamp'])
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('raw_messages').execute();
}
```

### Database Client Configuration

```typescript
// src/db/client.ts
import { Kysely, PostgresDialect } from 'kysely';
import { Pool } from 'pg';
import type { Database } from './types';

export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  pool?: {
    min?: number;
    max?: number;
    idleTimeoutMillis?: number;
  };
}

export function createDatabaseClient(config: DatabaseConfig): Kysely<Database> {
  const pool = new Pool({
    host: config.host,
    port: config.port,
    database: config.database,
    user: config.user,
    password: config.password,
    min: config.pool?.min ?? 2,
    max: config.pool?.max ?? 10,
    idleTimeoutMillis: config.pool?.idleTimeoutMillis ?? 30000,
  });

  const dialect = new PostgresDialect({ pool });

  return new Kysely<Database>({ dialect });
}
```

### Migration Runner

```typescript
// src/db/migrator.ts
import { Kysely, Migrator, FileMigrationProvider } from 'kysely';
import { promises as fs } from 'fs';
import path from 'path';

export async function migrateToLatest(db: Kysely<any>): Promise<void> {
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
      console.log(`Migration "${result.migrationName}" was executed successfully`);
    } else if (result.status === 'Error') {
      console.error(`Migration "${result.migrationName}" failed`);
    }
  });

  if (error) {
    console.error('Failed to migrate:', error);
    throw error;
  }
}

export async function migrateDown(db: Kysely<any>): Promise<void> {
  const migrator = new Migrator({
    db,
    provider: new FileMigrationProvider({
      fs,
      path,
      migrationFolder: path.join(__dirname, 'migrations'),
    }),
  });

  const { error, results } = await migrator.migrateDown();

  if (error) {
    console.error('Failed to rollback:', error);
    throw error;
  }

  results?.forEach((result) => {
    console.log(`Rolled back migration "${result.migrationName}"`);
  });
}
```

### Type Generation

```typescript
// scripts/generate-types.ts
import { createDatabaseClient } from '../src/db/client';
import { Kysely } from 'kysely';
import { PostgresIntrospector } from 'kysely';
import { promises as fs } from 'fs';

async function generateTypes() {
  const db = createDatabaseClient({
    host: process.env.DB_HOST ?? 'localhost',
    port: parseInt(process.env.DB_PORT ?? '5432'),
    database: process.env.DB_NAME ?? 'btmqtt',
    user: process.env.DB_USER ?? 'btmqtt',
    password: process.env.DB_PASSWORD ?? 'password',
  });

  // Use kysely-codegen or similar tool
  // This is a placeholder - actual implementation uses kysely-codegen
  console.log('Generating types from database schema...');
  
  // Close connection
  await db.destroy();
}

generateTypes().catch(console.error);
```

### Configuration

```yaml
# config/database.yml
development:
  host: localhost
  port: 5432
  database: btmqtt_dev
  user: btmqtt
  password: password
  pool:
    min: 2
    max: 10
    idle_timeout: 30000

test:
  host: localhost
  port: 5432
  database: btmqtt_test
  user: btmqtt
  password: password
  pool:
    min: 1
    max: 5

production:
  host: ${DB_HOST}
  port: ${DB_PORT}
  database: ${DB_NAME}
  user: ${DB_USER}
  password: ${DB_PASSWORD}
  pool:
    min: 5
    max: 20
    idle_timeout: 60000
```

### CLI Commands

```bash
# Apply all pending migrations
npm run migrate:latest

# Rollback last migration
npm run migrate:down

# Generate TypeScript types from schema
npm run db:generate-types

# Create new migration
npm run migrate:create <name>
```

### Migration Tracking

Kysely automatically creates a migration tracking table:

```sql
CREATE TABLE kysely_migration (
  name VARCHAR(255) PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Testing Strategy

### Unit Tests

- [ ] Test migration file loading
- [ ] Test database client initialization
- [ ] Test connection pool configuration
- [ ] Test configuration parsing

### Integration Tests

- [ ] Test migration up execution
- [ ] Test migration down execution
- [ ] Test migration rollback
- [ ] Test idempotent migrations
- [ ] Test migration order
- [ ] Test type generation

### Migration Tests

- [ ] Apply migrations to clean database
- [ ] Verify table structure matches expectations
- [ ] Verify indexes are created
- [ ] Verify constraints are applied
- [ ] Test rollback restores previous state
- [ ] Test migration re-run (should be no-op)

### Manual Tests

- [ ] Test on development database
- [ ] Test on test database
- [ ] Test migration in Docker container
- [ ] Verify generated types match schema
- [ ] Test connection pooling under load

---

## Open Questions

1. **Q**: Should we use kysely-codegen or write custom type generator?
   - **A**: Use kysely-codegen - battle-tested and well-maintained

2. **Q**: Should migrations run automatically on startup?
   - **A**: No - require explicit migration command for safety

3. **Q**: How to handle migration failures in production?
   - **A**: Manual intervention required, document recovery procedures

4. **Q**: Should we version-control generated types?
   - **A**: Yes - commit types to ensure build reproducibility

5. **Q**: Should we support migration branching?
   - **A**: Not in Phase 1 - linear migration history only

---

## Implementation Checklist

### Setup
- [ ] Install Kysely and dependencies
- [ ] Install kysely-codegen for type generation
- [ ] Create database directory structure
- [ ] Configure TypeScript for database code

### Migration System
- [ ] Implement migration runner
- [ ] Create migration file template
- [ ] Implement up/down migration commands
- [ ] Add migration status command
- [ ] Create migration creation script

### Database Client
- [ ] Implement database client factory
- [ ] Configure connection pooling
- [ ] Add environment-specific configuration
- [ ] Implement graceful connection shutdown
- [ ] Add connection health check

### Initial Schema
- [ ] Create initial migration (raw_messages table)
- [ ] Add indexes migration
- [ ] Add constraints migration
- [ ] Test migrations on clean database
- [ ] Generate initial TypeScript types

### CLI Scripts
- [ ] Create migrate:latest script
- [ ] Create migrate:down script
- [ ] Create migrate:status script
- [ ] Create db:generate-types script
- [ ] Add scripts to package.json

### Documentation
- [ ] Document migration workflow
- [ ] Document how to create new migrations
- [ ] Document rollback procedure
- [ ] Document type generation process
- [ ] Create troubleshooting guide

### Testing
- [ ] Write migration runner tests
- [ ] Write migration validation tests
- [ ] Test rollback functionality
- [ ] Test type generation
- [ ] Test in CI environment

---

## Acceptance Criteria

- [ ] Kysely migrations system installed and configured
- [ ] Initial migration creates raw_messages table successfully
- [ ] Migration rollback works correctly
- [ ] TypeScript types generated from schema
- [ ] Database client provides type-safe queries
- [ ] Connection pooling configured correctly
- [ ] CLI commands work for all migration operations
- [ ] Migrations tested in development environment
- [ ] Migration tracking table created automatically
- [ ] Documentation complete and accurate
- [ ] CI/CD integration tested

---

## Related Features

- [Raw Storage](raw-storage.md) - Primary table created by migrations
- [MQTT Subscriber](mqtt-subscriber.md) - Uses database client
- [Device Registry](../phase-2/device-registry.md) - Future tables
- [Parser System](../phase-2/parser-system.md) - Future tables

---

## References

- [Kysely Documentation](https://kysely.dev/)
- [Kysely Migrations Guide](https://kysely.dev/docs/migrations)
- [kysely-codegen](https://github.com/RobinBlomberg/kysely-codegen)
- [PostgreSQL 16 Documentation](https://www.postgresql.org/docs/16/)
- [ADR-0008: Kysely Migrations](../../decisions/0008-kysely-migrations.md)
- [Database Schema Documentation](../../database-schema.md)
