# Feature: Scanner Heartbeat

**Status:** Planned  
**Milestone:** Phase 2 - Core Features  
**Owner:** TBD  
**Related ADRs:** [ADR-0003: MQTT Topic Structure](../../decisions/0003-mqtt-topic-structure.md)

---

## Overview

Scanner Heartbeat provides health monitoring and status reporting for BLE scanners. It publishes periodic status messages containing scanner health, operational metrics, and system information, enabling centralized monitoring of distributed scanner deployments.

### Motivation

In production deployments:
- Need to know if scanner is operational
- Need to detect scanner crashes or hangs
- Need visibility into scanner performance
- Need to track device discovery rates
- Need to monitor system resources

### Goals

- Publish periodic heartbeat messages
- Include scanner health status
- Report device discovery metrics
- Include system resource usage
- Support configurable heartbeat interval
- Enable alerting on missing heartbeats

### Non-Goals

- Detailed performance profiling
- Remote scanner control
- Scanner log aggregation
- Network diagnostics

---

## Requirements

### Functional Requirements

1. **FR-1**: Publish heartbeat message every N seconds (default: 60)
2. **FR-2**: Include scanner status (running, stopped, error)
3. **FR-3**: Include device discovery count
4. **FR-4**: Include deduplication statistics
5. **FR-5**: Include system uptime
6. **FR-6**: Include system memory usage
7. **FR-7**: Include MQTT connection status
8. **FR-8**: Use dedicated MQTT topic: `ble/scanner/{scanner_id}/status`

### Non-Functional Requirements

1. **NFR-1**: **Reliability**: Heartbeat never blocks scanning
2. **NFR-2**: **Performance**: Heartbeat adds <1ms overhead
3. **NFR-3**: **Consistency**: Heartbeat interval accurate within 5%

---

## Dependencies

### Prerequisites

- BLE Scanner (Phase 1)
- MQTT Publisher (Phase 1)

### Blocked By

- None

### Blocks

- None (monitoring feature)

---

## Technical Design

### MQTT Topic

```
ble/scanner/{scanner_id}/status
```

Example: `ble/scanner/scanner-01/status`

### Message Format

```json
{
  "scanner_id": "scanner-01",
  "timestamp": "2026-01-11T10:30:45.123Z",
  "status": "running",
  "uptime_seconds": 3600,
  "metrics": {
    "devices_discovered": 42,
    "advertisements_received": 15234,
    "advertisements_published": 1523,
    "deduplication_rate": 0.90,
    "blocked_devices": 8
  },
  "system": {
    "memory_usage_mb": 45.3,
    "cpu_percent": 5.2,
    "platform": "linux"
  },
  "mqtt": {
    "connected": true,
    "messages_sent": 1523,
    "last_error": null
  }
}
```

### Implementation

