# Feature: Grafana Dashboards

**Status:** Planned  
**Milestone:** Phase 4 - Visualization  
**Owner:** TBD  
**Related ADRs:** None

---

## Overview

Grafana Dashboards provide pre-built, professional data visualization and monitoring interfaces for the BT-MQTT system. Grafana offers powerful querying, alerting, and visualization capabilities out-of-the-box, enabling operators to monitor scanner health, device activity, and sensor readings.

### Motivation

Grafana provides:
- Production-ready monitoring dashboards
- Built-in alerting capabilities
- PostgreSQL data source integration
- Community ecosystem and plugins
- Low development effort for high-quality results

### Goals

- Create system overview dashboard
- Create environmental monitoring dashboard
- Create device activity dashboard
- Create scanner health dashboard
- Configure Grafana data sources
- Provision dashboards as code
- Set up alert notifications

### Non-Goals

- Custom visualization plugins
- Real-time streaming (beyond Grafana refresh)
- User management (use Grafana built-in)
- Mobile app

---

## Requirements

### Functional Requirements

1. **FR-1**: System Overview Dashboard
   - Device count by type
   - Message rate over time
   - Scanner status indicators
   - System health metrics

2. **FR-2**: Environmental Monitoring Dashboard
   - Temperature trends per device
   - Humidity trends per device
   - Battery level monitoring
   - Multi-device comparison

3. **FR-3**: Device Activity Dashboard
   - Device discovery timeline
   - Device activity heatmap
   - RSSI signal strength over time
   - Active vs. inactive devices

4. **FR-4**: Scanner Performance Dashboard
   - Scanner uptime
   - Message throughput
   - Deduplication efficiency
   - System resource usage

---

## Technical Design

### Docker Compose Integration

```yaml
# docker-compose.yml (add Grafana service)
services:
  grafana:
    image: grafana/grafana:10.2.3
    container_name: bt-mqtt-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    depends_on:
      - postgres
    networks:
      - bt-mqtt

volumes:
  grafana-data:
```

### Data Source Configuration

```yaml
# grafana/provisioning/datasources/postgres.yml
apiVersion: 1

datasources:
  - name: BT-MQTT PostgreSQL
    type: postgres
    access: proxy
    url: postgres:5432
    database: btmqtt
    user: btmqtt
    secureJsonData:
      password: ${DB_PASSWORD}
    jsonData:
      sslmode: disable
      postgresVersion: 1600
      timescaledb: false
```

### Dashboard Provisioning

```yaml
# grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1

providers:
  - name: 'BT-MQTT Dashboards'
    orgId: 1
    folder: 'BT-MQTT'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

### Example Dashboard: System Overview

```json
{
  "dashboard": {
    "title": "BT-MQTT System Overview",
    "panels": [
      {
        "id": 1,
        "title": "Total Devices",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT COUNT(*) FROM devices"
          }
        ]
      },
      {
        "id": 2,
        "title": "Active Devices (24h)",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT COUNT(*) FROM devices WHERE last_seen > NOW() - INTERVAL '24 hours'"
          }
        ]
      },
      {
        "id": 3,
        "title": "Messages per Hour",
        "type": "graph",
        "targets": [
          {
            "rawSql": "SELECT date_trunc('hour', timestamp) AS time, COUNT(*) AS count FROM raw_messages WHERE timestamp > NOW() - INTERVAL '7 days' GROUP BY time ORDER BY time"
          }
        ]
      },
      {
        "id": 4,
        "title": "Device Types",
        "type": "piechart",
        "targets": [
          {
            "rawSql": "SELECT device_type, COUNT(*) FROM devices GROUP BY device_type"
          }
        ]
      }
    ]
  }
}
```

### Example Dashboard: Environmental Monitoring

```json
{
  "dashboard": {
    "title": "Environmental Sensors",
    "panels": [
      {
        "id": 1,
        "title": "Temperature Trends",
        "type": "graph",
        "targets": [
          {
            "rawSql": "SELECT timestamp AS time, mac_address AS metric, temperature_c AS value FROM environmental_readings WHERE timestamp > NOW() - INTERVAL '24 hours' ORDER BY time"
          }
        ]
      },
      {
        "id": 2,
        "title": "Humidity Trends",
        "type": "graph",
        "targets": [
          {
            "rawSql": "SELECT timestamp AS time, mac_address AS metric, humidity_percent AS value FROM environmental_readings WHERE timestamp > NOW() - INTERVAL '24 hours' ORDER BY time"
          }
        ]
      },
      {
        "id": 3,
        "title": "Current Temperatures",
        "type": "gauge",
        "targets": [
          {
            "rawSql": "SELECT DISTINCT ON (mac_address) mac_address, temperature_c FROM environmental_readings ORDER BY mac_address, timestamp DESC"
          }
        ]
      }
    ]
  }
}
```

### Alert Configuration

```yaml
# grafana/provisioning/alerting/alerts.yml
apiVersion: 1

groups:
  - name: Device Alerts
    interval: 1m
    rules:
      - uid: device-offline
        title: Device Offline
        condition: C
        data:
          - refId: A
            datasourceUid: postgres
            model:
              rawSql: "SELECT COUNT(*) FROM devices WHERE last_seen < NOW() - INTERVAL '2 hours'"
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              expression: A
              conditions:
                - evaluator:
                    params: [0]
                    type: gt
        annotations:
          description: One or more devices have not been seen in 2 hours
```

---

## Implementation Checklist

- [ ] Add Grafana to docker-compose.yml
- [ ] Configure PostgreSQL data source
- [ ] Create System Overview dashboard
- [ ] Create Environmental Monitoring dashboard
- [ ] Create Device Activity dashboard
- [ ] Create Scanner Health dashboard
- [ ] Set up dashboard provisioning
- [ ] Configure alert rules
- [ ] Test dashboards with real data
- [ ] Document dashboard usage

---

## Acceptance Criteria

- [ ] Grafana accessible at http://localhost:3001
- [ ] PostgreSQL data source configured
- [ ] All 4 dashboards created and provisioned
- [ ] Dashboards display live data
- [ ] Alerts configured and tested
- [ ] Documentation complete

---

## Related Features

- [Data Aggregation](../phase-3/data-aggregation.md)
- [Scanner Heartbeat](../phase-2/scanner-heartbeat.md)
- [Environmental Parser](../phase-2/environmental-parser.md)

---

## References

- [Grafana Documentation](https://grafana.com/docs/)
- [Grafana PostgreSQL Data Source](https://grafana.com/docs/grafana/latest/datasources/postgres/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
