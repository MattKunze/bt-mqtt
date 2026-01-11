# Feature: Query API

**Status:** Planned  
**Milestone:** Phase 3 - Extended Features  
**Owner:** TBD  
**Related ADRs:** None

---

## Overview

The Query API provides a RESTful HTTP interface for accessing BLE device data, enabling external integrations, custom dashboards, and third-party applications to query the BT-MQTT system.

### Goals

- Provide REST API for data queries
- Support device listing and filtering
- Enable reading queries with time ranges
- Provide health check endpoints
- Support API authentication

### Non-Goals

- GraphQL interface
- WebSocket streaming
- Write operations (read-only API)
- Rate limiting (Phase 4)

---

## Requirements

### Functional Requirements

1. **FR-1**: `GET /devices` - List all devices
2. **FR-2**: `GET /devices/:mac` - Device details
3. **FR-3**: `GET /devices/:mac/readings` - Query readings
4. **FR-4**: `GET /health` - System health check
5. **FR-5**: Support pagination
6. **FR-6**: Support filtering by time range
7. **FR-7**: API key authentication

---

## Technical Design

### API Framework

- **Framework**: Fastify (high performance)
- **Port**: 3000
- **Base Path**: `/api/v1`

### Endpoints

```typescript
// GET /api/v1/devices
// List all devices with optional filters
interface DeviceListQuery {
  device_type?: string;
  status?: 'active' | 'idle' | 'inactive';
  limit?: number;
  offset?: number;
}

// GET /api/v1/devices/:mac
// Get device details
interface DeviceResponse {
  mac_address: string;
  device_type: string;
  local_name: string;
  first_seen: string;
  last_seen: string;
  message_count: number;
  status: string;
}

// GET /api/v1/devices/:mac/readings
// Query device readings
interface ReadingsQuery {
  start_time?: string;  // ISO 8601
  end_time?: string;    // ISO 8601
  limit?: number;
  offset?: number;
}

// GET /api/v1/health
// System health check
interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    database: boolean;
    mqtt: boolean;
  };
}
```

### Implementation

```typescript
// src/api/server.ts
import Fastify from 'fastify';
import { DeviceRegistry } from '../registry/device-registry';

export function createServer(
  deviceRegistry: DeviceRegistry,
  db: Kysely<Database>
) {
  const fastify = Fastify({ logger: true });
  
  // Authentication middleware
  fastify.addHook('onRequest', async (request, reply) => {
    const apiKey = request.headers['x-api-key'];
    if (!apiKey || apiKey !== process.env.API_KEY) {
      reply.code(401).send({ error: 'Unauthorized' });
    }
  });
  
  // List devices
  fastify.get('/api/v1/devices', async (request, reply) => {
    const { device_type, status, limit = 100, offset = 0 } = request.query as DeviceListQuery;
    
    let query = db.selectFrom('device_summary').selectAll();
    
    if (device_type) {
      query = query.where('device_type', '=', device_type);
    }
    
    if (status) {
      query = query.where('status', '=', status);
    }
    
    const devices = await query
      .limit(limit)
      .offset(offset)
      .execute();
    
    return { devices, count: devices.length };
  });
  
  // Get device
  fastify.get('/api/v1/devices/:mac', async (request, reply) => {
    const { mac } = request.params as { mac: string };
    
    const device = await deviceRegistry.getDevice(mac);
    
    if (!device) {
      reply.code(404).send({ error: 'Device not found' });
      return;
    }
    
    return device;
  });
  
  // Health check
  fastify.get('/api/v1/health', async (request, reply) => {
    const dbHealthy = await checkDatabase(db);
    const mqttHealthy = true;  // TODO: Implement MQTT health check
    
    const status = dbHealthy && mqttHealthy ? 'healthy' : 'degraded';
    
    return {
      status,
      timestamp: new Date().toISOString(),
      checks: {
        database: dbHealthy,
        mqtt: mqttHealthy
      }
    };
  });
  
  return fastify;
}

async function checkDatabase(db: Kysely<Database>): Promise<boolean> {
  try {
    await db.selectFrom('devices').select('id').limit(1).execute();
    return true;
  } catch {
    return false;
  }
}
```

---

## Implementation Checklist

- [ ] Set up Fastify server
- [ ] Implement device endpoints
- [ ] Implement readings endpoints
- [ ] Implement health endpoint
- [ ] Add API authentication
- [ ] Add pagination support
- [ ] Write API tests
- [ ] Generate OpenAPI spec
- [ ] Document API

---

## Acceptance Criteria

- [ ] All endpoints implemented
- [ ] Authentication works
- [ ] API returns correct data
- [ ] Performance <100ms per request
- [ ] OpenAPI documentation generated
- [ ] Integration tests pass

---

## Related Features

- [Device Registry](../phase-2/device-registry.md)
- [Data Aggregation](data-aggregation.md)
- [Custom Web UI](../phase-4/custom-web-ui.md)

