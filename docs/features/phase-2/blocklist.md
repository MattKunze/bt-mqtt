# Feature: Device Blocklist

**Status:** Planned  
**Milestone:** Phase 2 - Core Features  
**Owner:** TBD  
**Related ADRs:** None

---

## Overview

The Device Blocklist feature allows filtering out unwanted BLE devices at the scanner level, preventing noise from mobile phones, laptops, and other irrelevant devices from entering the data pipeline. This reduces storage costs, improves data quality, and focuses processing on devices of interest.

### Motivation

BLE environments often contain many devices that are not relevant to monitoring objectives:
- Personal smartphones and tablets
- Laptops and computers
- Smartwatches and fitness trackers
- Random nearby devices

Filtering these at the scanner level prevents wasted resources on storage, processing, and analysis.

### Goals

- Filter devices by MAC address
- Filter devices by MAC address prefix (OUI)
- Support device name patterns
- Hot-reload blocklist without restart
- Log blocked device statistics
- Provide both file-based and configuration-based blocklists

### Non-Goals

- Allowlist (Phase 3 if needed)
- Dynamic learning of unwanted devices
- Cross-scanner blocklist synchronization
- Device classification/categorization

---

## Requirements

### Functional Requirements

1. **FR-1**: Block devices by exact MAC address match
2. **FR-2**: Block devices by MAC prefix (first 3 bytes / OUI)
3. **FR-3**: Block devices by name pattern (regex)
4. **FR-4**: Support blocklist in configuration file
5. **FR-5**: Support external blocklist file
6. **FR-6**: Reload blocklist without scanner restart
7. **FR-7**: Log blocked advertisement count
8. **FR-8**: Support comments in blocklist file
9. **FR-9**: Validate blocklist entries on load

### Non-Functional Requirements

1. **NFR-1**: **Performance**: Add <0.5ms per advertisement check
2. **NFR-2**: **Scalability**: Support 10,000+ blocklist entries
3. **NFR-3**: **Usability**: Clear error messages for invalid entries
4. **NFR-4**: **Reliability**: Invalid entries don't break entire blocklist

---

## Dependencies

### Prerequisites

- BLE Scanner (Phase 1)

### Blocked By

- None

### Blocks

- None

---

## Technical Design

### Blocklist Format

```yaml
# config/blocklist.yml
blocklist:
  # Exact MAC addresses
  mac_addresses:
    - "AA:BB:CC:DD:EE:FF"  # John's iPhone
    - "11:22:33:44:55:66"  # Office laptop
  
  # MAC prefixes (OUI - Organizationally Unique Identifier)
  mac_prefixes:
    - "F0:18:98"  # Apple devices
    - "DC:A6:32"  # Raspberry Pi
  
  # Device name patterns (regex)
  name_patterns:
    - "^iPhone.*"
    - "^Galaxy.*"
    - ".*-MacBook$"
```

### Implementation

```python
import re
from typing import Set, List, Pattern
from dataclasses import dataclass

@dataclass
class BlocklistRule:
    """A single blocklist rule"""
    type: str  # 'mac', 'prefix', 'pattern'
    value: str
    pattern: Pattern = None  # Compiled regex for name patterns
    
    def matches(self, mac: str, name: str = None) -> bool:
        if self.type == 'mac':
            return mac.upper() == self.value.upper()
        elif self.type == 'prefix':
            return mac.upper().startswith(self.value.upper())
        elif self.type == 'pattern':
            return name and self.pattern.match(name) is not None
        return False

class BlocklistFilter:
    def __init__(self, config: dict):
        self.rules: List[BlocklistRule] = []
        self.blocked_count = 0
        self.checked_count = 0
        self.load_blocklist(config)
    
    def load_blocklist(self, config: dict):
        """Load blocklist from configuration"""
        self.rules.clear()
        
        # Load exact MAC addresses
        for mac in config.get('mac_addresses', []):
            self.rules.append(BlocklistRule(type='mac', value=mac))
        
        # Load MAC prefixes
        for prefix in config.get('mac_prefixes', []):
            self.rules.append(BlocklistRule(type='prefix', value=prefix))
        
        # Load name patterns
        for pattern in config.get('name_patterns', []):
            compiled = re.compile(pattern)
            self.rules.append(BlocklistRule(
                type='pattern', 
                value=pattern, 
                pattern=compiled
            ))
    
    def is_blocked(self, mac_address: str, local_name: str = None) -> bool:
        """Check if device should be blocked"""
        self.checked_count += 1
        
        for rule in self.rules:
            if rule.matches(mac_address, local_name):
                self.blocked_count += 1
                return True
        
        return False
    
    def get_statistics(self) -> dict:
        """Return blocklist statistics"""
        block_rate = self.blocked_count / self.checked_count if self.checked_count > 0 else 0
        
        return {
            "checked": self.checked_count,
            "blocked": self.blocked_count,
            "block_rate": block_rate,
            "rule_count": len(self.rules)
        }
```

### Integration with Scanner

```python
async def scan_loop():
    scanner = BLEScanner()
    dedup_filter = DeduplicationFilter(...)
    blocklist_filter = BlocklistFilter(config.blocklist)
    
    async for advertisement in scanner.scan():
        # Check blocklist first (before deduplication)
        if blocklist_filter.is_blocked(
            advertisement.mac_address,
            advertisement.local_name
        ):
            continue  # Skip blocked device
        
        # Apply deduplication
        if dedup_filter.should_publish(...):
            await mqtt_publisher.publish(advertisement)
```

---

## Testing Strategy

### Unit Tests

- [ ] Test exact MAC match
- [ ] Test MAC prefix match
- [ ] Test name pattern match
- [ ] Test case insensitivity
- [ ] Test multiple rules
- [ ] Test reload functionality

### Integration Tests

- [ ] Test with real advertisements
- [ ] Verify blocked devices don't publish
- [ ] Test hot-reload of blocklist
- [ ] Test statistics tracking

---

## Implementation Checklist

- [ ] Create BlocklistFilter class
- [ ] Implement MAC address matching
- [ ] Implement MAC prefix matching
- [ ] Implement name pattern matching
- [ ] Add configuration loading
- [ ] Add hot-reload support
- [ ] Integrate with scanner
- [ ] Add statistics logging
- [ ] Write tests
- [ ] Document configuration

---

## Acceptance Criteria

- [ ] Devices blocked by MAC address
- [ ] Devices blocked by MAC prefix
- [ ] Devices blocked by name pattern
- [ ] Blocklist reloads without restart
- [ ] Statistics logged periodically
- [ ] Unit test coverage >80%

---

## Related Features

- [BLE Scanner](../phase-1/ble-scanner.md)
- [Deduplication](deduplication.md)

