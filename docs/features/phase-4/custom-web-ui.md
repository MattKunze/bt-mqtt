# Feature: Custom Web UI

**Status:** Planned  
**Milestone:** Phase 4 - Visualization  
**Owner:** TBD  
**Related ADRs:** None

---

## Overview

The Custom Web UI provides a tailored, user-friendly interface for monitoring BLE devices, managing system configuration, and accessing historical data. Built with modern web technologies, it offers real-time updates, responsive design, and intuitive device management.

### Motivation

While Grafana provides excellent monitoring, a custom UI enables:
- Tailored user experience for BT-MQTT workflows
- Device management and configuration
- Real-time device discovery feed
- Custom business logic and workflows
- Branding and white-labeling

### Goals

- Build responsive web application
- Real-time device monitoring
- Historical data visualization
- Device management interface
- Configuration management
- User authentication

### Non-Goals

- Mobile native apps (use responsive web)
- Offline functionality
- Multi-tenancy
- Advanced analytics (use Grafana)

---

## Requirements

### Functional Requirements

1. **FR-1**: Real-time device discovery feed
2. **FR-2**: Device list with search and filters
3. **FR-3**: Device detail pages with history
4. **FR-4**: Environmental sensor charts
5. **FR-5**: Scanner status indicators
6. **FR-6**: Configuration management UI
7. **FR-7**: User authentication and login
8. **FR-8**: Data export (CSV, JSON)

---

## Technical Design

### Tech Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **UI Components**: shadcn/ui + Radix UI
- **Styling**: TailwindCSS
- **Charts**: Recharts
- **Real-time**: WebSocket or Server-Sent Events

### Architecture

```
┌─────────────────────────────────────┐
│         Web Browser                  │
│                                      │
│  ┌────────────────────────────────┐ │
│  │   React Application            │ │
│  │                                │ │
│  │  - Device List                 │ │
│  │  - Device Details              │ │
│  │  - Charts & Graphs             │ │
│  │  - Configuration               │ │
│  └────────────────────────────────┘ │
│            │                         │
│            ▼                         │
│  ┌────────────────────────────────┐ │
│  │   TanStack Query               │ │
│  │   (Data Fetching & Caching)    │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│       Query API (Fastify)            │
│       /api/v1/*                      │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│       PostgreSQL                     │
└─────────────────────────────────────┘
```

### Key Pages

#### 1. Dashboard (Home)
- System overview cards (device count, message rate)
- Recent device activity
- Scanner health indicators
- Quick stats

#### 2. Device List
- Searchable/filterable table
- Columns: MAC, Type, Name, Last Seen, Status
- Pagination
- Export button

#### 3. Device Detail
- Device information card
- Historical readings charts
- RSSI signal strength over time
- Raw message history
- Notes and metadata editor

#### 4. Live Feed
- Real-time device discoveries
- WebSocket or SSE connection
- Auto-scrolling list
- Filter by scanner or device type

#### 5. Configuration
- Scanner settings editor
- Blocklist management
- Alert rule configuration
- System settings

#### 6. Settings
- User profile
- API key management
- Theme preferences

### Project Structure

```
packages/web-ui/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── DeviceList.tsx
│   │   ├── DeviceCard.tsx
│   │   ├── SensorChart.tsx
│   │   └── ...
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── DeviceList.tsx
│   │   ├── DeviceDetail.tsx
│   │   ├── LiveFeed.tsx
│   │   └── Configuration.tsx
│   ├── hooks/
│   │   ├── useDevices.ts
│   │   ├── useReadings.ts
│   │   └── useWebSocket.ts
│   ├── api/
│   │   └── client.ts        # API client
│   ├── lib/
│   │   └── utils.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### Example Component

```typescript
// src/components/DeviceList.tsx
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

interface Device {
  mac_address: string;
  device_type: string;
  local_name: string;
  last_seen: string;
  status: 'active' | 'idle' | 'inactive';
}

export function DeviceList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['devices'],
    queryFn: () => apiClient.getDevices(),
    refetchInterval: 5000  // Refresh every 5 seconds
  });
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              MAC Address
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Last Seen
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data?.devices.map((device: Device) => (
            <tr key={device.mac_address} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                {device.mac_address}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                {device.device_type || 'Unknown'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                {device.local_name || '-'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                {new Date(device.last_seen).toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusBadge status={device.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Docker Integration

```dockerfile
# packages/web-ui/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Implementation Checklist

- [ ] Initialize Vite + React + TypeScript project
- [ ] Set up TailwindCSS and shadcn/ui
- [ ] Set up React Router
- [ ] Set up TanStack Query
- [ ] Create API client
- [ ] Build Dashboard page
- [ ] Build Device List page
- [ ] Build Device Detail page
- [ ] Build Live Feed page
- [ ] Build Configuration page
- [ ] Implement authentication
- [ ] Add WebSocket/SSE support
- [ ] Create Docker container
- [ ] Add to docker-compose.yml
- [ ] Write component tests
- [ ] Write E2E tests
- [ ] Document UI components

---

## Acceptance Criteria

- [ ] UI accessible at http://localhost:3002
- [ ] All pages implemented and functional
- [ ] Real-time updates working
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Authentication working
- [ ] Data export working
- [ ] Page load time <2 seconds
- [ ] Component test coverage >70%
- [ ] Documentation complete

---

## Related Features

- [Query API](../phase-3/query-api.md)
- [Device Registry](../phase-2/device-registry.md)
- [Environmental Parser](../phase-2/environmental-parser.md)

---

## References

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [TanStack Query](https://tanstack.com/query/)
- [shadcn/ui](https://ui.shadcn.com/)
- [TailwindCSS](https://tailwindcss.com/)
