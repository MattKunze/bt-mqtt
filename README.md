# BT-MQTT: Bluetooth to MQTT Data Pipeline

A system for capturing Bluetooth Low Energy (BLE) advertisements and streaming them through MQTT to a data pipeline for storage, processing, and analysis.

## Overview

This project enables you to:
- **Capture** BLE advertisements from environmental sensors, beacons, and other Bluetooth devices
- **Stream** raw data through MQTT to a central processing service
- **Archive** complete raw advertisement data for historical analysis
- **Process** and extract sensor readings (temperature, humidity, etc.) with pluggable parsers
- **Visualize** and analyze data through Grafana dashboards or custom web interfaces

## Architecture

```
BLE Devices → Scanner Agent (Pi Zero W) → MQTT Broker → Subscriber Service → PostgreSQL
                  [Python]              mqtt.shypan.st    [TypeScript]        [Raw + Parsed]
```

**Key Components:**
- **Scanner Agent**: Lightweight Python service running on Raspberry Pi Zero W that scans for BLE advertisements and publishes to MQTT
- **MQTT Broker**: Message broker for real-time data streaming (external: mqtt.shypan.st)
- **Subscriber Service**: TypeScript/Node.js service that ingests raw data, applies parsers, and stores in PostgreSQL
- **PostgreSQL**: Database for both raw archival data and processed sensor readings

## Quick Start

### Prerequisites

- [devenv](https://devenv.sh/) (for local development)
- Docker and Docker Compose (for running PostgreSQL)
- Raspberry Pi Zero W with Bluetooth (for scanner deployment)

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd bt-mqtt

# Enter devenv shell (installs dependencies automatically)
devenv shell

# Start PostgreSQL
docker compose up -d postgres

# Run subscriber service
cd subscriber
npm install
npm run dev

# In another terminal, run scanner (requires Bluetooth adapter)
cd scanner
uv sync
uv run python -m scanner
```

## Project Structure

```
bt-mqtt/
├── scanner/          # Python BLE scanner agent (Raspberry Pi)
├── subscriber/       # TypeScript MQTT subscriber and processor
├── docs/            # Comprehensive documentation
│   ├── decisions/   # Architecture Decision Records (ADRs)
│   ├── features/    # Feature specifications by phase
│   └── design/      # Design documents
├── docker/          # Docker Compose and container configs
└── scripts/         # Deployment and utility scripts
```

## Documentation

- [Architecture Overview](docs/architecture.md) - System design and data flow
- [MQTT Schema](docs/mqtt-schema.md) - Topic structure and message formats
- [Database Schema](docs/database-schema.md) - PostgreSQL tables and Kysely types
- [Scanner Documentation](docs/scanner.md) - Scanner agent configuration and deployment
- [Subscriber Documentation](docs/subscriber.md) - Subscriber service and parser system
- [Deployment Guide](docs/deployment.md) - Production deployment instructions
- [Development Guide](docs/development.md) - Local setup and contributing
- [Roadmap](docs/roadmap.md) - Implementation phases and milestones
- [Project Status](STATUS.md) - Current progress and next steps

### Architecture Decision Records

All major architectural decisions are documented in [docs/decisions/](docs/decisions/) following the ADR format.

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Scanner Agent | Python 3.11+ with `bleak` | BLE scanning on Raspberry Pi |
| Subscriber | Node.js 20+ with TypeScript | Data processing and storage |
| Database | PostgreSQL 16+ | Raw archival and processed data |
| Query Builder | Kysely | Type-safe SQL queries and migrations |
| MQTT Broker | Mosquitto (mqtt.shypan.st) | Message streaming |
| Package Management | `uv` (Python), `npm` (Node.js) | Fast, modern tooling |
| Dev Environment | devenv (Nix) | Reproducible development setup |
| Deployment | Docker Compose | Container orchestration |

## Current Status

See [STATUS.md](STATUS.md) for the latest progress updates.

**Current Phase:** Planning & Documentation
**Next Milestone:** Phase 1 - Foundation (raw data pipeline)

## Features

### Implemented
- ✅ Project structure and documentation
- ✅ Architecture design and ADRs

### In Progress (Phase 1)
- 🚧 Scanner agent (BLE scanning + MQTT publishing)
- 🚧 Subscriber service (MQTT ingestion + raw storage)
- 🚧 Database schema with Kysely migrations
- 🚧 Docker Compose environment

### Planned (Phase 2)
- ⏳ Deduplication at scanner level
- ⏳ Device blocklist filtering
- ⏳ Parser plugin system
- ⏳ Environmental sensor parser
- ⏳ Device registry and auto-discovery
- ⏳ Scanner heartbeat monitoring

### Future (Phase 3+)
- 📋 Additional device parsers (beacons, proximity sensors)
- 📋 Data aggregation and analytics
- 📋 Query API
- 📋 Grafana dashboards
- 📋 Custom web UI (Vite + React)

## Contributing

This project is in active development. Contributions, suggestions, and feedback are welcome!

1. Check [docs/features/](docs/features/) for feature specifications
2. Review [docs/decisions/](docs/decisions/) for architectural context
3. See [docs/development.md](docs/development.md) for local setup
4. Check [STATUS.md](STATUS.md) for current work

## License

[To be determined]

## Acknowledgments

Built to experiment with IoT data pipelines, time-series data storage, and home automation monitoring.
