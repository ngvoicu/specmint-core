# Transcript: "Forge a spec" for WebSocket Real-Time Dashboard

## User Prompt

> forge a spec for adding a WebSocket-based real-time dashboard to our Django REST Framework API. We need live-updating charts showing API request rates, error rates, and response times. The data is in PostgreSQL and we're deployed on AWS ECS.

---

## Claude Code Response (No Skill Loaded)

That's a solid feature request. Before I jump into writing a full spec, I have some clarifying questions that would help me nail down the right architecture. I'll list them, then provide a comprehensive spec draft based on reasonable defaults -- you can adjust from there.

### Clarifying Questions

1. **Scale**: Roughly how many API requests/minute does your service handle? This affects whether we need a dedicated time-series aggregation layer or if PostgreSQL can handle the query load directly.

2. **Dashboard audience**: Is this for internal ops/engineering only, or will customers see it? This drives auth requirements and UI polish level.

3. **Retention**: How long should granular metric data be retained? (e.g., 1-minute granularity for 24h, 5-minute for 30 days, hourly for 1 year?)

4. **Existing infra**: Do you already have Redis in your stack? Django Channels needs a channel layer backend, and Redis (via ElastiCache) is the standard choice.

5. **Frontend stack**: Are you using a specific JS framework (React, Vue, etc.) or server-rendered templates? This determines the charting approach.

6. **Auth model**: Should the dashboard WebSocket connection use the same auth as your REST API (JWT, session, etc.)?

7. **Alerting**: Do you want threshold-based alerts (e.g., error rate > 5%) as part of this, or just visualization?

I'll proceed with reasonable assumptions for now.

---

## Technical Specification: WebSocket Real-Time Dashboard

### 1. Overview

Add a real-time monitoring dashboard to the existing Django REST Framework API that displays live-updating charts for API request rates, error rates, and response times. The system uses Django Channels for WebSocket connectivity, PostgreSQL for metric storage, and is designed for AWS ECS deployment.

### 2. Architecture

```
                                    +------------------+
                                    |   ALB (AWS)      |
                                    | HTTP + WebSocket |
                                    +--------+---------+
                                             |
                              +--------------+--------------+
                              |                             |
                    +---------v---------+         +---------v---------+
                    |  Django ASGI      |         |  Django ASGI      |
                    |  (Daphne/Uvicorn) |         |  (Daphne/Uvicorn) |
                    |  ECS Task         |         |  ECS Task         |
                    +---------+---------+         +---------+---------+
                              |                             |
                    +---------v-----------------------------v---------+
                    |              Redis (ElastiCache)                 |
                    |              Channel Layer                       |
                    +------------------------+------------------------+
                                             |
                    +------------------------v------------------------+
                    |              PostgreSQL (RDS)                    |
                    |              Metrics tables                      |
                    +-------------------------------------------------+
```

**Key components:**

- **Metrics Middleware**: Django middleware that records every API request (path, status code, response time) into PostgreSQL.
- **Aggregation Worker**: Periodic task (Celery beat or ECS scheduled task) that rolls up raw metrics into time-bucketed aggregates.
- **WebSocket Consumer**: Django Channels consumer that pushes aggregated metrics to connected dashboard clients.
- **Broadcast Ticker**: A periodic task that computes current metrics and broadcasts to all connected WebSocket clients via the Redis channel layer.
- **Dashboard Frontend**: Single-page dashboard with live-updating charts.

### 3. Data Model

#### 3.1 Raw Metrics Table

```sql
CREATE TABLE api_metrics_raw (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    method          VARCHAR(10) NOT NULL,
    path            VARCHAR(512) NOT NULL,
    status_code     SMALLINT NOT NULL,
    response_time_ms FLOAT NOT NULL,
    is_error        BOOLEAN NOT NULL DEFAULT FALSE,

    -- Partitioning support
    CONSTRAINT api_metrics_raw_timestamp_check CHECK (timestamp IS NOT NULL)
);

-- Partition by day for efficient cleanup
-- CREATE TABLE api_metrics_raw_20260306 PARTITION OF api_metrics_raw
--     FOR VALUES FROM ('2026-03-06') TO ('2026-03-07');

CREATE INDEX idx_api_metrics_raw_timestamp ON api_metrics_raw (timestamp);
CREATE INDEX idx_api_metrics_raw_path_timestamp ON api_metrics_raw (path, timestamp);
```

#### 3.2 Aggregated Metrics Table

