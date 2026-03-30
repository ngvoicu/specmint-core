# Spec: WebSocket-Based Real-Time Dashboard for Django REST Framework API

## Overview

This spec covers adding a real-time dashboard to an existing Django REST Framework API. The dashboard displays live-updating charts for API request rates, error rates, and response times. Data lives in PostgreSQL and the system is deployed on AWS ECS.

---

## 1. Architecture

### High-Level Components

```
Browser (Dashboard UI)
   |
   |-- WebSocket (wss://)
   |         |
   |    Django Channels (ASGI)
   |         |
   |    Channel Layer (Redis)
   |         |
   |    Metrics Worker (background)
   |         |
   |    PostgreSQL (metrics data)
   |
   |-- REST API (HTTPS, existing DRF endpoints)
```

### Key Technology Choices

| Concern | Technology | Rationale |
|---|---|---|
| WebSocket server | Django Channels (daphne or uvicorn) | Native Django integration, mature library |
| Channel layer | Redis (via `channels_redis`) | Required for multi-process/multi-container pub/sub on ECS |
| Metrics collection | Django middleware writing to a `api_metrics` table | Captures request/response data at the framework boundary |
| Charting | Chart.js or Recharts (if React) | Lightweight, real-time capable |
| Task scheduling | Celery Beat or a Channels background worker | Periodic aggregation and broadcast |
| ASGI server | Uvicorn (or Daphne) behind ALB | WebSocket support on ECS |

### Deployment on AWS ECS

- **ALB**: Must be configured for WebSocket support (HTTP/1.1 upgrade, sticky sessions, increased idle timeout to 300s+).
- **ECS Service**: Run the ASGI server (uvicorn) as the primary entrypoint instead of gunicorn, or run both behind the same ALB with path-based routing (`/ws/` -> ASGI container, everything else -> WSGI container).
- **Redis**: Use AWS ElastiCache (Redis) for the channel layer. This is required for cross-container WebSocket message broadcasting.
- **Target Group Health Checks**: Ensure health check path is an HTTP endpoint (not the WebSocket path).

---

## 2. Data Model

### New Table: `api_metrics`

```sql
CREATE TABLE api_metrics (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL DEFAULT gen_random_uuid(),
    method VARCHAR(10) NOT NULL,
    path VARCHAR(2048) NOT NULL,
    status_code SMALLINT NOT NULL,
    response_time_ms DOUBLE PRECISION NOT NULL,
    is_error BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_metrics_created_at ON api_metrics (created_at DESC);
CREATE INDEX idx_api_metrics_is_error_created_at ON api_metrics (is_error, created_at DESC);
```

### Aggregation View (optional materialized view for historical queries)

```sql
CREATE MATERIALIZED VIEW api_metrics_minutely AS
SELECT
    date_trunc('minute', created_at) AS bucket,
    COUNT(*) AS request_count,
    COUNT(*) FILTER (WHERE is_error) AS error_count,
    AVG(response_time_ms) AS avg_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) AS p99_response_time_ms
FROM api_metrics
GROUP BY 1
ORDER BY 1 DESC;
```

---

## 3. Backend Implementation

### 3.1 Django Middleware for Metrics Collection

```python
# middleware/metrics.py

import time
from django.utils.timezone import now
from metrics.models import ApiMetric

class ApiMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        ApiMetric.objects.create(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            response_time_ms=duration_ms,
            is_error=(response.status_code >= 400),
        )

        return response
```

**Performance note**: In production, batch inserts or write to Redis first and flush to PostgreSQL periodically to avoid adding a DB write to every request's critical path. Consider using `bulk_create` with a buffer or Celery task.

### 3.2 Django Channels Setup

**Install dependencies:**
```
pip install channels channels-redis uvicorn
```

**ASGI configuration (`asgi.py`):**
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from dashboard.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

**Channel layer settings:**
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}
```

### 3.3 WebSocket Consumer

```python
# dashboard/consumers.py

import json
from channels.generic.websocket import AsyncWebSocketConsumer

class DashboardConsumer(AsyncWebSocketConsumer):
    GROUP_NAME = "dashboard_metrics"

    async def connect(self):
        # Add authentication check here
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def metrics_update(self, event):
        """Handle metrics broadcast from the worker."""
        await self.send(text_data=json.dumps(event["data"]))
```

**Routing:**
```python
# dashboard/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/dashboard/metrics/$", consumers.DashboardConsumer.as_asgi()),
]
```

### 3.4 Metrics Broadcasting Worker

A periodic task (Celery Beat or a custom management command) queries recent metrics and broadcasts to all connected dashboard clients.

```python
# dashboard/tasks.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.timezone import now
from datetime import timedelta
from metrics.models import ApiMetric
from django.db.models import Count, Avg, Q

