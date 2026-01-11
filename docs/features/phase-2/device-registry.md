# Feature: Device Registry

**Status:** Planned  
**Milestone:** Phase 2 - Core Features  
**Owner:** TBD  
**Related ADRs:** [ADR-0004: Processing Pipeline](../../decisions/0004-processing-pipeline.md)

---

## Overview

The Device Registry provides automatic discovery and tracking of all BLE devices detected by the system. It maintains a centralized inventory of devices, tracks their activity, identifies device types through parsers, and provides a foundation for device management features.

### Motivation

A device registry enables:
- Automatic discovery of new devices
- Tracking device first/last seen timestamps
- Device type classification
- Historical device activity analysis
- Foundation for device management UI

### Goals

- Auto-register devices on first detection
- Track first seen and last seen timestamps
- Store device type from parsers
- Support device metadata (name, location, notes)
- Provide device lookup by MAC address
- Query active vs. inactive devices

### Non-Goals

- Device authentication or pairing
- Device control or commands
- Device firmware management
- Multi-scanner device correlation

---

## Requirements

### Functional Requirements

1. **FR-1**: Automatically register new devices on first message
2. **FR-2**: Update last_seen timestamp on each message
3. **FR-3**: Store device type from parser
4. **FR-4**: Store device name from advertisements
5. **FR-5**: Support custom device metadata (notes, location, tags)
6. **FR-6**: Query devices by MAC address
7. **FR-7**: Query active devices (seen in last N hours)
8. **FR-8**: Query devices by type
9. **FR-9**: Track message count per device

### Non-Functional Requirements

1. **NFR-1**: **Performance**: Device lookup <5ms
2. **NFR-2**: **Consistency**: Registry always in sync with messages
3. **NFR-3**: **Scalability**: Support 10,000+ devices

---

## Dependencies

### Prerequisites

- Database Setup (Phase 1)
- Parser System (Phase 2)

### Blocked By

- Database Setup must be complete

### Blocks

- None (enables future features)

---

## Technical Design

### Database Schema

```sql
CREATE TABLE devices (
  id BIGSERIAL PRIMARY KEY,
  mac_address VARCHAR(17) UNIQUE NOT NULL,
  device_type VARCHAR(100),
  local_name VARCHAR(255),
  manufacturer VARCHAR(255),
  first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  message_count BIGINT NOT NULL DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_mac ON devices(mac_address);
CREATE INDEX idx_devices_type ON devices(device_type);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);
CREATE INDEX idx_devices_metadata ON devices USING GIN(metadata);

-- Add foreign key to environmental_readings
ALTER TABLE environmental_readings 
  ADD CONSTRAINT fk_environmental_device 
  FOREIGN KEY (device_id) REFERENCES devices(id);
```

### Device Registry Service

```typescript
// src/registry/device-registry.ts
export interface DeviceInfo {
  id: bigint;
  mac_address: string;
  device_type: string | null;
  local_name: string | null;
  manufacturer: string | null;
  first_seen: Date;
  last_seen: Date;
  message_count: bigint;
  metadata: Record<string, any>;
  notes: string | null;
}

export class DeviceRegistry {
  constructor(private db: Kysely<Database>) {}
  
  async registerOrUpdate(
    macAddress: string,
    deviceType: string | null,
    localName: string | null,
    manufacturer: string | null
  ): Promise<bigint> {
    // Try to get existing device
    const existing = await this.db
      .selectFrom('devices')
      .select('id')
      .where('mac_address', '=', macAddress)
      .executeTakeFirst();
    
    if (existing) {
      // Update existing device
      await this.db
        .updateTable('devices')
        .set({
          last_seen: new Date(),
          message_count: sql`message_count + 1`,
          updated_at: new Date(),
          // Update fields if they have values
          ...(deviceType && { device_type: deviceType }),
          ...(localName && { local_name: localName }),
          ...(manufacturer && { manufacturer }),
        })
        .where('id', '=', existing.id)
        .execute();
      
      return existing.id;
    } else {
      // Insert new device
      const result = await this.db
        .insertInto('devices')
        .values({
          mac_address: macAddress,
          device_type: deviceType,
          local_name: localName,
          manufacturer,
          first_seen: new Date(),
          last_seen: new Date(),
          message_count: 1n,
          metadata: {},
        })
        .returning('id')
        .executeTakeFirstOrThrow();
      
      console.log(`New device registered: ${macAddress} (${deviceType || 'unknown'})`);
      
      return result.id;
    }
  }
  
  async getDevice(macAddress: string): Promise<DeviceInfo | null> {
    return await this.db
      .selectFrom('devices')
      .selectAll()
      .where('mac_address', '=', macAddress)
      .executeTakeFirst();
  }
  
  async getActiveDevices(
    sinceHours: number = 24
  ): Promise<DeviceInfo[]> {
    const cutoff = new Date();
    cutoff.setHours(cutoff.getHours() - sinceHours);
    
    return await this.db
      .selectFrom('devices')
      .selectAll()
      .where('last_seen', '>=', cutoff)
      .orderBy('last_seen', 'desc')
      .execute();
  }
  
  async getDevicesByType(deviceType: string): Promise<DeviceInfo[]> {
    return await this.db
      .selectFrom('devices')
      .selectAll()
      .where('device_type', '=', deviceType)
      .orderBy('last_seen', 'desc')
      .execute();
  }
  
  async updateMetadata(
    macAddress: string,
    metadata: Record<string, any>
  ): Promise<void> {
    await this.db
      .updateTable('devices')
      .set({
        metadata: sql`metadata || ${JSON.stringify(metadata)}::jsonb`,
        updated_at: new Date(),
      })
      .where('mac_address', '=', macAddress)
      .execute();
  }
  
  async updateNotes(
    macAddress: string,
    notes: string
  ): Promise<void> {
    await this.db
      .updateTable('devices')
      .set({
        notes,
        updated_at: new Date(),
      })
      .where('mac_address', '=', macAddress)
      .execute();
  }
  
  async getDeviceCount(): Promise<bigint> {
    const result = await this.db
      .selectFrom('devices')
      .select(sql`COUNT(*)`.as('count'))
      .executeTakeFirstOrThrow();
    
    return result.count as bigint;
  }
}
```

