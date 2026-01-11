# BT-MQTT Project Roadmap

## Overview

This roadmap outlines the development phases for the BT-MQTT system, a Bluetooth Low Energy (BLE) scanning and data collection platform that publishes device data via MQTT and stores it in PostgreSQL for analysis and visualization.

**Last Updated:** January 11, 2026

---

## Phase 1: Foundation

### Objective
Establish the core infrastructure and prove the basic data flow from BLE scanning through MQTT to persistent storage.

### Features

#### 1.1 Project Structure and Tooling
- **Task:** Set up TypeScript monorepo structure
- **Components:**
  - `packages/scanner/` - BLE scanning service
  - `packages/subscriber/` - MQTT consumer and data storage
  - `packages/shared/` - Common types and utilities
  - Root-level configuration and build tooling
- **Tooling:**
  - TypeScript with strict mode
  - ESLint + Prettier for code quality
  - Vitest for testing framework
  - tsx for development execution

#### 1.2 Database Schema with Kysely
- **Task:** Design and implement initial database schema
- **Schema:**
  - `raw_messages` table for all incoming BLE data
  - Basic indexes for performance
  - Migration system setup
- **Technology:** Kysely for type-safe SQL queries

#### 1.3 Scanner: Basic BLE Scanning + MQTT Publish
- **Task:** Implement BLE scanning without filtering
- **Features:**
  - Initialize Noble BLE adapter
  - Scan for all advertising packets
  - Publish raw data to MQTT (no deduplication)
  - Basic error handling
- **MQTT Topics:** `ble/raw/{mac_address}`

#### 1.4 Subscriber: MQTT Subscribe + Raw Storage
- **Task:** Consume MQTT messages and store in database
- **Features:**
  - Connect to MQTT broker
  - Subscribe to `ble/raw/#` topic pattern
  - Insert all messages into `raw_messages` table
  - Connection recovery on failures

#### 1.5 Docker Compose Infrastructure
- **Task:** Containerize dependencies
- **Services:**
  - PostgreSQL 16 with persistent volumes
  - Mosquitto MQTT broker
  - Subscriber service (containerized)
- **Configuration:** Environment variables for connection strings

#### 1.6 Configuration Management
- **Task:** Implement YAML-based configuration
- **Features:**
  - MQTT broker settings (host, port, credentials)
  - Database connection parameters
  - Scanner settings (scan interval, MQTT topics)
  - Environment-specific configs (dev, prod)

#### 1.7 Basic Logging
- **Task:** Set up structured logging
- **Features:**
  - Winston or Pino for logging
  - Log levels (debug, info, warn, error)
  - Timestamp and service identification
  - Console output for development

### Deliverable
**End-to-end raw data flow:** BLE scanner discovers devices → publishes to MQTT → subscriber stores in PostgreSQL → manual query verification

### Success Criteria
- [ ] Scanner runs continuously and publishes BLE advertisements
- [ ] Subscriber receives and stores 100% of published messages
- [ ] Database contains raw message data with timestamps
- [ ] Docker Compose brings up full stack with one command
- [ ] Configuration changes don't require code modifications
- [ ] Logs provide visibility into system operation

### Dependencies
- None (greenfield project)

### Risks
- **BLE Hardware Compatibility:** Noble may not work on all platforms
  - *Mitigation:* Test on target hardware early; document requirements
- **MQTT Message Volume:** High-frequency scanning could overwhelm broker
  - *Mitigation:* Implement basic rate limiting; monitor message throughput
- **Database Performance:** Raw storage could grow quickly
  - *Mitigation:* Add retention policy; implement basic indexes

---

## Phase 2: Core Features

### Objective
Transform the raw data pipeline into a production-ready system with intelligent filtering, parsing, and device management.

### Features

#### 2.1 Scanner: Time-Based Deduplication
- **Task:** Prevent duplicate messages for the same device
- **Logic:**
  - Track last-seen timestamp per MAC address
  - Configurable deduplication window (e.g., 60 seconds)
  - Publish only if device hasn't been seen within window
- **Configuration:** `deduplication_window_seconds` in YAML

#### 2.2 Scanner: Blocklist Filtering
- **Task:** Filter out unwanted devices
- **Features:**
  - Blocklist configuration (MAC addresses, prefixes)
  - Pattern matching for common noise devices
  - Blocklist hot-reload without restart
- **Configuration:** `blocklist` section in YAML

#### 2.3 Scanner: Heartbeat and Status Messages
- **Task:** Publish health status messages
- **Features:**
  - Periodic heartbeat (every 60 seconds)
  - Scanner status (scanning, stopped, error)
  - Device discovery count metrics
  - System health (memory, uptime)
