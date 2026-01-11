# Feature: Beacon Parser

**Status:** Planned  
**Milestone:** Phase 3 - Extended Features  
**Owner:** TBD  
**Related ADRs:** [ADR-0006: Parser Plugin System](../../decisions/0006-parser-plugin-system.md)

---

## Overview

The Beacon Parser adds support for proximity beacon protocols including iBeacon, Eddystone, and AltBeacon. These standardized formats are used for indoor positioning, proximity marketing, asset tracking, and presence detection.

### Motivation

Beacon protocols are widely deployed for:
- Indoor navigation and wayfinding
- Proximity-based notifications
- Asset tracking and inventory management
- Presence detection and attendance tracking
- Retail analytics

### Goals

- Parse iBeacon advertisements (Apple)
- Parse Eddystone advertisements (Google)
- Parse AltBeacon advertisements (open standard)
- Extract UUID, major, minor values
- Calculate estimated distance from RSSI
- Store beacon data in dedicated table

### Non-Goals

- Beacon deployment or configuration
- Trilateration or indoor positioning
- Content delivery or notifications
- Beacon firmware updates

---

## Requirements

### Functional Requirements

1. **FR-1**: Identify iBeacon advertisements
2. **FR-2**: Identify Eddystone-UID advertisements
3. **FR-3**: Identify Eddystone-URL advertisements
4. **FR-4**: Identify AltBeacon advertisements
5. **FR-5**: Extract proximity UUID
6. **FR-6**: Extract major and minor values
7. **FR-7**: Extract measured power (TX power)
8. **FR-8**: Calculate estimated distance from RSSI
9. **FR-9**: Store beacon data in `beacon_readings` table

### Non-Functional Requirements

1. **NFR-1**: **Accuracy**: Parse all standard beacon formats
2. **NFR-2**: **Performance**: Parse in <5ms per message

---

## Dependencies

### Prerequisites

- Parser System (Phase 2)
- Device Registry (Phase 2)

### Blocked By

- Parser System must be complete

### Blocks

- None

---

## Technical Design

### Supported Beacon Types

1. **iBeacon** (Apple)
   - Manufacturer ID: `0x004c` (Apple)
   - 128-bit UUID, 16-bit major, 16-bit minor
   - Measured power at 1m

2. **Eddystone-UID** (Google)
   - Service UUID: `0xFEAA`
   - 10-byte namespace + 6-byte instance
   - TX power

3. **AltBeacon** (Open Standard)
   - Manufacturer ID: `0xFFFF` + `0xBEAC`
   - 128-bit UUID, 16-bit major, 16-bit minor

### Database Schema

```sql
CREATE TABLE beacon_readings (
  id BIGSERIAL PRIMARY KEY,
  device_id BIGINT NOT NULL REFERENCES devices(id),
  mac_address VARCHAR(17) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  beacon_type VARCHAR(50) NOT NULL,  -- 'ibeacon', 'eddystone-uid', 'altbeacon'
  uuid VARCHAR(36),  -- Proximity UUID (iBeacon, AltBeacon)
  namespace VARCHAR(20),  -- Eddystone namespace
  instance VARCHAR(12),  -- Eddystone instance
  major INTEGER,  -- iBeacon, AltBeacon
  minor INTEGER,  -- iBeacon, AltBeacon
  measured_power INTEGER,  -- TX power at 1m
  rssi INTEGER NOT NULL,
  estimated_distance_m NUMERIC(8, 2),  -- Calculated distance
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_beacon_device ON beacon_readings(device_id);
CREATE INDEX idx_beacon_timestamp ON beacon_readings(timestamp);
CREATE INDEX idx_beacon_type ON beacon_readings(beacon_type);
CREATE INDEX idx_beacon_uuid ON beacon_readings(uuid);
```

### iBeacon Parser

