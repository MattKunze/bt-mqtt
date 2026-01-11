# Documentation Index

This directory contains comprehensive documentation for the BT-MQTT project.

## Core Documentation

- **[Architecture](architecture.md)** - System architecture, components, and data flow
- **[MQTT Schema](mqtt-schema.md)** - Topic structure, message formats, and conventions
- **[Database Schema](database-schema.md)** - PostgreSQL tables, indexes, and Kysely types
- **[Scanner](scanner.md)** - Scanner agent design, configuration, and deployment
- **[Subscriber](subscriber.md)** - Subscriber service design and parser system
- **[Deployment](deployment.md)** - Docker Compose setup and production deployment
- **[Development](development.md)** - Local development setup and contributing guide
- **[Roadmap](roadmap.md)** - Implementation phases, milestones, and timeline

## Architecture Decision Records (ADRs)

All architectural decisions are documented in [decisions/](decisions/) following the ADR format:

- [ADR-0001](decisions/0001-python-scanner.md) - Use Python for Scanner Agent
- [ADR-0002](decisions/0002-typescript-subscriber.md) - Use TypeScript for Subscriber
- [ADR-0003](decisions/0003-mqtt-topic-structure.md) - MQTT Topic Structure
- [ADR-0004](decisions/0004-processing-pipeline.md) - Processing Pipeline Architecture
- [ADR-0005](decisions/0005-deduplication-strategy.md) - Deduplication Strategy
- [ADR-0006](decisions/0006-parser-plugin-system.md) - Parser Plugin System
- [ADR-0007](decisions/0007-scanner-id-manual-config.md) - Manual Scanner ID Configuration
- [ADR-0008](decisions/0008-kysely-migrations.md) - Use Kysely for Migrations
- [ADR-0009](decisions/0009-mqtt-failure-drop-messages.md) - Drop Messages on MQTT Failure
- [ADR-0010](decisions/0010-parser-manual-registration.md) - Manual Parser Registration

See [decisions/README.md](decisions/README.md) for the ADR index and template.

## Feature Specifications

Features are organized by implementation phase in [features/](features/):

### Phase 1: Foundation
- [BLE Scanner](features/phase-1/ble-scanner.md)
- [MQTT Publisher](features/phase-1/mqtt-publisher.md)
- [MQTT Subscriber](features/phase-1/mqtt-subscriber.md)
- [Raw Storage](features/phase-1/raw-storage.md)
- [Database Setup](features/phase-1/database-setup.md)

### Phase 2: Core Features
- [Deduplication](features/phase-2/deduplication.md)
- [Blocklist](features/phase-2/blocklist.md)
- [Parser System](features/phase-2/parser-system.md)
- [Environmental Parser](features/phase-2/environmental-parser.md)
- [Device Registry](features/phase-2/device-registry.md)
- [Scanner Heartbeat](features/phase-2/scanner-heartbeat.md)

### Phase 3: Extended Features
- [Beacon Parser](features/phase-3/beacon-parser.md)
- [Data Aggregation](features/phase-3/data-aggregation.md)
- [Query API](features/phase-3/query-api.md)

### Phase 4: Visualization
- [Grafana Dashboards](features/phase-4/grafana-dashboards.md)
- [Custom Web UI](features/phase-4/custom-web-ui.md)

See [features/README.md](features/README.md) for the complete feature index with status tracking.

## Design Documents

Detailed design documents for complex features in [design/](design/):

- [Parser Plugin System](design/parser-plugin-system.md)
- [Configuration Management](design/configuration-management.md)
- [Error Handling Strategy](design/error-handling-strategy.md)

## Quick Links

- [Project README](../README.md)
- [Project Status](../STATUS.md)
- [Roadmap](roadmap.md)

## Documentation Standards

### Writing Style
- Use clear, concise language
- Include code examples where applicable
- Keep documents focused on a single topic
- Update the date when making significant changes

### Diagrams
- Use ASCII diagrams for simple flows
- Use Mermaid for complex diagrams (if needed)

### Code Examples
- Use language-specific syntax highlighting
- Include comments for clarity
- Show both Python and TypeScript examples where relevant

### Cross-References
- Link to related documents
- Reference ADRs when discussing decisions
- Link to feature specs from design docs

## Contributing to Documentation

When adding or updating documentation:

1. Follow the existing structure and format
2. Update this index if adding new documents
3. Cross-reference related documents
4. Update the "Last Updated" date
5. Keep STATUS.md synchronized with progress

## Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| README.md (this file) | ✅ Complete | 2026-01-11 |
| architecture.md | 🚧 In Progress | - |
| mqtt-schema.md | 🚧 In Progress | - |
| database-schema.md | 🚧 In Progress | - |
| scanner.md | 🚧 In Progress | - |
| subscriber.md | 🚧 In Progress | - |
| deployment.md | ⏳ Planned | - |
| development.md | ⏳ Planned | - |
| roadmap.md | 🚧 In Progress | - |
| ADRs (10 total) | 🚧 In Progress | - |
| Features (13 total) | 🚧 In Progress | - |
| Design Docs (3 total) | ⏳ Planned | - |