- **MQTT Topic:** `ble/scanner/status`

#### 2.4 Subscriber: Parser System Architecture
- **Task:** Design extensible parser framework
- **Architecture:**
  - Parser registry for device type detection
  - Parser interface with standardized input/output
  - Fallback to raw storage for unknown devices
  - Parser selection based on manufacturer data or service UUIDs

#### 2.5 Subscriber: Environmental Sensor Parser
- **Task:** Implement first concrete parser
- **Devices:** Temperature/humidity sensors (e.g., Xiaomi MiJia)
- **Features:**
  - Parse manufacturer-specific data format
  - Extract temperature, humidity, battery level
  - Store in dedicated `environmental_readings` table
  - Unit conversion and validation

#### 2.6 Subscriber: Device Registry
- **Task:** Auto-discovery and tracking of devices
- **Features:**
  - `devices` table with MAC, type, first/last seen
  - Automatic device registration on first message
  - Device type identification via parsers
  - Update last-seen timestamp on each message
- **Schema:**
  - `id`, `mac_address`, `device_type`, `first_seen`, `last_seen`, `metadata`

#### 2.7 Error Handling and Retries
- **Task:** Robust error recovery
- **Features:**
  - Database connection retry with exponential backoff
  - MQTT reconnection logic
  - Dead letter queue for unparseable messages
  - Graceful shutdown on SIGTERM/SIGINT
  - Transaction support for data consistency

#### 2.8 Comprehensive Logging
- **Task:** Enhanced logging for production
- **Features:**
  - Structured JSON logs for parsing
  - Correlation IDs for message tracing
  - Performance metrics (parsing time, DB latency)
  - Log rotation and retention
  - Optional: Log shipping to external service

### Deliverable
**Production-ready system** supporting environmental sensors with intelligent filtering, auto-discovery, and reliable operation.

### Success Criteria
- [ ] Duplicate messages reduced by >90%
- [ ] Blocklist effectively filters unwanted devices
- [ ] Environmental sensor data parsed and stored correctly
- [ ] Device registry accurately tracks all seen devices
- [ ] System recovers automatically from transient failures
- [ ] Logs provide detailed troubleshooting information
- [ ] Zero data loss under normal operating conditions

### Dependencies
- Phase 1 completion required
- Access to environmental sensor devices for testing

### Risks
- **Parser Complexity:** Device-specific protocols may be poorly documented
  - *Mitigation:* Start with well-documented devices; capture raw data for analysis
- **Device Type Identification:** Multiple devices may have similar signatures
  - *Mitigation:* Use multiple identification criteria; allow manual classification
- **Database Schema Evolution:** Parser additions may require schema changes
  - *Mitigation:* Use migration system; design flexible schema with JSONB columns

---

## Phase 3: Extended Features

### Objective
Expand device support, add querying capabilities, and optimize for production scale.

### Features

#### 3.1 Additional Device Parsers
- **Task:** Support more device types
- **Parsers:**
  - **Beacon Parser:** iBeacon, Eddystone protocols
  - **Proximity Parser:** RSSI-based distance estimation
  - **Heart Rate Monitors:** BLE HR profile
  - **Smart Plugs:** Energy consumption data
  - **Asset Trackers:** Location beacons
- **Storage:** New tables per device type or generic `device_data` table

#### 3.2 Data Aggregation Queries
- **Task:** Implement common analytical queries
- **Queries:**
  - Device activity summary (count by hour/day)
  - Average environmental readings per location
  - Device uptime and reliability metrics
  - RSSI distribution analysis
  - Data retention cleanup
- **Implementation:** SQL views or materialized views

#### 3.3 REST API for Data Querying (Optional)
- **Task:** HTTP API for external access
- **Framework:** Express or Fastify
- **Endpoints:**
  - `GET /devices` - List all devices
  - `GET /devices/:mac` - Device details
  - `GET /readings` - Query readings with filters
  - `GET /health` - System health check
- **Features:** Pagination, filtering, authentication (API keys)

#### 3.4 Alert System (Optional)
- **Task:** Configurable alerting for anomalies
- **Alert Types:**
  - Device offline (no data for X minutes)
  - Sensor threshold breach (temp too high/low)
  - System health issues (high error rate)
- **Notification Channels:** MQTT, webhook, email
- **Configuration:** YAML-based alert rules

#### 3.5 Performance Optimization
- **Task:** Scale to handle high device counts
- **Optimizations:**
  - Database query optimization and index tuning
  - Connection pooling configuration
  - Batch inserts for subscriber
  - Memory profiling and leak detection
  - Scanner performance tuning (scan parameters)
- **Testing:** Load testing with simulated devices

