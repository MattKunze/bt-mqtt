# Feature: Data Aggregation

**Status:** Planned  
**Milestone:** Phase 3 - Extended Features  
**Owner:** TBD  
**Related ADRs:** None

---

## Overview

Data Aggregation provides pre-computed analytical queries, views, and materialized views for efficient access to common data patterns. This feature enables fast dashboards and reports without expensive real-time calculations.

### Goals

- Create SQL views for common queries
- Implement time-based aggregations
- Provide device activity summaries
- Calculate sensor reading averages
- Enable data retention cleanup

### Non-Goals

- Real-time streaming aggregations
- Machine learning or predictions
- Custom user-defined aggregations

---

## Requirements

### Functional Requirements

1. **FR-1**: Hourly device activity counts
2. **FR-2**: Daily device activity counts
3. **FR-3**: Average environmental readings per device
4. **FR-4**: Device uptime/reliability metrics
5. **FR-5**: RSSI distribution analysis
6. **FR-6**: Data retention cleanup queries

---

## Technical Design

### SQL Views

```sql
-- Hourly device activity
CREATE VIEW device_activity_hourly AS
SELECT 
  mac_address,
  date_trunc('hour', timestamp) AS hour,
  COUNT(*) AS message_count,
  AVG(rssi) AS avg_rssi,
  MIN(rssi) AS min_rssi,
  MAX(rssi) AS max_rssi
FROM raw_messages
GROUP BY mac_address, date_trunc('hour', timestamp);

-- Daily environmental averages
CREATE VIEW environmental_daily_avg AS
SELECT
  mac_address,
  date_trunc('day', timestamp) AS day,
  AVG(temperature_c) AS avg_temperature,
  AVG(humidity_percent) AS avg_humidity,
  MIN(temperature_c) AS min_temperature,
  MAX(temperature_c) AS max_temperature,
  COUNT(*) AS reading_count
FROM environmental_readings
GROUP BY mac_address, date_trunc('day', timestamp);

-- Device last seen summary
CREATE VIEW device_summary AS
SELECT
  d.mac_address,
  d.device_type,
  d.local_name,
  d.first_seen,
  d.last_seen,
  d.message_count,
  EXTRACT(EPOCH FROM (NOW() - d.last_seen)) / 3600 AS hours_since_last_seen,
  CASE 
    WHEN d.last_seen > NOW() - INTERVAL '1 hour' THEN 'active'
    WHEN d.last_seen > NOW() - INTERVAL '24 hours' THEN 'idle'
    ELSE 'inactive'
  END AS status
FROM devices d;
```

---

## Implementation Checklist

- [ ] Create aggregation views migration
- [ ] Create TypeScript query functions
- [ ] Add caching for expensive queries
- [ ] Implement data retention cleanup
- [ ] Write tests
- [ ] Document query patterns

---

## Acceptance Criteria

- [ ] Views created successfully
- [ ] Queries return results in <500ms
- [ ] Documentation complete

---

## Related Features

- [Query API](query-api.md)
- [Grafana Dashboards](../phase-4/grafana-dashboards.md)