### Integration with Processing Pipeline

```typescript
// src/processing/pipeline.ts (updated)
export class ProcessingPipeline {
  constructor(
    private registry: ParserRegistry,
    private deviceRegistry: DeviceRegistry,
    private rawStorage: RawStorage,
    private parsedStorage: ParsedDataStorage
  ) {}
  
  async process(advertisement: RawAdvertisement): Promise<void> {
    // Always store raw message
    await this.rawStorage.store(advertisement);
    
    // Try to find parser
    const parser = this.registry.findParser(advertisement);
    const deviceType = parser?.deviceType ?? null;
    
    // Register or update device
    const deviceId = await this.deviceRegistry.registerOrUpdate(
      advertisement.mac_address,
      deviceType,
      advertisement.local_name ?? null,
      this.extractManufacturer(advertisement)
    );
    
    if (parser) {
      try {
        const result = await parser.parse(advertisement);
        
        if (result.success && result.data) {
          await this.parsedStorage.store(
            deviceId,
            advertisement.mac_address,
            result.data
          );
        }
      } catch (error) {
        console.error(`Parser error:`, error);
      }
    }
  }
  
  private extractManufacturer(ad: RawAdvertisement): string | null {
    // Extract manufacturer from manufacturer data or service UUIDs
    if (ad.manufacturer_data) {
      const keys = Object.keys(ad.manufacturer_data);
      if (keys.length > 0) {
        return this.manufacturerIdToName(keys[0]);
      }
    }
    return null;
  }
  
  private manufacturerIdToName(id: string): string {
    const manufacturers: Record<string, string> = {
      '0017': 'Xiaomi',
      'EC88': 'Govee',
      '004c': 'Apple',
      '0075': 'Samsung',
      // Add more as needed
    };
    return manufacturers[id.toLowerCase()] ?? `Unknown (${id})`;
  }
}
```

---

## Testing Strategy

### Unit Tests

- [ ] Test device registration (new device)
- [ ] Test device update (existing device)
- [ ] Test last_seen update
- [ ] Test message count increment
- [ ] Test metadata updates
- [ ] Test query methods

### Integration Tests

- [ ] Test auto-registration from advertisements
- [ ] Test device type from parser
- [ ] Verify foreign key relationships
- [ ] Test active device query

---

## Implementation Checklist

- [ ] Create database migration for devices table
- [ ] Implement DeviceRegistry class
- [ ] Add device registration logic
- [ ] Add device update logic
- [ ] Implement query methods
- [ ] Integrate with processing pipeline
- [ ] Add manufacturer lookup
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Document API

---

## Acceptance Criteria

- [ ] Devices auto-registered on first message
- [ ] Last seen updated on each message
- [ ] Device type populated from parsers
- [ ] Message count tracked correctly
- [ ] Metadata updates work
- [ ] Query methods return correct results
- [ ] Unit test coverage >80%
- [ ] Integration tests pass

---

## Related Features

- [Parser System](parser-system.md)
- [Environmental Parser](environmental-parser.md)
- [Device Management UI](../phase-4/custom-web-ui.md)