#### 3.6 Production Deployment Documentation
- **Task:** Operations runbook
- **Documentation:**
  - System requirements and dependencies
  - Installation and configuration guide
  - Deployment architectures (single-node, distributed)
  - Monitoring and health checks
  - Backup and recovery procedures
  - Troubleshooting guide
  - Security best practices

### Deliverable
**Feature-rich system** supporting multiple device types with querying capabilities, optional alerting, optimized performance, and production-ready documentation.

### Success Criteria
- [ ] 5+ device types supported with parsers
- [ ] Aggregation queries return results in <500ms
- [ ] REST API (if implemented) handles 100+ req/s
- [ ] Alert system (if implemented) detects conditions within 1 minute
- [ ] System handles 100+ devices with <5% CPU usage
- [ ] Documentation enables deployment by new team members
- [ ] Load testing validates performance targets

### Dependencies
- Phase 2 completion required
- Access to various device types for parser development
- Production-like environment for performance testing

### Risks
- **Device Protocol Variations:** Different manufacturers may use incompatible formats
  - *Mitigation:* Modular parser design; support multiple versions per device type
- **API Security:** Exposed API could be abused
  - *Mitigation:* Implement rate limiting, authentication, input validation
- **Performance Bottlenecks:** Database or MQTT could become bottleneck
  - *Mitigation:* Early load testing; horizontal scaling options documented

---

## Phase 4: Visualization

### Objective
Provide comprehensive data visualization and management interfaces for operators and end-users.

### Features

#### 4.1 Grafana Dashboard Integration
- **Task:** Pre-built monitoring dashboards
- **Dashboards:**
  - **System Overview:** Device count, message rate, system health
  - **Environmental Monitoring:** Temperature/humidity trends per device
  - **Device Activity:** Heatmap of device appearances over time
  - **Performance Metrics:** Database performance, MQTT throughput
  - **Alert Dashboard:** Active alerts and alert history
- **Data Source:** PostgreSQL via Grafana plugin

#### 4.2 Grafana Setup and Configuration
- **Task:** Add Grafana to Docker Compose
- **Features:**
  - Pre-configured data sources
  - Dashboard provisioning (dashboards as code)
  - User authentication setup
  - Alert notification channel configuration

#### 4.3 Custom Web UI: Foundation
- **Task:** Build custom dashboard application
- **Tech Stack:**
  - Vite + React for frontend
  - TypeScript for type safety
  - TanStack Query for data fetching
  - Recharts or Chart.js for visualization
  - TailwindCSS for styling
- **Setup:** Project scaffolding, routing, authentication

#### 4.4 Real-Time Monitoring Views
- **Task:** Live data visualization
- **Features:**
  - Real-time device discovery feed (via WebSocket or SSE)
  - Live environmental readings with auto-refresh
  - RSSI signal strength visualization
  - Scanner status indicator
  - Map view for proximity-based devices

#### 4.5 Historical Data Views
- **Task:** Time-series analysis interface
- **Features:**
  - Date range selector for historical queries
  - Multi-device comparison charts
  - Data export functionality (CSV, JSON)
  - Trend analysis and statistics
  - Configurable time aggregation (hourly, daily, weekly)

#### 4.6 Device Management UI
- **Task:** Administrative interface
- **Features:**
  - Device list with search and filters
  - Device detail pages with full history
  - Manual device type override
  - Blocklist management (add/remove devices)
  - Device notes and metadata editing
  - Device grouping and tagging

#### 4.7 Configuration Management UI
- **Task:** Web-based configuration editor
- **Features:**
  - YAML editor with validation
  - Scanner configuration (deduplication, blocklist)
  - Alert rule configuration
  - User settings and preferences
  - Configuration change history

#### 4.8 User Authentication and Authorization
- **Task:** Secure multi-user access
- **Features:**
  - User registration and login
  - Role-based access control (admin, viewer)
  - API token management
  - Audit logging for admin actions
- **Technology:** JWT tokens, bcrypt for passwords

#### 4.9 Deployment and Optimization
- **Task:** Production-ready web UI
- **Features:**
  - Production build optimization
  - Docker container for web UI
  - Nginx reverse proxy configuration
  - HTTPS/TLS setup
  - CDN integration for assets
  - Performance monitoring

### Deliverable
**Complete observability and management platform** with both Grafana dashboards and custom web UI, providing real-time monitoring, historical analysis, and device management capabilities.

### Success Criteria
- [ ] Grafana dashboards provide instant system visibility
- [ ] Custom UI loads in <2 seconds on standard connections
- [ ] Real-time updates appear within 5 seconds of event
- [ ] Historical queries handle 1M+ records efficiently
- [ ] Device management UI supports 1000+ devices smoothly
- [ ] Authentication prevents unauthorized access
- [ ] UI is responsive and works on mobile devices
- [ ] All features accessible without command-line access

