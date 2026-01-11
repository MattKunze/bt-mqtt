# Feature: Environmental Sensor Parser

**Status:** Planned  
**Milestone:** Phase 2 - Core Features  
**Owner:** TBD  
**Related ADRs:** [ADR-0006: Parser Plugin System](../../decisions/0006-parser-plugin-system.md)

---

## Overview

The Environmental Sensor Parser is the first concrete parser implementation, supporting temperature and humidity sensors such as Xiaomi MiJia, Govee, and similar BLE environmental monitoring devices. It extracts sensor readings from manufacturer-specific advertisement data and stores them in a structured format for analysis and visualization.

### Motivation

Environmental sensors are common BLE devices used for monitoring:
- Indoor temperature and humidity
- Greenhouse conditions
- Server room environment
- Home automation

Supporting these devices demonstrates the parser system's capability and provides immediate value for monitoring use cases.

### Goals

- Parse Xiaomi MiJia sensor advertisements
- Extract temperature, humidity, and battery level
- Store readings in dedicated table
- Support multiple sensor manufacturers
- Validate sensor data ranges
- Handle unit conversion (Celsius/Fahrenheit)

### Non-Goals

- Historical data aggregation (Phase 3)
- Alerting on threshold breach (Phase 3)
- Sensor calibration
- Multi-sensor fusion

---

## Requirements

### Functional Requirements

1. **FR-1**: Identify environmental sensors by manufacturer data
2. **FR-2**: Parse temperature readings (Celsius)
3. **FR-3**: Parse humidity readings (percentage)
4. **FR-4**: Parse battery level (percentage or voltage)
5. **FR-5**: Validate sensor reading ranges
6. **FR-6**: Store readings in `environmental_readings` table
7. **FR-7**: Associate readings with device registry
8. **FR-8**: Handle missing or malformed data gracefully

### Non-Functional Requirements

1. **NFR-1**: **Accuracy**: Parse readings with manufacturer-specified precision
2. **NFR-2**: **Performance**: Parse in <5ms per message
3. **NFR-3**: **Reliability**: Invalid data doesn't crash parser

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

### Supported Devices

1. **Xiaomi MiJia LYWSD03MMC**
   - Manufacturer ID: `0x0017` (Xiaomi)
   - Temperature: -40°C to 60°C, 0.1°C resolution
   - Humidity: 0-100%, 1% resolution
   - Battery: 0-100%

2. **Govee H5075**
   - Manufacturer ID: `0xEC88` (Govee)
   - Temperature: -20°C to 60°C, 0.1°C resolution
   - Humidity: 0-99%, 0.1% resolution
   - Battery: 0-100%

### Database Schema

```sql
CREATE TABLE environmental_readings (
  id BIGSERIAL PRIMARY KEY,
  device_id BIGINT NOT NULL REFERENCES devices(id),
  mac_address VARCHAR(17) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  temperature_c NUMERIC(5, 2),  -- Celsius, -99.99 to 99.99
  humidity_percent NUMERIC(5, 2),  -- 0.00 to 100.00
  battery_percent INTEGER,  -- 0 to 100
  rssi INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_environmental_device ON environmental_readings(device_id);
CREATE INDEX idx_environmental_timestamp ON environmental_readings(timestamp);
CREATE INDEX idx_environmental_mac ON environmental_readings(mac_address);
```

### Parser Implementation