```python
# src/scanner/heartbeat.py
import asyncio
import psutil
import time
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class HeartbeatMetrics:
    devices_discovered: int
    advertisements_received: int
    advertisements_published: int
    deduplication_rate: float
    blocked_devices: int

@dataclass
class SystemMetrics:
    memory_usage_mb: float
    cpu_percent: float
    platform: str

@dataclass
class MQTTMetrics:
    connected: bool
    messages_sent: int
    last_error: str | None

@dataclass
class HeartbeatMessage:
    scanner_id: str
    timestamp: str
    status: str
    uptime_seconds: int
    metrics: HeartbeatMetrics
    system: SystemMetrics
    mqtt: MQTTMetrics

class HeartbeatPublisher:
    def __init__(
        self,
        scanner_id: str,
        mqtt_publisher,
        interval_seconds: int = 60
    ):
        self.scanner_id = scanner_id
        self.mqtt_publisher = mqtt_publisher
        self.interval_seconds = interval_seconds
        self.start_time = time.time()
        
        # Metrics collectors
        self.devices_discovered = set()
        self.advertisements_received = 0
        self.advertisements_published = 0
        self.blocked_devices = set()
    
    async def start(self):
        """Start heartbeat loop"""
        while True:
            try:
                await self._publish_heartbeat()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(self.interval_seconds)
    
    async def _publish_heartbeat(self):
        """Publish a heartbeat message"""
        message = self._build_heartbeat_message()
        topic = f"ble/scanner/{self.scanner_id}/status"
        
        await self.mqtt_publisher.publish(
            topic=topic,
            payload=message,
            qos=0
        )
    
    def _build_heartbeat_message(self) -> dict:
        """Build heartbeat message"""
        uptime = int(time.time() - self.start_time)
        dedup_rate = (
            (self.advertisements_received - self.advertisements_published) 
            / self.advertisements_received
            if self.advertisements_received > 0 else 0.0
        )
        
        message = HeartbeatMessage(
            scanner_id=self.scanner_id,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            status=self._get_status(),
            uptime_seconds=uptime,
            metrics=HeartbeatMetrics(
                devices_discovered=len(self.devices_discovered),
                advertisements_received=self.advertisements_received,
                advertisements_published=self.advertisements_published,
                deduplication_rate=round(dedup_rate, 3),
                blocked_devices=len(self.blocked_devices)
            ),
            system=self._get_system_metrics(),
            mqtt=self._get_mqtt_metrics()
        )
        
        return asdict(message)
    
    def _get_status(self) -> str:
        """Get scanner status"""
        # In real implementation, check actual scanner state
        return "running"
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get system resource metrics"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        return SystemMetrics(
            memory_usage_mb=round(memory_mb, 1),
            cpu_percent=round(cpu_percent, 1),
            platform=psutil.PLATFORM
        )
    
    def _get_mqtt_metrics(self) -> MQTTMetrics:
        """Get MQTT connection metrics"""
        return MQTTMetrics(
            connected=self.mqtt_publisher.is_connected(),
            messages_sent=self.advertisements_published,
            last_error=self.mqtt_publisher.get_last_error()
        )
    
    def record_device(self, mac_address: str):
        """Record discovered device"""
        self.devices_discovered.add(mac_address)
    
    def record_advertisement(self):
        """Record received advertisement"""
        self.advertisements_received += 1
    
    def record_publish(self):
        """Record published advertisement"""
        self.advertisements_published += 1
    
    def record_blocked(self, mac_address: str):
        """Record blocked device"""
        self.blocked_devices.add(mac_address)
```

### Integration with Scanner

```python
async def main():
    scanner = BLEScanner()
    mqtt_publisher = MQTTPublisher(config)
    dedup_filter = DeduplicationFilter(config)
    blocklist_filter = BlocklistFilter(config)
    heartbeat = HeartbeatPublisher(
        scanner_id=config.scanner_id,
        mqtt_publisher=mqtt_publisher,
        interval_seconds=config.heartbeat_interval
    )
    
    # Start heartbeat in background
    asyncio.create_task(heartbeat.start())
    
    # Main scanning loop
    async for advertisement in scanner.scan():
        heartbeat.record_advertisement()
        heartbeat.record_device(advertisement.mac_address)
        
        if blocklist_filter.is_blocked(advertisement.mac_address):
            heartbeat.record_blocked(advertisement.mac_address)
            continue
        
        if dedup_filter.should_publish(...):
            await mqtt_publisher.publish(advertisement)
            heartbeat.record_publish()
```

### Configuration

```yaml
scanner:
  heartbeat:
    enabled: true
    interval_seconds: 60
    include_system_metrics: true
```

---

## Testing Strategy

### Unit Tests

- [ ] Test heartbeat message construction
- [ ] Test metrics collection
- [ ] Test system metrics gathering
- [ ] Test uptime calculation

### Integration Tests

- [ ] Test heartbeat publishing to MQTT
- [ ] Test heartbeat interval accuracy
- [ ] Verify message format
- [ ] Test with subscriber

---

## Implementation Checklist

- [ ] Create HeartbeatPublisher class
- [ ] Implement metrics collection
- [ ] Implement system metrics
- [ ] Integrate with scanner loop
- [ ] Add configuration support
- [ ] Implement background task
- [ ] Write unit tests
- [ ] Test with MQTT broker
- [ ] Document message format

---

## Acceptance Criteria

- [ ] Heartbeat published every 60 seconds
- [ ] Message contains all required fields
- [ ] Metrics are accurate
- [ ] System metrics included
- [ ] Heartbeat doesn't block scanning
- [ ] Configuration works correctly
- [ ] Unit test coverage >80%

---

## Related Features

- [BLE Scanner](../phase-1/ble-scanner.md)
- [MQTT Publisher](../phase-1/mqtt-publisher.md)
- [Deduplication](deduplication.md)

