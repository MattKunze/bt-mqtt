# 0007. Manual Scanner ID Configuration

**Date:** 2026-01-11

**Status:** Accepted

## Context

Each scanner agent publishes to a unique MQTT topic based on its scanner ID (see ADR-0003: `bt-mqtt/raw/{scanner_id}`). We need to decide how scanners obtain their unique identifier. Considerations:

- Scanner ID should be stable across restarts
- Should be meaningful for debugging and monitoring
- Multiple scanners may run in the same environment
- Deployment can be bare metal, containers, or cloud VMs
- Scanner location/purpose should be identifiable from the ID

Options range from auto-generating IDs to requiring manual configuration.

## Decision

Scanner ID will be **manually configured** via environment variable or configuration file. No auto-generation.

Configuration method:
```bash
# Environment variable
SCANNER_ID=pi-living-room python scanner.py

# Or in .env file
SCANNER_ID=pi-living-room
```

Requirements:
- Scanner ID is **required** - scanner will fail to start without it
- Must match pattern `[a-z0-9-]+` (lowercase alphanumeric and hyphens)
- Should be descriptive of scanner location/purpose

Examples:
- `pi-living-room`
- `rpi-garage`
- `office-desk`
- `scanner-01`

## Consequences

### Positive

- **Meaningful identifiers**: Human-readable names aid debugging and monitoring
- **Explicit configuration**: Forces operator to think about scanner placement and naming
- **No conflicts**: Operator controls uniqueness
- **Stable**: ID doesn't change unexpectedly due to hostname changes, MAC rotation, etc.
- **Location awareness**: ID can encode physical location or coverage area
- **Simple implementation**: No ID generation logic needed
- **Deterministic**: Same ID every time, easy to track in logs and databases
- **Deployment flexibility**: Works in any environment (bare metal, Docker, k8s)

### Negative

- **Manual setup required**: Operator must configure each scanner
- **No protection against duplicates**: Multiple scanners could use same ID if misconfigured
- **Documentation needed**: Must document ID requirements and conventions
- **Deployment automation complexity**: Must inject unique IDs when deploying multiple scanners

### Neutral

- **Convention over enforcement**: Rely on naming conventions rather than technical constraints
- **Collision detection**: MQTT doesn't prevent multiple clients on same topic (but this is observable)

## Alternatives Considered

### Auto-generate from hostname

- **Pros**: No configuration needed, automatic uniqueness
- **Cons**: Hostname may not be meaningful (e.g., `raspberrypi`), can change unexpectedly, container hostnames are often random

### Auto-generate from MAC address

- **Pros**: Guaranteed unique, stable per hardware
- **Cons**: Not human-readable (e.g., `b8-27-eb-a1-2c-3d`), makes debugging harder, MAC can change on some systems, privacy concerns

### Auto-generate UUID on first run

- **Pros**: Guaranteed unique, stable after first run
- **Cons**: Not human-readable, requires persistent storage, meaningless identifiers make debugging difficult

### Hybrid: Auto-generate with manual override

- **Pros**: Works out of box but allows customization
- **Cons**: Added complexity, encourages not setting meaningful names, auto-generated IDs still not meaningful

### Discover from MQTT broker (dynamic registration)

- **Pros**: Centralized ID management
- **Cons**: Requires broker-side logic, network dependency for startup, added complexity, doesn't solve naming problem

### Container orchestration labels (k8s annotations, etc.)

- **Pros**: Fits container deployment models
- **Cons**: Only works in orchestrated environments, doesn't work for bare metal, ties deployment to specific platforms

## Implementation Notes

Scanner startup validation:
```python
scanner_id = os.getenv('SCANNER_ID')
if not scanner_id:
    raise ValueError("SCANNER_ID environment variable is required")
if not re.match(r'^[a-z0-9-]+$', scanner_id):
    raise ValueError("SCANNER_ID must contain only lowercase letters, numbers, and hyphens")
```

Deployment automation can inject IDs:
```yaml
# docker-compose.yml
services:
  scanner-living-room:
    environment:
      - SCANNER_ID=pi-living-room
  scanner-garage:
    environment:
      - SCANNER_ID=rpi-garage
```

## Naming Conventions

Recommended naming patterns:
- Location-based: `{device}-{location}` (e.g., `pi-living-room`)
- Numeric: `scanner-{number}` (e.g., `scanner-01`)
- Purpose-based: `{purpose}-{location}` (e.g., `temp-sensor-warehouse`)

Should document in deployment guide.