```sql
CREATE TABLE api_metrics_aggregate (
    id              BIGSERIAL PRIMARY KEY,
    bucket_start    TIMESTAMPTZ NOT NULL,
    bucket_size     VARCHAR(10) NOT NULL,  -- '1min', '5min', '1hour'
    path            VARCHAR(512),           -- NULL = all paths combined
    request_count   INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    avg_response_ms FLOAT NOT NULL DEFAULT 0,
    p50_response_ms FLOAT,
    p95_response_ms FLOAT,
    p99_response_ms FLOAT,
    min_response_ms FLOAT,
    max_response_ms FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_metrics_aggregate_bucket
        UNIQUE (bucket_start, bucket_size, path)
);

CREATE INDEX idx_metrics_aggregate_bucket ON api_metrics_aggregate (bucket_start, bucket_size);
```

### 4. Backend Components

#### 4.1 Metrics Collection Middleware

```python
# dashboard/middleware.py
import time
from django.utils import timezone

class MetricsMiddleware:
    """Records API request metrics to PostgreSQL."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        # Fire-and-forget: queue metric write to avoid blocking response
        from dashboard.tasks import record_metric
        record_metric.delay(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            response_time_ms=duration_ms,
            timestamp=timezone.now().isoformat(),
        )

        return response
```

**Key decision**: Use Celery `delay()` for async metric recording so request latency is not affected by database writes. At very high scale, consider buffering in Redis and batch-inserting.

#### 4.2 Django Channels Configuration

```python
# config/asgi.py
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

```python
# config/settings.py additions
INSTALLED_APPS += ['channels', 'dashboard']

ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}
```

#### 4.3 WebSocket Consumer

```python
# dashboard/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebSocketConsumer

class DashboardConsumer(AsyncJsonWebSocketConsumer):
    GROUP_NAME = "dashboard_metrics"

    async def connect(self):
        # TODO: Add authentication check here
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

        # Send initial snapshot on connect
        snapshot = await self.get_current_snapshot()
        await self.send_json({"type": "snapshot", "data": snapshot})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive_json(self, content):
        # Handle client messages (e.g., change time range, filter by path)
        msg_type = content.get("type")
        if msg_type == "set_filter":
            # Store filter preference for this connection
            self.scope["filter_path"] = content.get("path")

    async def metrics_update(self, event):
        """Handler for broadcast messages from the channel layer."""
        await self.send_json({
            "type": "update",
            "data": event["data"],
        })

    @staticmethod
    async def get_current_snapshot():
        from dashboard.services import MetricsService
        return await MetricsService.get_dashboard_snapshot()
```

```python
# dashboard/routing.py
from django.urls import re_path
from dashboard.consumers import DashboardConsumer

websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
]
```

#### 4.4 Metrics Aggregation and Broadcasting

```python
# dashboard/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def record_metric(method, path, status_code, response_time_ms, timestamp):
    """Insert a raw metric row."""
    from dashboard.models import ApiMetricsRaw
    ApiMetricsRaw.objects.create(
        method=method,
        path=path,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_error=(status_code >= 400),
        timestamp=timestamp,
    )

@shared_task
def aggregate_and_broadcast():
    """
    Runs every 5 seconds via Celery beat.
    Computes current metrics and broadcasts to all dashboard clients.
    """
    from dashboard.services import MetricsService

    data = MetricsService.compute_live_metrics()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard_metrics",
        {
            "type": "metrics.update",
            "data": data,
        }
    )

@shared_task
def rollup_metrics():
    """
    Runs every minute via Celery beat.
    Aggregates raw metrics into bucketed summaries.
    """
    from dashboard.services import MetricsService
    MetricsService.rollup_to_aggregates()

@shared_task
def cleanup_old_metrics():
    """
    Runs daily. Drops raw metric partitions older than retention period.
    """
    from dashboard.services import MetricsService
    MetricsService.cleanup_expired_partitions(days=7)
```

#### 4.5 Metrics Service

```python
# dashboard/services.py
from django.db import connection
from django.utils import timezone
from datetime import timedelta

