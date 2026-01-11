# 0008. Kysely for Type-Safe Queries and Migrations

**Date:** 2026-01-11

**Status:** Accepted

## Context

The subscriber component needs to store parsed BLE advertisement data in PostgreSQL. Requirements:

- Type-safe database operations to prevent runtime errors
- Database migrations for schema evolution
- Good developer experience with autocomplete and compile-time checking
- Support for complex queries (joins, aggregations, filtering)
- Integration with TypeScript for end-to-end type safety
- Good performance for high-volume inserts

We need to choose a database library/ORM that balances type safety, performance, and developer experience.

## Decision

Use **Kysely** for type-safe database queries and migrations.

Kysely is a type-safe SQL query builder for TypeScript that:
- Provides end-to-end type safety from database schema to application code
- Uses TypeScript's type system rather than code generation
- Supports migrations with up/down functions
- Allows raw SQL when needed
- Has minimal runtime overhead

Setup:
```typescript
// Database interface generated from schema
interface Database {
  advertisements: AdvertisementTable;
  parsed_readings: ParsedReadingTable;
}

// Kysely instance
const db = new Kysely<Database>({
  dialect: new PostgresDialect({ pool })
});

// Type-safe queries
const readings = await db
  .selectFrom('parsed_readings')
  .where('device_mac', '=', mac)
  .where('timestamp', '>', startTime)
  .selectAll()
  .execute();
```

Migrations managed via Kysely's migration system:
```typescript
export async function up(db: Kysely<any>): Promise<void> {
  await db.schema
    .createTable('advertisements')
    .addColumn('id', 'serial', (col) => col.primaryKey())
    .addColumn('device_mac', 'varchar(17)', (col) => col.notNull())
    .addColumn('timestamp', 'timestamp', (col) => col.notNull())
    .execute();
}
```

## Consequences

### Positive

- **End-to-end type safety**: TypeScript knows exact database schema, catches errors at compile time
- **Excellent developer experience**: Autocomplete for table names, columns, and query methods
- **Refactoring confidence**: Renaming columns caught by TypeScript compiler
- **SQL-like syntax**: Familiar to developers who know SQL, low learning curve
- **No code generation**: Types derived from TypeScript interfaces, no build step needed
- **Raw SQL support**: Can drop to raw SQL for complex queries when needed
- **Framework agnostic**: Works with any Node.js setup, not tied to specific framework
- **Active development**: Well-maintained with good community support
- **Migration support**: Built-in migration system with TypeScript migrations
- **Performance**: Minimal overhead, generates efficient SQL queries
- **Transaction support**: First-class support for database transactions

### Negative

- **Manual type maintenance**: Database schema types must be manually kept in sync with migrations (though kysely-codegen can help)
- **Learning curve**: Some Kysely-specific APIs to learn (though close to SQL)
- **Less magic**: No ActiveRecord-style models, more explicit than some ORMs
- **Verbosity**: More verbose than some ORMs for simple CRUD operations

### Neutral

- **Not a traditional ORM**: No models/entities, just query builder (we consider this a positive)
- **PostgreSQL-specific features**: Some features require PostgreSQL-specific plugins

## Alternatives Considered

### Prisma

- **Pros**: Excellent type safety, great migrations, auto-generates types from schema, popular
- **Cons**: Heavy code generation, opininated folder structure, larger runtime, some TypeScript limitations, migration format less flexible

### TypeORM

- **Pros**: Full-featured ORM, decorators for entities, popular
- **Cons**: Weaker type safety, decorators can be problematic, heavier runtime, ActiveRecord pattern not ideal for our use case

### node-postgres (pg) with raw SQL

- **Pros**: Lightest weight, maximum control, no abstraction
- **Cons**: No type safety, manual query building, migration management needed, prone to SQL injection if not careful

### Drizzle ORM

- **Pros**: Similar type safety to Kysely, good performance, growing community
- **Cons**: Newer/less mature, smaller ecosystem, less flexible query builder

### Sequelize

- **Pros**: Very mature, large community, full-featured
- **Cons**: Weak TypeScript support, less type-safe, heavier runtime, dated API design

### MikroORM

- **Pros**: Good TypeScript support, Unit of Work pattern, modern
- **Cons**: More complex than needed, heavier runtime, steeper learning curve

## Migration Strategy

Migrations stored in `src/migrations/` with timestamp prefixes:
```
migrations/
  001_initial_schema.ts
  002_add_battery_column.ts
  003_add_indexes.ts
```

Migration runner:
```bash
npm run migrate:latest  # Run pending migrations
npm run migrate:down    # Rollback last migration
npm run migrate:create  # Create new migration file
```

## Type Generation

Options for keeping types in sync:
1. **Manual** (chosen initially): Update `Database` interface when schema changes
2. **kysely-codegen** (future): Auto-generate types from live database
3. **kysely-ctl** (future): Enhanced tooling for migrations and types

Starting with manual approach for simplicity, can add codegen later if needed.

## Implementation Notes

Connection pooling:
```typescript
const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  max: 10
});
```

Query patterns:
- Use `insertInto()` for new readings
- Use `selectFrom()` with `where()` for queries  
- Use `updateTable()` for updates
- Use transactions for multi-step operations