### Dependencies
- Phase 3 completion required (especially REST API)
- REST API must support all required endpoints
- WebSocket or SSE support for real-time features

### Risks
- **UI Complexity:** Feature-rich UI may be difficult to maintain
  - *Mitigation:* Component library, design system, comprehensive testing
- **Real-Time Performance:** WebSocket connections may not scale
  - *Mitigation:* Connection pooling, message throttling, SSE fallback
- **Security Vulnerabilities:** Web UI increases attack surface
  - *Mitigation:* Security audit, dependency scanning, rate limiting
- **Browser Compatibility:** Modern features may not work everywhere
  - *Mitigation:* Target recent browser versions only, document requirements

---

## Cross-Phase Concerns

### Testing Strategy
- **Unit Tests:** Core business logic, parsers, utilities
- **Integration Tests:** Database operations, MQTT communication
- **End-to-End Tests:** Full pipeline from scanning to storage
- **Performance Tests:** Load testing with simulated devices
- **Target Coverage:** >80% for core packages

### Documentation
- **README:** Quick start guide, prerequisites
- **Architecture Docs:** System design, component interaction
- **API Documentation:** OpenAPI spec for REST API
- **Parser Development Guide:** How to add new device types
- **Operations Manual:** Deployment, monitoring, troubleshooting
- **Configuration Reference:** All config options documented

### Security Considerations
- **Network:** MQTT TLS, database connection encryption
- **Authentication:** API keys, user authentication, RBAC
- **Input Validation:** Sanitize all external inputs
- **Secrets Management:** Environment variables, never commit secrets
- **Dependencies:** Regular security audits, automated updates
- **Logging:** Avoid logging sensitive data (credentials, PII)

### Monitoring and Observability
- **Metrics:** Message rates, parsing success rate, database latency
- **Health Checks:** Liveness and readiness endpoints
- **Alerting:** Critical errors, system degradation
- **Tracing:** Request correlation across services
- **Dashboards:** System health, business metrics

---

## Risk Register

| Risk | Probability | Impact | Phase | Mitigation |
|------|-------------|--------|-------|------------|
| BLE hardware incompatibility | Medium | High | 1 | Early testing, document requirements |
| MQTT message volume overload | Medium | Medium | 1-2 | Rate limiting, monitoring |
| Parser protocol documentation gaps | High | Medium | 2-3 | Capture raw data, community research |
| Database performance degradation | Medium | High | 3 | Early optimization, load testing |
| API security vulnerabilities | Medium | High | 3-4 | Security audit, rate limiting |
| UI complexity and maintenance | Low | Medium | 4 | Component library, testing |
| Scope creep | High | Medium | All | Strict phase gates, prioritization |
| Third-party dependency issues | Medium | Low | All | Lock dependencies, regular updates |

---

## Success Metrics

### Technical Metrics
- **Uptime:** >99% scanner uptime
- **Data Integrity:** Zero data loss under normal operation
- **Performance:** Handle 100+ devices with <5% CPU usage
- **Latency:** End-to-end data flow <10 seconds (scan to storage)
- **Test Coverage:** >80% code coverage

### Business Metrics
- **Device Support:** 5+ device types by Phase 3
- **Deployment Time:** New deployment in <30 minutes
- **Documentation Quality:** New team member productive in <1 day
- **User Adoption:** Active usage by target users within 2 weeks of Phase 4

---

## Future Enhancements (Beyond Phase 4)

- **Machine Learning:** Anomaly detection, predictive maintenance
- **Edge Computing:** Run scanner on IoT gateways (Raspberry Pi)
- **Multi-Site Support:** Centralized monitoring of distributed scanners
- **Mobile App:** Native iOS/Android apps for monitoring
- **Advanced Analytics:** Complex queries, custom reports, data exports
- **Integration APIs:** Webhook support, third-party integrations
- **High Availability:** Multi-node deployment, failover support
- **Data Mesh:** Support for multiple independent data domains

---

## Conclusion

This roadmap provides a structured approach to building the BT-MQTT platform from foundation to full-featured system. Each phase builds upon the previous one, with clear deliverables and success criteria. The phased approach allows for early validation of core concepts while progressively adding value.

**Key Principles:**
- Start simple, iterate quickly
- Validate early with real hardware
- Prioritize reliability and data integrity
- Document as you build
- Test continuously
- Plan for scale from day one

For questions or clarification on any phase, please refer to the detailed architecture documentation or contact the development team.
