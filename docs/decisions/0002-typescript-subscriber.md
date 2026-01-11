# 0002. TypeScript/Node.js for Subscriber

**Date:** 2026-01-11

**Status:** Accepted

## Context

The subscriber component receives raw BLE advertisement data from MQTT, parses it using device-specific parsers, and stores processed data in PostgreSQL. This component needs:

- Robust MQTT subscription handling with reconnection logic
- Plugin architecture for extensible device parsers
- Type-safe database operations with migrations
- Structured logging and error handling
- Integration with PostgreSQL for data persistence
- Maintainable codebase for business logic

The subscriber is more complex than the scanner and handles significant business logic around parsing, deduplication, and data storage.

## Decision

We will implement the subscriber in TypeScript running on Node.js.

## Consequences

### Positive

- **Type safety**: TypeScript provides compile-time type checking, catching errors early and improving maintainability
- **Modern async/await**: Natural handling of asynchronous MQTT messages and database operations
- **Rich ecosystem**: Excellent libraries for MQTT (mqtt.js), PostgreSQL (pg, Kysely), logging (pino), and more
- **Developer experience**: Strong IDE support with autocomplete, refactoring, and inline documentation
- **Type-safe database**: Kysely provides end-to-end type safety from database schema to application code
- **Easy testing**: Rich testing ecosystem with Jest, Vitest, and type-safe mocking
- **JSON-native**: Natural handling of JSON payloads from MQTT
- **Parser plugin system**: TypeScript interfaces enable type-safe parser registration and validation
- **Industry standard**: TypeScript is widely adopted for backend services, making hiring and collaboration easier

### Negative

- **Runtime overhead**: Node.js has higher memory usage compared to compiled languages
- **Build step required**: TypeScript requires compilation, adding complexity to deployment
- **Type erasure**: Runtime type validation still needed for external data (MQTT messages)
- **Dependency management**: npm ecosystem can have dependency bloat and security concerns

### Neutral

- **Separate from scanner**: Creates a polyglot system, but with clean separation via MQTT
- **Single-threaded**: Node.js event loop is single-threaded, but sufficient for I/O-bound operations

## Alternatives Considered

### Python

- **Pros**: Would unify with scanner codebase, good database libraries
- **Cons**: Lack of compile-time type safety makes complex business logic harder to maintain, weaker IDE support for refactoring, less structured approach to plugin architecture

### Rust

- **Pros**: Maximum performance, memory safety, excellent type system
- **Cons**: Steeper learning curve, slower development velocity, limited database ORM options, overkill for I/O-bound operations, smaller talent pool

### Go

- **Pros**: Good performance, simple deployment, built-in concurrency
- **Cons**: Less sophisticated type system, weaker database tooling compared to TypeScript ecosystem, more verbose error handling, limited generic support for plugin system

### Java/Kotlin

- **Pros**: Strong type systems, mature enterprise ecosystem
- **Cons**: Heavier runtime, more boilerplate, slower development iteration, less modern async patterns
