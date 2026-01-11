# Feature: Parser System

**Status:** Planned  
**Milestone:** Phase 2 - Core Features  
**Owner:** TBD  
**Related ADRs:** [ADR-0006: Parser Plugin System](../../decisions/0006-parser-plugin-system.md), [ADR-0010: Parser Manual Registration](../../decisions/0010-parser-manual-registration.md)

---

## Overview

The Parser System provides an extensible architecture for interpreting device-specific BLE advertisement data. It enables automatic device type identification and extraction of structured data from manufacturer-specific formats, transforming raw BLE advertisements into meaningful sensor readings and device events.

### Motivation

BLE devices use manufacturer-specific data formats that require custom parsing logic. A plugin-based parser system allows:
- Easy addition of new device types without core code changes
- Separation of concerns (parsing vs. storage)
- Reusable parsing logic across projects
- Community-contributed parsers

### Goals

- Define parser plugin interface
- Implement parser registry and selection
- Support automatic device type detection
- Enable manual parser registration
- Fallback to raw storage for unknown devices
- Provide parser error handling and logging

### Non-Goals

- Automatic parser discovery (manual registration only)
- Parser versioning or updates
- Parser performance optimization (Phase 3)
- Cross-device data correlation

---

## Requirements

### Functional Requirements

1. **FR-1**: Define standard parser interface
2. **FR-2**: Implement parser registry
3. **FR-3**: Select parser based on manufacturer data or service UUIDs
4. **FR-4**: Support manual parser registration
5. **FR-5**: Call parser for matching advertisements
6. **FR-6**: Store parsed data in device-specific tables
7. **FR-7**: Fallback to raw storage if no parser matches
8. **FR-8**: Handle parser errors gracefully
9. **FR-9**: Log parsing success/failure statistics
10. **FR-10**: Support parser testing and validation

### Non-Functional Requirements

1. **NFR-1**: **Performance**: Parsing adds <10ms per message
2. **NFR-2**: **Reliability**: Parser errors don't crash subscriber
3. **NFR-3**: **Extensibility**: New parsers added with <50 LOC
4. **NFR-4**: **Maintainability**: Clear parser structure and documentation

---

## Dependencies

### Prerequisites

- MQTT Subscriber (Phase 1)
- Database Setup (Phase 1)

### Blocked By

- None

### Blocks

- Environmental Parser (first concrete parser)
- All device-specific parsers

---

## Technical Design

### Parser Interface

```typescript
// src/parsers/base.ts
export interface ParsedData {
  deviceType: string;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface ParserResult {
  success: boolean;
  data?: ParsedData;
  error?: string;
}

export interface Parser {
  readonly name: string;
  readonly deviceType: string;
  readonly description: string;
  
  /**
   * Check if this parser can handle the advertisement
   */
  canParse(advertisement: RawAdvertisement): boolean;
  
  /**
   * Parse the advertisement data
   */
  parse(advertisement: RawAdvertisement): Promise<ParserResult>;
}

export interface RawAdvertisement {
  scanner_id: string;
  mac_address: string;
  rssi: number;
  timestamp: string;
  manufacturer_data?: Record<string, string>;
  service_uuids?: string[];
  local_name?: string;
}
```

### Parser Registry

```typescript
// src/parsers/registry.ts
export class ParserRegistry {
  private parsers: Map<string, Parser> = new Map();
  
  register(parser: Parser): void {
    if (this.parsers.has(parser.name)) {
      throw new Error(`Parser ${parser.name} already registered`);
    }
    this.parsers.set(parser.name, parser);
    console.log(`Registered parser: ${parser.name} (${parser.deviceType})`);
  }
  
  findParser(advertisement: RawAdvertisement): Parser | null {
    for (const parser of this.parsers.values()) {
      if (parser.canParse(advertisement)) {
        return parser;
      }
    }
    return null;
  }
  
  getAllParsers(): Parser[] {
    return Array.from(this.parsers.values());
  }
}
```

### Processing Pipeline