```typescript
// src/parsers/xiaomi-mijia.ts
export class XiaomiMiJiaParser implements Parser {
  readonly name = 'xiaomi-mijia';
  readonly deviceType = 'environmental-sensor';
  readonly description = 'Xiaomi MiJia temperature/humidity sensor';
  
  private readonly MANUFACTURER_ID = '0017';  // Xiaomi
  
  canParse(advertisement: RawAdvertisement): boolean {
    return advertisement.manufacturer_data?.hasOwnProperty(this.MANUFACTURER_ID) ?? false;
  }
  
  async parse(advertisement: RawAdvertisement): Promise<ParserResult> {
    try {
      const mfgData = advertisement.manufacturer_data![this.MANUFACTURER_ID];
      
      // Parse hex data
      const buffer = Buffer.from(mfgData, 'hex');
      
      // Extract temperature (bytes 6-7, little endian, signed, x0.1)
      const tempRaw = buffer.readInt16LE(6);
      const temperature = tempRaw / 10;
      
      // Extract humidity (bytes 8-9, little endian, unsigned, x0.1)
      const humidityRaw = buffer.readUInt16LE(8);
      const humidity = humidityRaw / 10;
      
      // Extract battery (byte 10, unsigned)
      const battery = buffer.readUInt8(10);
      
      // Validate ranges
      if (temperature < -40 || temperature > 60) {
        return {
          success: false,
          error: `Temperature out of range: ${temperature}°C`
        };
      }
      
      if (humidity < 0 || humidity > 100) {
        return {
          success: false,
          error: `Humidity out of range: ${humidity}%`
        };
      }
      
      if (battery < 0 || battery > 100) {
        return {
          success: false,
          error: `Battery out of range: ${battery}%`
        };
      }
      
      return {
        success: true,
        data: {
          deviceType: this.deviceType,
          data: {
            temperature_c: temperature,
            humidity_percent: humidity,
            battery_percent: battery,
            rssi: advertisement.rssi
          },
          metadata: {
            parser: this.name,
            manufacturer: 'Xiaomi',
            model: 'LYWSD03MMC',
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
}
```

### Data Storage

```typescript
// src/storage/environmental-storage.ts
export class EnvironmentalStorage {
  constructor(private db: Kysely<Database>) {}
  
  async store(
    deviceId: bigint,
    macAddress: string,
    timestamp: Date,
    data: any
  ): Promise<void> {
    await this.db
      .insertInto('environmental_readings')
      .values({
        device_id: deviceId,
        mac_address: macAddress,
        timestamp,
        temperature_c: data.temperature_c,
        humidity_percent: data.humidity_percent,
        battery_percent: data.battery_percent,
        rssi: data.rssi
      })
      .execute();
  }
  
  async getLatestReading(macAddress: string): Promise<any | null> {
    return await this.db
      .selectFrom('environmental_readings')
      .selectAll()
      .where('mac_address', '=', macAddress)
      .orderBy('timestamp', 'desc')
      .limit(1)
      .executeTakeFirst();
  }
  
  async getReadingsInRange(
    macAddress: string,
    startTime: Date,
    endTime: Date
  ): Promise<any[]> {
    return await this.db
      .selectFrom('environmental_readings')
      .selectAll()
      .where('mac_address', '=', macAddress)
      .where('timestamp', '>=', startTime)
      .where('timestamp', '<=', endTime)
      .orderBy('timestamp', 'asc')
      .execute();
  }
}
```

---

## Testing Strategy

### Unit Tests

- [ ] Test Xiaomi data parsing
- [ ] Test Govee data parsing
- [ ] Test temperature validation
- [ ] Test humidity validation
- [ ] Test battery validation
- [ ] Test malformed data handling
- [ ] Test canParse() method

### Integration Tests

- [ ] Test with real sensor data
- [ ] Test database storage
- [ ] Verify data types and precision
- [ ] Test with device registry

### Manual Tests

- [ ] Test with physical Xiaomi sensor
- [ ] Test with physical Govee sensor
- [ ] Verify readings accuracy
- [ ] Test battery reporting

---

## Implementation Checklist

- [ ] Create database migration for environmental_readings table
- [ ] Implement XiaomiMiJiaParser
- [ ] Implement GoveeParser
- [ ] Create EnvironmentalStorage class
- [ ] Add data validation
- [ ] Register parsers with registry
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test with real devices
- [ ] Document supported devices

---

## Acceptance Criteria

- [ ] Parser identifies environmental sensors correctly
- [ ] Temperature parsed with 0.1°C precision
- [ ] Humidity parsed with 1% precision
- [ ] Battery level extracted correctly
- [ ] Data stored in database successfully
- [ ] Invalid readings rejected
- [ ] Unit test coverage >80%
- [ ] Tested with physical devices
- [ ] Documentation complete

---

## Related Features

- [Parser System](parser-system.md)
- [Device Registry](device-registry.md)

---

## References

- [Xiaomi MiJia Protocol](https://github.com/custom-components/ble_monitor)
- [Govee API Documentation](https://govee-public.s3.amazonaws.com/developer-docs/GoveeDeveloperAPIReference.pdf)