class MetricsService:

    @staticmethod
    def compute_live_metrics():
        """Compute metrics for the last 60 seconds, bucketed by 5s intervals."""
        now = timezone.now()
        since = now - timedelta(seconds=60)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    date_trunc('second', timestamp)
                        - (EXTRACT(SECOND FROM timestamp)::int %% 5) * INTERVAL '1 second'
                        AS bucket,
                    COUNT(*) AS request_count,
                    COUNT(*) FILTER (WHERE is_error) AS error_count,
                    AVG(response_time_ms) AS avg_response_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_ms
                FROM api_metrics_raw
                WHERE timestamp >= %s
                GROUP BY bucket
                ORDER BY bucket
            """, [since])

            rows = cursor.fetchall()

        return {
            "timestamp": now.isoformat(),
            "window_seconds": 60,
            "buckets": [
                {
                    "time": row[0].isoformat(),
                    "request_rate": row[1] / 5.0,  # requests per second
                    "error_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                    "avg_response_ms": round(row[3], 2),
                    "p95_response_ms": round(row[4], 2) if row[4] else None,
                }
                for row in rows
            ],
        }

    @staticmethod
    def rollup_to_aggregates():
        """Roll up raw metrics into 1-minute aggregate buckets."""
        # Implementation: INSERT ... ON CONFLICT UPDATE for idempotency
        pass

    @staticmethod
    async def get_dashboard_snapshot():
        """Get historical data for initial dashboard load."""
        # Return last 30 minutes of 1-minute aggregates
        pass

    @staticmethod
    def cleanup_expired_partitions(days=7):
        """Drop PostgreSQL partitions older than retention period."""
        pass
```

### 5. Frontend Dashboard

#### 5.1 Technology Choice

- **Chart.js** with the streaming plugin (`chartjs-plugin-streaming`) for real-time line charts, or **Recharts** if the project uses React.
- Vanilla WebSocket API (no Socket.IO needed -- Django Channels speaks native WebSocket).

#### 5.2 Dashboard Layout

```
+------------------------------------------------------------------+
|  Real-Time API Dashboard                        [Last 5m | 30m | 1h]  |
+------------------------------------------------------------------+
|                                                                    |
|  Request Rate (req/s)           |  Error Rate (%)                  |
|  [===== live line chart =====]  |  [===== live line chart =====]  |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  Response Time (ms)             |  Top Endpoints (table)           |
|  [== p50/p95/p99 chart ====]   |  /api/users    120ms  2.1%      |
|                                 |  /api/orders   340ms  0.5%      |
|                                 |  /api/auth     45ms   8.3%      |
+------------------------------------------------------------------+
```

#### 5.3 WebSocket Client

```javascript
// dashboard/static/dashboard/js/ws-client.js
class DashboardSocket {
    constructor(onUpdate, onSnapshot) {
        this.onUpdate = onUpdate;
        this.onSnapshot = onSnapshot;
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        this.ws = new WebSocket(`${protocol}://${window.location.host}/ws/dashboard/`);

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'snapshot') {
                this.onSnapshot(msg.data);
            } else if (msg.type === 'update') {
                this.onUpdate(msg.data);
            }
        };

        this.ws.onclose = () => {
            // Reconnect with exponential backoff
            setTimeout(() => this.connect(), this.getBackoffDelay());
        };
    }

    setFilter(path) {
        this.ws.send(JSON.stringify({ type: 'set_filter', path }));
    }

    getBackoffDelay() {
        // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
        this._retries = (this._retries || 0) + 1;
        return Math.min(1000 * Math.pow(2, this._retries - 1), 30000);
    }
}
```

### 6. AWS ECS Deployment Considerations

#### 6.1 ALB Configuration

- **WebSocket support**: AWS ALB natively supports WebSocket connections. No special configuration needed beyond ensuring the target group uses HTTP (not HTTPS -- TLS is terminated at the ALB).
- **Idle timeout**: Increase ALB idle timeout to 300 seconds (default 60s) to prevent premature WebSocket disconnects.
- **Sticky sessions**: Not required -- Django Channels uses Redis as the channel layer, so any ECS task can handle any WebSocket connection.
- **Health check path**: Add `/ws/health/` HTTP endpoint (not WebSocket) for ALB health checks.

#### 6.2 ECS Task Definition

```json
{
    "containerDefinitions": [
        {
            "name": "web",
            "command": ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"],
            "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
            "environment": [
                {"name": "REDIS_URL", "value": "redis://your-elasticache-endpoint:6379/0"}
            ]
        }
    ]
}
```

**Key decisions:**

- Use **Daphne** (or Uvicorn with `--ws websockets`) as the ASGI server instead of Gunicorn, since Gunicorn cannot handle WebSocket connections.
- If the existing deployment uses Gunicorn for HTTP, you have two options:
  1. **Replace Gunicorn with Daphne/Uvicorn** for all traffic (simpler).
  2. **Run two ECS services**: one with Gunicorn for HTTP, one with Daphne for WebSocket, with ALB path-based routing (`/ws/*` -> Daphne service).

#### 6.3 Redis (ElastiCache)

- Provision an ElastiCache Redis cluster (single node is fine for channel layer use).
- Redis is used only as a message broker for Django Channels (pub/sub), not for data persistence.
- Memory requirements are minimal: a `cache.t3.micro` instance is sufficient for up to ~10,000 concurrent WebSocket connections.

#### 6.4 Scaling

- WebSocket connections are long-lived. ECS auto-scaling based on CPU/memory still works, but consider also scaling on `ActiveConnectionCount` from the ALB.
- Each Daphne worker handles many concurrent WebSocket connections (thousands per process).
- The broadcast ticker (Celery beat) should run on exactly one instance. Use a Celery beat lock (e.g., `django-celery-beat` with database scheduler) to prevent duplicate ticks.

### 7. Dependencies

```
# requirements.txt additions
channels>=4.0,<5.0
channels-redis>=4.1,<5.0
daphne>=4.0,<5.0
celery>=5.3,<6.0
redis>=5.0,<6.0
```

### 8. Implementation Plan

#### Phase 1: Data Collection (Estimated: 2-3 days)
- [ ] Create `dashboard` Django app
- [ ] Define `ApiMetricsRaw` and `ApiMetricsAggregate` models
- [ ] Create PostgreSQL migration with table partitioning
- [ ] Implement `MetricsMiddleware`
- [ ] Implement `record_metric` Celery task
- [ ] Write unit tests for middleware and metric recording

#### Phase 2: Aggregation Pipeline (Estimated: 2 days)
- [ ] Implement `MetricsService.compute_live_metrics()` with raw SQL
- [ ] Implement `MetricsService.rollup_to_aggregates()` for 1-min and 5-min buckets
- [ ] Implement `MetricsService.cleanup_expired_partitions()`
- [ ] Set up Celery beat schedule (5s broadcast, 1min rollup, daily cleanup)
- [ ] Write tests for aggregation accuracy

#### Phase 3: WebSocket Layer (Estimated: 2-3 days)
- [ ] Install and configure Django Channels with Redis channel layer
- [ ] Convert from WSGI to ASGI (update `asgi.py`, settings)
- [ ] Implement `DashboardConsumer` with group broadcast
- [ ] Implement `aggregate_and_broadcast` task
- [ ] Add WebSocket authentication (reuse existing session/JWT auth)
- [ ] Write integration tests for WebSocket consumer

#### Phase 4: Frontend Dashboard (Estimated: 3-4 days)
- [ ] Create dashboard template and static files
- [ ] Implement WebSocket client with reconnection logic
- [ ] Build request rate chart (live line chart)
- [ ] Build error rate chart (live line chart with threshold line)
- [ ] Build response time chart (p50/p95/p99 bands)
- [ ] Build top endpoints table (sortable)
- [ ] Add time range selector (5m, 30m, 1h)
- [ ] Add endpoint filter dropdown

#### Phase 5: AWS ECS Deployment (Estimated: 2 days)
- [ ] Provision ElastiCache Redis instance
- [ ] Update ECS task definition to use Daphne/Uvicorn ASGI server
- [ ] Configure ALB idle timeout for WebSocket support
- [ ] Add ALB path-based routing if running separate HTTP/WS services
- [ ] Update Celery worker task definition with beat schedule
- [ ] Add health check endpoint
- [ ] Load test WebSocket connections

#### Phase 6: Hardening (Estimated: 1-2 days)
- [ ] Add rate limiting on WebSocket connections
- [ ] Add connection count monitoring/alerting
- [ ] Verify partition cleanup works correctly
- [ ] Performance test metric recording under load
- [ ] Add dashboard access permission checks
- [ ] Document runbook for operations team

**Total estimated effort: 12-16 days**

### 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| High metric write volume degrades API latency | High | Async writes via Celery; batch inserts at scale |
| PostgreSQL query load from live aggregation | Medium | Pre-aggregated tables; index on timestamp; partition pruning |
| WebSocket connections exhausting ECS task memory | Medium | Connection limits per task; auto-scaling on connection count |
| WSGI-to-ASGI migration breaks existing endpoints | High | Thorough integration testing; Daphne handles HTTP too |
| Redis channel layer becomes SPOF | Medium | ElastiCache Multi-AZ; graceful degradation (dashboard shows stale data) |
| Celery beat duplicate ticks cause double broadcasts | Low | Use database-backed scheduler with locking |

### 10. Open Questions

1. Should we use PostgreSQL's `pg_partman` extension for automatic partition management, or handle it manually in the cleanup task?
2. Do we want to expose per-endpoint drill-down views, or keep it to aggregate metrics only?
3. Should the dashboard be a separate SPA served from a CDN, or a Django template served by the same application?
4. Is there an existing Celery setup, or does this need to be added from scratch?
5. Do we need to support multiple simultaneous dashboard viewers with different time range selections, or is a single shared broadcast sufficient?

---

That's the full spec. The core architecture is straightforward: middleware captures metrics into PostgreSQL, a periodic task aggregates and broadcasts via Django Channels, and a frontend renders live charts over a WebSocket connection.

The biggest architectural decision is whether to replace Gunicorn with an ASGI server for all traffic or run a separate WebSocket service. I'd recommend starting with a single Daphne/Uvicorn service (option 1) for simplicity, since ASGI servers handle HTTP perfectly well, and split later only if you hit scaling issues.

Want me to start implementing any of these phases, or do you want to refine the spec first?