def broadcast_metrics():
    """Run every 5 seconds. Aggregates the last 5 seconds of metrics and pushes to WebSocket clients."""
    channel_layer = get_channel_layer()
    cutoff = now() - timedelta(seconds=5)

    qs = ApiMetric.objects.filter(created_at__gte=cutoff)
    stats = qs.aggregate(
        request_count=Count("id"),
        error_count=Count("id", filter=Q(is_error=True)),
        avg_response_time_ms=Avg("response_time_ms"),
    )

    payload = {
        "timestamp": now().isoformat(),
        "request_rate": stats["request_count"] / 5.0,  # per second
        "error_rate": (stats["error_count"] / max(stats["request_count"], 1)) * 100,
        "avg_response_time_ms": round(stats["avg_response_time_ms"] or 0, 2),
    }

    async_to_sync(channel_layer.group_send)(
        "dashboard_metrics",
        {"type": "metrics.update", "data": payload},
    )
```

---

## 4. Frontend Implementation

### 4.1 Dashboard Page

The frontend connects via WebSocket and renders three live-updating charts:

1. **Request Rate** (line chart, requests/sec over time)
2. **Error Rate** (line chart, percentage over time, with threshold line at e.g. 5%)
3. **Response Time** (line chart, avg ms over time, optionally with p95/p99)

### 4.2 WebSocket Client

```javascript
// dashboard.js

const SOCKET_URL = `wss://${window.location.host}/ws/dashboard/metrics/`;
let socket;
let reconnectInterval = 1000;

function connect() {
    socket = new WebSocket(SOCKET_URL);

    socket.onopen = () => {
        console.log("Dashboard WebSocket connected");
        reconnectInterval = 1000; // reset backoff
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateCharts(data);
    };

    socket.onclose = () => {
        console.log(`WebSocket closed. Reconnecting in ${reconnectInterval}ms...`);
        setTimeout(connect, reconnectInterval);
        reconnectInterval = Math.min(reconnectInterval * 2, 30000); // exponential backoff
    };
}

function updateCharts(data) {
    // Append data point to each chart's dataset
    // Remove oldest point if window exceeds N minutes
    requestRateChart.data.labels.push(data.timestamp);
    requestRateChart.data.datasets[0].data.push(data.request_rate);
    requestRateChart.update('none'); // no animation for real-time

    errorRateChart.data.labels.push(data.timestamp);
    errorRateChart.data.datasets[0].data.push(data.error_rate);
    errorRateChart.update('none');

    responseTimeChart.data.labels.push(data.timestamp);
    responseTimeChart.data.datasets[0].data.push(data.avg_response_time_ms);
    responseTimeChart.update('none');

    // Trim to last 60 data points (5 minutes at 5s intervals)
    const MAX_POINTS = 60;
    [requestRateChart, errorRateChart, responseTimeChart].forEach(chart => {
        if (chart.data.labels.length > MAX_POINTS) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
    });
}

connect();
```

### 4.3 Chart Initialization (Chart.js example)

```javascript
function createChart(canvasId, label, borderColor) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: borderColor,
                borderWidth: 2,
                fill: false,
                tension: 0.3,
                pointRadius: 0,
            }]
        },
        options: {
            responsive: true,
            animation: false,
            scales: {
                x: { display: true, title: { display: true, text: 'Time' } },
                y: { display: true, beginAtZero: true }
            }
        }
    });
}

const requestRateChart = createChart('requestRateCanvas', 'Requests/sec', '#3b82f6');
const errorRateChart = createChart('errorRateCanvas', 'Error Rate (%)', '#ef4444');
const responseTimeChart = createChart('responseTimeCanvas', 'Avg Response Time (ms)', '#10b981');
```

---

## 5. Authentication and Security

- **WebSocket authentication**: Use Django Channels' `AuthMiddlewareStack` which reads the session cookie. For token-based auth (e.g., JWT), implement a custom middleware that reads the token from the WebSocket query string (`?token=...`) or the first message.
- **Rate limiting**: Limit WebSocket connections per user to prevent resource exhaustion.
- **CORS / Origin checking**: Configure `ALLOWED_HOSTS` and validate the `Origin` header in the WebSocket consumer's `connect()` method.
- **Dashboard access control**: Restrict the dashboard to staff/admin users (`user.is_staff` check in the consumer).

---

## 6. AWS ECS Deployment Considerations

### 6.1 ECS Task Definition Changes

- Replace gunicorn entrypoint with uvicorn (or run both):
  ```
  uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
  ```
- Add a separate ECS service or sidecar for the Celery Beat worker that runs `broadcast_metrics`.

### 6.2 ALB Configuration

- **Idle timeout**: Increase to 300-3600 seconds (WebSocket connections are long-lived).
- **Stickiness**: Enable session stickiness on the target group if not using Redis channel layer (but Redis channel layer is strongly recommended, making stickiness unnecessary).
- **Health check**: Point to `/health/` (HTTP), not `/ws/`.
- **Security group**: Ensure port 443 is open for WSS.

### 6.3 ElastiCache Redis

- Use a Redis cluster or single-node instance for the channel layer.
- Place it in the same VPC and security group as the ECS tasks.
- Connection string via environment variable: `REDIS_URL=redis://your-elasticache-endpoint:6379/0`.

