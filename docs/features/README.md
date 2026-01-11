# BT-MQTT Feature Specifications

This directory contains detailed feature specifications for the BT-MQTT project, organized by development phase.

## Feature Status Tracking

| Phase | Feature | Status | Priority | Owner |
|-------|---------|--------|----------|-------|
| **Phase 1: Foundation** |
| 1 | [BLE Scanner](phase-1/ble-scanner.md) | In Progress | P0 | TBD |
| 1 | [MQTT Publisher](phase-1/mqtt-publisher.md) | In Progress | P0 | TBD |
| 1 | [MQTT Subscriber](phase-1/mqtt-subscriber.md) | In Progress | P0 | TBD |
| 1 | [Raw Storage](phase-1/raw-storage.md) | In Progress | P0 | TBD |
| 1 | [Database Setup](phase-1/database-setup.md) | In Progress | P0 | TBD |
| **Phase 2: Core Features** |
| 2 | [Deduplication](phase-2/deduplication.md) | Planned | P0 | TBD |
| 2 | [Blocklist](phase-2/blocklist.md) | Planned | P1 | TBD |
| 2 | [Parser System](phase-2/parser-system.md) | Planned | P0 | TBD |
| 2 | [Environmental Parser](phase-2/environmental-parser.md) | Planned | P0 | TBD |
| 2 | [Device Registry](phase-2/device-registry.md) | Planned | P0 | TBD |
| 2 | [Scanner Heartbeat](phase-2/scanner-heartbeat.md) | Planned | P1 | TBD |
| **Phase 3: Extended Features** |
| 3 | [Beacon Parser](phase-3/beacon-parser.md) | Planned | P1 | TBD |
| 3 | [Data Aggregation](phase-3/data-aggregation.md) | Planned | P1 | TBD |
| 3 | [Query API](phase-3/query-api.md) | Planned | P2 | TBD |
| **Phase 4: Visualization** |
| 4 | [Grafana Dashboards](phase-4/grafana-dashboards.md) | Planned | P1 | TBD |
| 4 | [Custom Web UI](phase-4/custom-web-ui.md) | Planned | P2 | TBD |

## Status Definitions

- **Planned**: Feature specification complete, not yet started
- **In Progress**: Active development underway
- **Blocked**: Development paused due to dependencies or issues
- **Complete**: Feature implemented and tested
- **Deferred**: Postponed to future phase

## Priority Definitions

- **P0**: Critical - Required for phase completion
- **P1**: High - Important but not blocking
- **P2**: Medium - Nice to have, can be deferred
- **P3**: Low - Optional enhancement

## Feature Specification Template

Each feature specification follows this structure:

1. **Metadata**: Status, milestone, owner, related ADRs
2. **Overview**: High-level description and motivation
3. **Requirements**: Functional and non-functional requirements
4. **Dependencies**: Prerequisites and blockers
5. **Technical Design**: Architecture and implementation approach
6. **Testing Strategy**: How the feature will be validated
7. **Open Questions**: Unresolved decisions
8. **Implementation Checklist**: Concrete tasks

## Related Documentation

- [Project Roadmap](../roadmap.md) - Overall project timeline and phases
- [Architecture](../architecture.md) - System architecture overview
- [Architecture Decision Records](../decisions/README.md) - Key technical decisions
- [Database Schema](../database-schema.md) - Database design
- [MQTT Schema](../mqtt-schema.md) - Message format specifications

## Contributing

When creating or updating feature specifications:

1. Use the standard template structure
2. Reference relevant ADRs for technical decisions
3. Keep the status table in this README updated
4. Link to related features and documentation
5. Include clear acceptance criteria
6. Identify dependencies and blockers early

## Questions?

For questions about feature specifications, contact the development team or create an issue in the project repository.