```typescript
// src/processing/pipeline.ts
export class ProcessingPipeline {
  constructor(
    private registry: ParserRegistry,
    private rawStorage: RawStorage,
    private parsedStorage: ParsedDataStorage
  ) {}
  
  async process(advertisement: RawAdvertisement): Promise<void> {
    // Always store raw message
    await this.rawStorage.store(advertisement);
    
    // Try to find parser
    const parser = this.registry.findParser(advertisement);
    
    if (!parser) {
      // No parser found - raw storage only
      return;
    }
    
    try {
      // Parse advertisement
      const result = await parser.parse(advertisement);
      
      if (result.success && result.data) {
        // Store parsed data
        await this.parsedStorage.store(
          advertisement.mac_address,
          result.data
        );
      } else {
        console.warn(
          `Parser ${parser.name} failed for ${advertisement.mac_address}: ${result.error}`
        );
      }
    } catch (error) {
      console.error(
        `Parser ${parser.name} threw exception:`,
        error
      );
    }
  }
}
```

### Parser Registration (Manual)

```typescript
// src/parsers/index.ts
import { ParserRegistry } from './registry';
import { XiaomiMiJiaParser } from './xiaomi-mijia';
import { RuuviTagParser } from './ruuvitag';

export function registerParsers(registry: ParserRegistry): void {
  // Manually register each parser (per ADR-0010)
  registry.register(new XiaomiMiJiaParser());
  registry.register(new RuuviTagParser());
  // Add more parsers here as they are developed
}
```

### Example Parser

```typescript
// src/parsers/example-parser.ts
export class ExampleParser implements Parser {
  readonly name = 'example-parser';
  readonly deviceType = 'example-device';
  readonly description = 'Example device parser';
  
  canParse(advertisement: RawAdvertisement): boolean {
    // Check for specific manufacturer ID
    return advertisement.manufacturer_data?.hasOwnProperty('4c00') ?? false;
  }
  
  async parse(advertisement: RawAdvertisement): Promise<ParserResult> {
    try {
      const mfgData = advertisement.manufacturer_data!['4c00'];
      
      // Parse manufacturer data
      const temperature = this.parseTemperature(mfgData);
      const humidity = this.parseHumidity(mfgData);
      const battery = this.parseBattery(mfgData);
      
      return {
        success: true,
        data: {
          deviceType: this.deviceType,
          data: {
            temperature,
            humidity,
            battery,
            rssi: advertisement.rssi
          },
          metadata: {
            parser: this.name,
            parsed_at: new Date().toISOString()
          }
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  private parseTemperature(data: string): number {
    // Implementation specific to device protocol
    return 0;
  }
  
  private parseHumidity(data: string): number {
    return 0;
  }
  
  private parseBattery(data: string): number {
    return 0;
  }
}
```

---

## Testing Strategy

### Unit Tests

- [ ] Test parser registration
- [ ] Test parser selection
- [ ] Test parser error handling
- [ ] Test fallback to raw storage
- [ ] Test duplicate parser registration

### Integration Tests

- [ ] Test full parsing pipeline
- [ ] Test with multiple parsers
- [ ] Test with unknown devices
- [ ] Verify parsed data storage

---

## Implementation Checklist

- [ ] Define Parser interface
- [ ] Create ParserRegistry class
- [ ] Create ProcessingPipeline
- [ ] Implement manual registration
- [ ] Add error handling
- [ ] Create example parser
- [ ] Integrate with subscriber
- [ ] Add statistics logging
- [ ] Write tests
- [ ] Document parser development guide

---

## Acceptance Criteria

- [ ] Parser interface defined
- [ ] Parser registry implemented
- [ ] Parsers can be registered manually
- [ ] Parser selection works correctly
- [ ] Errors handled gracefully
- [ ] Unknown devices fallback to raw storage
- [ ] Unit test coverage >80%
- [ ] Parser development guide complete

---

## Related Features

- [Environmental Parser](environmental-parser.md)
- [Device Registry](device-registry.md)
- [MQTT Subscriber](../phase-1/mqtt-subscriber.md)

---

## References

- [ADR-0006: Parser Plugin System](../../decisions/0006-parser-plugin-system.md)
- [ADR-0010: Parser Manual Registration](../../decisions/0010-parser-manual-registration.md)