```typescript
// src/parsers/ibeacon.ts
export class IBeaconParser implements Parser {
  readonly name = 'ibeacon';
  readonly deviceType = 'beacon';
  readonly description = 'Apple iBeacon proximity beacon';
  
  private readonly APPLE_MANUFACTURER_ID = '004c';
  private readonly IBEACON_TYPE = '0215';
  
  canParse(advertisement: RawAdvertisement): boolean {
    const mfgData = advertisement.manufacturer_data?.[this.APPLE_MANUFACTURER_ID];
    if (!mfgData) return false;
    
    // Check for iBeacon type identifier
    return mfgData.startsWith(this.IBEACON_TYPE);
  }
  
  async parse(advertisement: RawAdvertisement): Promise<ParserResult> {
    try {
      const mfgData = advertisement.manufacturer_data![this.APPLE_MANUFACTURER_ID];
      const buffer = Buffer.from(mfgData, 'hex');
      
      // iBeacon format:
      // Bytes 0-1: Type (0x02 0x15)
      // Bytes 2-17: Proximity UUID (16 bytes)
      // Bytes 18-19: Major (2 bytes, big-endian)
      // Bytes 20-21: Minor (2 bytes, big-endian)
      // Byte 22: Measured Power (signed)
      
      const uuid = this.parseUUID(buffer.slice(2, 18));
      const major = buffer.readUInt16BE(18);
      const minor = buffer.readUInt16BE(20);
      const measuredPower = buffer.readInt8(22);
      
      // Calculate estimated distance
      const distance = this.calculateDistance(
        advertisement.rssi,
        measuredPower
      );
      
      return {
        success: true,
        data: {
          deviceType: this.deviceType,
          data: {
            beacon_type: 'ibeacon',
            uuid,
            major,
            minor,
            measured_power: measuredPower,
            rssi: advertisement.rssi,
            estimated_distance_m: distance
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
        error: `Parse error: ${error.message}`
      };
    }
  }
  
  private parseUUID(buffer: Buffer): string {
    // Convert 16 bytes to UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    const hex = buffer.toString('hex');
    return [
      hex.substr(0, 8),
      hex.substr(8, 4),
      hex.substr(12, 4),
      hex.substr(16, 4),
      hex.substr(20, 12)
    ].join('-');
  }
  
  private calculateDistance(rssi: number, measuredPower: number): number {
    // Simple distance calculation (not highly accurate)
    // distance = 10 ^ ((measuredPower - rssi) / (10 * n))
    // where n is the path loss exponent (typically 2-4, using 2 for simplicity)
    const ratio = (measuredPower - rssi) / 20.0;
    const distance = Math.pow(10, ratio);
    return Math.round(distance * 100) / 100;  // Round to 2 decimals
  }
}
```

### Eddystone-UID Parser

```typescript
// src/parsers/eddystone-uid.ts
export class EddystoneUIDParser implements Parser {
  readonly name = 'eddystone-uid';
  readonly deviceType = 'beacon';
  readonly description = 'Google Eddystone-UID beacon';
  
  private readonly EDDYSTONE_SERVICE_UUID = 'FEAA';
  private readonly FRAME_TYPE_UID = 0x00;
  
  canParse(advertisement: RawAdvertisement): boolean {
    return advertisement.service_uuids?.includes(this.EDDYSTONE_SERVICE_UUID) ?? false;
  }
  
  async parse(advertisement: RawAdvertisement): Promise<ParserResult> {
    // Implementation similar to iBeacon
    // Parse namespace (10 bytes) and instance (6 bytes)
    // Calculate distance from TX power
    return { success: false, error: 'Not implemented' };
  }
}
```

---

## Testing Strategy

### Unit Tests

- [ ] Test iBeacon parsing
- [ ] Test Eddystone parsing
- [ ] Test AltBeacon parsing
- [ ] Test UUID extraction
- [ ] Test distance calculation
- [ ] Test invalid data handling

### Integration Tests

- [ ] Test with real beacon devices
- [ ] Verify database storage
- [ ] Test distance accuracy

---

## Implementation Checklist

- [ ] Create database migration
- [ ] Implement IBeaconParser
- [ ] Implement EddystoneUIDParser
- [ ] Implement EddystoneURLParser
- [ ] Implement AltBeaconParser
- [ ] Implement distance calculation
- [ ] Create beacon storage service
- [ ] Register parsers
- [ ] Write tests
- [ ] Test with real beacons

---

## Acceptance Criteria

- [ ] iBeacon parsed correctly
- [ ] Eddystone parsed correctly
- [ ] Distance calculated within 20% accuracy
- [ ] Data stored successfully
- [ ] Unit test coverage >80%

---

## Related Features

- [Parser System](../phase-2/parser-system.md)
- [Device Registry](../phase-2/device-registry.md)