### 6.4 Scaling

- WebSocket connections are stateful. Horizontal scaling works because Redis channel layer handles cross-instance pub/sub.
- Monitor WebSocket connection counts per container. Each uvicorn worker can handle thousands of concurrent WebSocket connections.
- Consider a separate ECS service for WebSocket traffic if the connection profile differs significantly from REST API traffic.

---

## 7. Data Retention and Performance

- **Partitioning**: Partition `api_metrics` by time (e.g., daily or weekly) using PostgreSQL native partitioning. Drop old partitions instead of running DELETE queries.
- **Buffered writes**: Instead of writing to PostgreSQL on every request, buffer metrics in Redis (LPUSH) and flush to PostgreSQL in batches every few seconds via Celery.
- **Materialized view refresh**: If using the minutely materialized view, refresh it via `REFRESH MATERIALIZED VIEW CONCURRENTLY` on a schedule (e.g., every minute via Celery Beat).
- **Retention policy**: Keep raw metrics for 7-30 days; keep aggregated data longer.

---

## 8. Implementation Phases

### Phase 1: Metrics Collection
- [ ] Create `api_metrics` Django model and migration
- [ ] Implement `ApiMetricsMiddleware`
- [ ] Add middleware to `MIDDLEWARE` setting
- [ ] Write tests for middleware (status code recording, timing, error flag)

### Phase 2: Django Channels + WebSocket
- [ ] Install `channels`, `channels_redis`, `uvicorn`
- [ ] Configure `asgi.py` with `ProtocolTypeRouter`
- [ ] Configure `CHANNEL_LAYERS` with Redis backend
- [ ] Implement `DashboardConsumer` with group join/leave
- [ ] Add WebSocket URL routing
- [ ] Write tests for WebSocket consumer (connect, disconnect, receive message)

### Phase 3: Metrics Broadcasting
- [ ] Implement `broadcast_metrics` task
- [ ] Set up Celery Beat schedule (every 5 seconds)
- [ ] Test end-to-end: middleware -> DB -> broadcast -> WebSocket message

### Phase 4: Frontend Dashboard
- [ ] Create dashboard HTML template with three canvas elements
- [ ] Add Chart.js (CDN or bundled)
- [ ] Implement WebSocket client with reconnection logic
- [ ] Implement chart update functions
- [ ] Add authentication gate (staff-only access)
- [ ] Style the dashboard

### Phase 5: AWS ECS Deployment
- [ ] Add Redis (ElastiCache) to infrastructure (Terraform/CloudFormation)
- [ ] Update ECS task definition to use uvicorn
- [ ] Configure ALB idle timeout and WebSocket support
- [ ] Add Celery Beat worker as a separate ECS service
- [ ] Update health check configuration
- [ ] Load test WebSocket connections at expected scale

### Phase 6: Production Hardening
- [ ] Implement buffered metric writes (Redis -> PostgreSQL batch flush)
- [ ] Add PostgreSQL table partitioning for `api_metrics`
- [ ] Set up data retention / partition pruning
- [ ] Add monitoring: WebSocket connection count, broadcast latency, metric write lag
- [ ] Add alerting on error rate thresholds

---

## 9. Dependencies

| Package | Version | Purpose |
|---|---|---|
| `channels` | >=4.0 | Django ASGI + WebSocket support |
| `channels-redis` | >=4.0 | Redis channel layer for cross-process pub/sub |
| `uvicorn` | >=0.20 | ASGI server with WebSocket support |
| `redis` | >=4.0 | Redis client (dependency of channels-redis) |
| `celery[redis]` | >=5.0 | Task scheduling for metrics broadcast (if using Celery) |

---

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Per-request DB write adds latency | High request volume = noticeable overhead | Buffer writes in Redis, batch flush to PG |
| WebSocket connections exhaust container memory | Dashboard under heavy use | Monitor connections, set per-user limits, autoscale |
| ALB drops WebSocket connections | Dashboard shows stale data | Client-side reconnection with exponential backoff |
| Redis channel layer outage | No broadcast to clients | Health checks on Redis, fallback to polling REST endpoint |
| PostgreSQL metrics table grows unbounded | Disk pressure, slow queries | Time-based partitioning, automated partition pruning |

---

## Summary

This spec outlines a complete approach to adding a real-time metrics dashboard to a Django REST Framework API deployed on AWS ECS. The core path is: Django middleware captures per-request metrics into PostgreSQL, a periodic worker aggregates recent data and broadcasts via Django Channels (Redis-backed) to WebSocket-connected dashboard clients, and a Chart.js frontend renders live-updating charts. The architecture scales horizontally on ECS thanks to the Redis channel layer, and production hardening includes buffered writes, table partitioning, and proper ALB configuration for long-lived WebSocket connections.
