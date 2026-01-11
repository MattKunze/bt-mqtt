# 0006. Pluggable Parser Architecture with Registry

**Date:** 2026-01-11

**Status:** Accepted

## Context

The subscriber needs to parse manufacturer-specific BLE advertisement data from various device types (Govee sensors, SwitchBot, iBeacon, etc.). Each device type has its own data format and parsing logic. Requirements:

- Support multiple device types with different data formats
- Easy to add new device parsers without modifying core code
- Type-safe parser implementations
- Route advertisements to the correct parser
- Handle unknown/unsupported devices gracefully
- Testable parser implementations in isolation

We need an extensible architecture that separates device-specific parsing from core message processing.

## Decision

Implement a **pluggable parser architecture** with a central registry.

Architecture components:

1. **Parser Interface** (`DeviceParser`):
```typescript
interface DeviceParser {
  name: string;
  canParse(advertisement: RawAdvertisement): boolean;
  parse(advertisement: RawAdvertisement): ParsedData | null;
}
```

2. **Parser Registry**:
```typescript
class ParserRegistry {
  private parsers: DeviceParser[] = [];
  
  register(parser: DeviceParser): void;
  findParser(advertisement: RawAdvertisement): DeviceParser | null;
  parseAdvertisement(advertisement: RawAdvertisement): ParsedData | null;
}
```

3. **Individual Parsers**: Each device type implements `DeviceParser` interface in its own file:
   - `parsers/govee.ts`
   - `parsers/switchbot.ts`
   - `parsers/ibeacon.ts`
   - etc.

4. **Manual Registration** (see ADR-0010): Parsers are explicitly registered in `parsers/index.ts`

## Consequences

### Positive

- **Extensibility**: New device types added by creating new parser files
- **Separation of concerns**: Each parser is independent and focused on one device type
- **Type safety**: TypeScript interfaces ensure parsers implement required methods
- **Testability**: Parsers can be unit tested in isolation with mock advertisement data
- **Clear routing**: `canParse()` method explicitly defines which parser handles which devices
- **Graceful degradation**: Unknown devices are skipped without crashing the system
- **Multiple parser strategies**: Can have parsers based on manufacturer ID, MAC prefix, or payload patterns
- **Easy debugging**: Can test individual parsers or log which parser handled each advertisement
- **Code organization**: Parser logic separated from MQTT and database code
- **Reusability**: Parser implementations can be shared or published as packages

### Negative

- **Indirection**: Adds layer of abstraction between receiving advertisement and parsing
- **Registration overhead**: Parsers must be manually registered (see ADR-0010)
- **Performance**: Registry lookup adds minimal overhead (acceptable for message volumes)

### Neutral

- **Parser count**: System complexity grows with number of device types (unavoidable)
- **Maintenance**: Each parser needs updates when device firmware changes format

## Alternatives Considered

### Monolithic if/else chain

- **Pros**: Simple, no abstraction
- **Cons**: Unmaintainable as device types grow, violates open/closed principle, hard to test, all parsing logic in one file

### Factory pattern with manufacturer ID map

- **Pros**: Direct lookup by manufacturer ID
- **Cons**: Doesn't handle MAC prefix routing, less flexible than `canParse()`, can't handle multiple parsers for same manufacturer

### Strategy pattern without registry

- **Pros**: Similar benefits to chosen approach
- **Cons**: No central management, harder to list or iterate parsers, duplicate routing logic

### Dynamic module loading (auto-discovery)

- **Pros**: Truly plug-and-play, no registration needed
- **Cons**: Complex, harder to debug, type safety challenges, see ADR-0010 for details

### Separate microservice per parser

- **Pros**: Maximum isolation, independent deployment
- **Cons**: Massive operational overhead, network latency, overkill for parsing logic

### Rule-based parsing engine

- **Pros**: Could define parsers in JSON/YAML config
- **Cons**: Less type-safe, harder to test, limited to simple parsing, complex logic difficult to express

## Implementation Notes

Parser selection order:
1. Registry iterates through registered parsers
2. First parser where `canParse()` returns `true` is used
3. If no parser matches, advertisement is logged and skipped
4. Parser order matters (more specific parsers should be registered first)

Example parser implementation:
```typescript
export const goveeParser: DeviceParser = {
  name: 'Govee',
  canParse: (ad) => ad.manufacturerId === 0x0001,
  parse: (ad) => {
    // Parse Govee-specific format
    return { temperature, humidity, battery };
  }
};
```
