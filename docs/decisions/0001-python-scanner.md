# 0001. Python with Bleak for Scanner Agent

**Date:** 2026-01-11

**Status:** Accepted

## Context

The scanner agent needs to continuously scan for Bluetooth Low Energy (BLE) advertisements and publish raw advertisement data to MQTT. This component is the primary interface to the Bluetooth hardware and needs:

- Reliable access to Bluetooth hardware across multiple platforms (Linux, macOS, Windows)
- Ability to capture raw BLE advertisement packets with manufacturer data
- Low-level control over scanning parameters (passive scanning, scan intervals)
- Minimal processing overhead to maximize scan coverage
- Simple deployment and maintenance

Different language ecosystems provide varying levels of Bluetooth support and hardware abstraction.

## Decision

We will implement the scanner agent in Python using the Bleak library for Bluetooth operations.

## Consequences

### Positive

- **Cross-platform compatibility**: Bleak provides a consistent API across Linux (BlueZ), macOS (CoreBluetooth), and Windows (WinRT)
- **Mature ecosystem**: Python has excellent MQTT client libraries (paho-mqtt) and JSON handling
- **Simple deployment**: Easy to package and deploy as a standalone service or container
- **Raw data access**: Bleak provides access to manufacturer data and RSSI values from advertisements
- **Active maintenance**: Bleak is actively maintained with good community support
- **Rapid development**: Python's simplicity allows quick iteration on scanning logic
- **Low barrier to entry**: Python is widely understood, making the scanner agent accessible to contributors

### Negative

- **Performance overhead**: Python is slower than compiled languages, though this is acceptable for BLE scanning use cases
- **Type safety**: Dynamic typing requires more runtime validation, though type hints can mitigate this
- **Memory usage**: Python has higher memory overhead compared to lower-level languages
- **GIL limitations**: Python's Global Interpreter Lock could theoretically limit concurrency, though async I/O mitigates this for our use case

### Neutral

- **Separate runtime**: Requires Python runtime separate from the TypeScript subscriber
- **Language boundary**: Creates a polyglot system, but with clean MQTT-based separation

## Alternatives Considered

### Node.js with @abandonware/noble

- **Pros**: Would unify the codebase in one language/runtime
- **Cons**: Noble is less actively maintained, platform support is less robust, and TypeScript/Node.js offers less benefit for this I/O-bound scanning task

### Rust with btleplug

- **Pros**: Excellent performance, memory safety, cross-platform support
- **Cons**: Steeper learning curve, slower development velocity, overkill for scanning requirements, smaller community

### Go with go-ble

- **Pros**: Good performance, simple deployment, cross-platform
- **Cons**: Less mature BLE ecosystem, limited library support compared to Python, cross-compilation complexity

### C++ with platform-native APIs

- **Pros**: Maximum performance and control
- **Cons**: Complex platform-specific code, difficult maintenance, unnecessary complexity for the use case
