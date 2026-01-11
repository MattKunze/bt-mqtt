# Project Status

**Last Updated:** 2026-01-11
**Current Phase:** Planning & Initial Documentation
**Overall Progress:** 5% (Documentation phase)

## Overview

The BT-MQTT project is in its initial phase. We've completed architectural planning and are creating foundational documentation and project structure. The focus is on establishing a clear design and roadmap before implementation begins.

## Current Milestone: Documentation & Planning

**Target:** Complete all planning artifacts and begin Phase 1 implementation
**Progress:** 2/4 major deliverables complete

### Completed ✅
- ✅ Architecture design and component breakdown
- ✅ Technology stack selection
- ✅ MQTT schema design (topics, message formats)
- ✅ Database schema design (PostgreSQL with Kysely)
- ✅ Project structure creation
- ✅ Main README.md

### In Progress 🚧
- 🚧 Architecture Decision Records (ADRs)
- 🚧 Feature specifications
- 🚧 Core documentation files
- 🚧 Development environment setup

### Blocked 🚫
None currently

## Recent Decisions

- **2026-01-11** ADR-0001: Use Python with `bleak` for scanner agent
- **2026-01-11** ADR-0002: Use TypeScript/Node.js for subscriber service
- **2026-01-11** ADR-0003: Single MQTT topic per scanner (`bt-mqtt/raw/{scanner_id}`)
- **2026-01-11** ADR-0004: Raw capture in scanner, all parsing in subscriber
- **2026-01-11** ADR-0005: Time-based deduplication at scanner level
- **2026-01-11** ADR-0006: Pluggable parser system with manual registration
- **2026-01-11** ADR-0007: Manual scanner ID configuration (no auto-generation)
- **2026-01-11** ADR-0008: Use Kysely for type-safe queries and migrations
- **2026-01-11** ADR-0009: Drop messages on MQTT connection failure
- **2026-01-11** ADR-0010: Manual parser registration (no auto-discovery)

## Next Steps

### Immediate
1. Complete all ADR documentation
2. Complete all feature specifications
3. Complete core documentation (architecture.md, mqtt-schema.md, etc.)
4. Set up devenv configuration with PostgreSQL
5. Create Docker Compose setup

### Short-term
1. Begin Phase 1 implementation:
   - Scanner: Basic BLE scanning
   - Scanner: MQTT publishing
   - Subscriber: MQTT subscription
   - Subscriber: Raw data storage
   - Database: Initial schema migration

### Medium-term
1. Complete Phase 1 (end-to-end raw data flow)
2. Begin Phase 2 (deduplication, blocklist, parser system)

## Phase Progress

### Phase 1: Foundation (0% complete)
**Goal:** Working end-to-end raw data pipeline

| Feature | Status | Notes |
|---------|--------|-------|
| BLE Scanner | Not Started | Python with bleak |
| MQTT Publisher | Not Started | Publish to mqtt.shypan.st |
| MQTT Subscriber | Not Started | Subscribe to bt-mqtt/raw/# |
| Raw Storage | Not Started | PostgreSQL with Kysely |
| Database Setup | Not Started | Initial schema migration |
| Configuration | Not Started | YAML config files |
| Docker Compose | Not Started | PostgreSQL container |

### Phase 2: Core Features (0% complete)
**Goal:** Production-ready with parser system

| Feature | Status | Notes |
|---------|--------|-------|
| Deduplication | Not Started | Time-based at scanner |
| Blocklist | Not Started | Filter unwanted devices |
| Parser System | Not Started | Plugin architecture |
| Environmental Parser | Not Started | Temp/humidity/pressure |
| Device Registry | Not Started | Auto-discovery |
| Scanner Heartbeat | Not Started | Health monitoring |

### Phase 3: Extended Features (0% complete)
**Goal:** Multiple device types and analytics

Planned features documented in roadmap.

### Phase 4: Visualization (0% complete)
**Goal:** Dashboards and monitoring UI

Deferred to later phase.

## Key Metrics

- **Documentation**: 2/13 core files complete
- **ADRs**: 0/10 complete
- **Features Specs**: 0/13 complete
- **Code**: 0 lines written
- **Tests**: 0 tests written
- **Test Coverage**: N/A

## Open Questions

None currently. All major architectural decisions have been made.

## Risks & Issues

### Risks
1. **BLE Hardware Access**: Scanner development requires physical Bluetooth adapter
   - **Mitigation**: Can mock BLE scanning for subscriber development
2. **MQTT Broker Availability**: Dependency on external mqtt.shypan.st
   - **Mitigation**: Can run local Mosquitto for development

### Issues
None currently

## Team Notes

This is an experimental IoT project focused on learning and iteration. The architecture prioritizes:
- Simplicity and maintainability
- Separation of concerns
- Ability to iterate and add features incrementally
- Complete data preservation (raw archival)

## Resources

- **Documentation**: [docs/](docs/)
- **ADRs**: [docs/decisions/](docs/decisions/)
- **Features**: [docs/features/](docs/features/)
- **Roadmap**: [docs/roadmap.md](docs/roadmap.md)
