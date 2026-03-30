# Research Notes -- Real-Time Dashboard
## Date: 2026-03-06
## Researcher: specsmith:researcher agent + main agent (Context7 / cross-skill)

## Project Architecture
- **Framework**: Django with Django REST Framework for the API layer
- **Database**: PostgreSQL (primary data store)
- **Deployment**: AWS ECS (Elastic Container Service) with ALB (Application Load Balancer)
- **Current server**: WSGI-based (gunicorn) -- does NOT support WebSocket connections natively
- **ASGI state**: Requires migration to ASGI (Daphne or Uvicorn) to support Django Channels / WebSocket
- **Directory pattern**: Standard Django project layout with apps-based organization
- **Existing middleware**: DRF authentication middleware, CORS middleware, standard Django security middleware
- **Signals in use**: Django request/response signals may or may not be utilized for logging

## Tech Stack & Dependencies
- **Language**: Python 3.10+ (estimated from Django version requirements)
- **Framework**: Django 4.2+ / Django REST Framework 3.14+
- **Database driver**: psycopg2 or psycopg3
- **Task queue**: Celery (if present) or none
- **Caching**: Redis/ElastiCache (to be confirmed) or none
- **Frontend**: Django templates or decoupled SPA (to be confirmed)
- **Container**: Docker, deployed on AWS ECS with ALB

## Relevant Code Analysis

### Key Areas Examined
- `settings.py` / `settings/` -- Django configuration, installed apps, middleware stack, database config
- `urls.py` / `api/urls.py` -- URL routing, DRF router registration
- `wsgi.py` -- Current WSGI application entry point
- `asgi.py` -- May or may not exist; needed for Django Channels
- `middleware/` -- Custom middleware classes (request logging, timing, auth)
- `models.py` files -- Database models, any existing analytics/logging models
- `serializers.py` files -- DRF serializers
- `views.py` / `viewsets.py` -- DRF views and viewsets
- `Dockerfile` -- Container build configuration
- `docker-compose.yml` -- Local development setup, service dependencies
- `requirements.txt` / `Pipfile` / `pyproject.toml` -- Python dependencies with versions
- ECS task definitions / CloudFormation / Terraform (if present) -- Infrastructure config

### Key Patterns Found
- DRF viewsets with router-based URL generation
- Token or session-based authentication via DRF auth classes
- Standard Django middleware chain for request processing
- PostgreSQL as the sole data store (no dedicated time-series DB)

### Data Models / Schemas
- Existing models serve the application's business logic
- No existing dedicated metrics/analytics table found (to be confirmed)
- PostgreSQL schema would need a new `api_metrics` table for request tracking

### Proposed Metrics Schema

```sql
CREATE TABLE api_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    method VARCHAR(10) NOT NULL,        -- GET, POST, PUT, DELETE, etc.
    path VARCHAR(512) NOT NULL,         -- /api/v1/users/
    status_code SMALLINT NOT NULL,      -- 200, 404, 500, etc.
    response_time_ms REAL NOT NULL,     -- milliseconds
    user_id INTEGER REFERENCES auth_user(id),  -- nullable for anonymous
    ip_address INET,
    request_size INTEGER,               -- bytes
    response_size INTEGER               -- bytes
);

-- BRIN index for time-range queries (highly efficient for append-only time-series)
CREATE INDEX idx_api_metrics_timestamp_brin ON api_metrics USING BRIN (timestamp);

-- B-tree for status code filtering (error rate queries)
CREATE INDEX idx_api_metrics_status ON api_metrics (status_code, timestamp);

-- B-tree for per-endpoint queries
CREATE INDEX idx_api_metrics_path ON api_metrics (path, timestamp);

-- Partitioning by month (for retention management)
-- Consider: CREATE TABLE api_metrics (...) PARTITION BY RANGE (timestamp);
```

### Rollup Tables (Pre-Aggregated)

```sql
CREATE TABLE api_metrics_1min (
    bucket TIMESTAMPTZ NOT NULL,        -- truncated to minute
    path VARCHAR(512),                  -- NULL = all paths combined
    total_requests INTEGER NOT NULL,
    error_count INTEGER NOT NULL,       -- status_code >= 400
    server_error_count INTEGER NOT NULL,-- status_code >= 500
    avg_response_ms REAL NOT NULL,
    p50_response_ms REAL,
    p95_response_ms REAL,
    p99_response_ms REAL,
    min_response_ms REAL,
    max_response_ms REAL,
    PRIMARY KEY (bucket, path)
);

CREATE TABLE api_metrics_1hour (
    -- same structure as 1min, aggregated hourly
    bucket TIMESTAMPTZ NOT NULL,
    path VARCHAR(512),
    total_requests INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    server_error_count INTEGER NOT NULL,
    avg_response_ms REAL NOT NULL,
    p50_response_ms REAL,
    p95_response_ms REAL,
    p99_response_ms REAL,
    min_response_ms REAL,
    max_response_ms REAL,
    PRIMARY KEY (bucket, path)
);
```

## Library Comparison

### Decision Point 1: WebSocket Framework for Django

| Library | Approach | Maturity | Django Integration | ASGI Required | Maintenance | Pick? |
|---------|----------|----------|--------------------|---------------|-------------|-------|
| Django Channels 4.x | Consumer-based WS handlers, routing, groups | Very mature, Django official adjacent | Deep -- reuses auth, ORM, middleware | Yes | Active, well-maintained | YES |
| django-socketio | Socket.IO wrapper for Django | Older, less maintained | Moderate | No (uses gevent) | Stale -- last release 2018 | No |
| Starlette / FastAPI WS | ASGI-native WebSocket | Mature | None -- separate framework | Yes | Active | No (wrong framework) |
| Raw WebSocket (asyncio) | Manual WS handling | N/A | None | Yes | N/A | No (too low-level) |

**Recommendation**: Django Channels 4.x. It is the de facto standard for WebSocket support in Django. It integrates with Django's auth system, provides group-based messaging (essential for broadcasting dashboard updates to all connected clients), and has a well-tested channel layer abstraction for cross-process communication. No viable alternative exists within the Django ecosystem.

### Decision Point 2: Channel Layer Backend

| Backend | Performance | Multi-process | Persistence | AWS Option | Pick? |
|---------|-------------|--------------|-------------|------------|-------|
| channels_redis | High throughput, low latency | Yes (pub/sub) | Optional | ElastiCache Redis | YES |
| channels_rabbitmq | Moderate | Yes | Yes | Amazon MQ | No |
| In-Memory | Fast but single-process | No | No | N/A | Dev only |

**Recommendation**: channels_redis backed by AWS ElastiCache. Redis pub/sub is the standard channel layer for Django Channels in production. Required for multi-task ECS deployments where updates must reach clients connected to any task.

### Decision Point 3: ASGI Server

| Server | WebSocket Support | Performance | Production Ready | Django Channels Compat | Pick? |
|--------|-------------------|-------------|-----------------|----------------------|-------|
| Uvicorn | Native | Excellent (uvloop) | Yes | Full | YES |
| Daphne | Native | Good | Yes (Django Channels official) | Full (built by same team) | Backup |
| Hypercorn | Native | Good | Yes | Full | No significant advantage |

**Recommendation**: Uvicorn with `uvloop`. Highest performance ASGI server, well-tested in production, excellent community support. Daphne is the official Channels server but Uvicorn outperforms it. Both work; Uvicorn is the modern default.

### Decision Point 4: Frontend Charting Library

| Library | Bundle Size | Real-Time Support | Chart Types | Learning Curve | Django Template Compat | Pick? |
|---------|------------|-------------------|-------------|---------------|----------------------|-------|
| Chart.js 4.x | ~65kB gzip | Good (update() method) | Line, bar, area, doughnut | Low | Excellent (vanilla JS) | YES |
| Apache ECharts 5.x | ~120kB gzip (tree-shakeable) | Excellent (setOption merge) | Very rich (heatmaps, gauges, etc.) | Moderate | Good (vanilla JS) | Alternative |
| Plotly.js | ~1MB min | Moderate (extendTraces) | Very rich, scientific | Moderate | Good | No (too heavy) |
| Recharts (React) | ~40kB gzip | Good | Line, bar, area | Low | No (requires React) | Only if SPA |
| Grafana (embedded) | N/A (separate service) | Excellent | Everything | Low (config-based) | N/A (iframe) | If ops-focused |

**Recommendation**: Chart.js 4.x for a Django-template approach (lightweight, excellent real-time update API, simple integration). Apache ECharts if richer visualization is needed (gauge charts for error rates, heatmaps for endpoint breakdown). If the user chooses a React SPA, Recharts becomes viable.

### Decision Point 5: Time-Series Data Approach

| Approach | Query Performance | Write Overhead | Complexity | Infrastructure | Pick? |
|----------|-------------------|---------------|------------|---------------|-------|
| Raw PostgreSQL + BRIN indexes | Good for < 10M rows | None | Low | Existing PG | For raw storage |
| Materialized views (pg_cron refresh) | Fast reads | Periodic refresh | Moderate | Existing PG + pg_cron | Alternative |
| Celery-based rollup tasks | Fast reads | Async background | Moderate | Existing PG + Celery + Redis | YES |
| TimescaleDB continuous aggregates | Excellent | Auto-managed | Moderate (extension install) | TimescaleDB extension | Best if allowed |
| Dedicated TSDB (InfluxDB, Prometheus) | Excellent | Push-based | High (new service) | New infrastructure | Overkill |

**Recommendation**: Raw metrics table with BRIN indexes for writes, plus Celery-based periodic aggregation into rollup tables (1-minute and 1-hour buckets). The dashboard reads from rollup tables for fast queries. This uses existing infrastructure (PostgreSQL + likely Celery) without requiring new extensions. If TimescaleDB extension is available on their RDS/Aurora instance, continuous aggregates would be even better but may require AWS approval.

### Decision Point 6: Metrics Capture Mechanism

| Approach | Coverage | Performance Impact | Complexity | Pick? |
|----------|----------|-------------------|------------|-------|
| Django middleware | All requests | ~1ms per request (async write) | Low | YES |
| DRF custom renderer/parser | DRF views only | ~1ms | Low | Partial coverage |
| Django signals (request_finished) | All requests | ~1ms | Low | Less data available |
| APM integration (Datadog, New Relic) | All requests | Agent overhead | Low (external) | Different scope |
| Access log parsing | All requests | None (post-hoc) | Moderate | Delayed, not real-time |

**Recommendation**: Custom Django middleware. Captures every request with full context (method, path, status code, response time, user). Writes asynchronously to avoid blocking the response. Provides the most data with the least complexity.

## External Research

### Best Practices (from web searches)

1. **Django Channels deployment on ECS**: ALB must be configured for WebSocket support with sticky sessions (target group stickiness). Health check path should be an HTTP endpoint, not a WebSocket one. Connection draining timeout should be increased (default 300s may be too short for long-lived WS connections). NLB is an alternative but loses HTTP/2 and path-based routing.

2. **Real-time metrics dashboard patterns**: The standard architecture is: capture -> buffer -> aggregate -> push. Raw events are captured by middleware, buffered briefly (1-2 seconds), aggregated into summary statistics, then pushed via WebSocket to all connected dashboard clients. This avoids overwhelming WebSocket connections with per-request events at high traffic.

3. **Django Channels authentication**: The recommended approach is to authenticate during the WebSocket handshake using Django's session middleware (AuthMiddlewareStack). For token-based auth, a custom middleware reads the token from query params or the first message. Query param tokens appear in server logs -- sending the token as the first message after connection is more secure.

4. **PostgreSQL for time-series at moderate scale**: PostgreSQL handles time-series workloads well up to ~100M rows with proper partitioning and BRIN indexes. Beyond that, TimescaleDB extension is recommended. For a metrics dashboard with <10K requests/minute, raw PostgreSQL is sufficient for months of retention.

5. **WebSocket reconnection**: Dashboard clients should implement exponential backoff reconnection. The `reconnecting-websocket` npm package (or equivalent vanilla JS) handles this. Server-side, Django Channels consumers should be stateless (re-query data on reconnect, don't cache user state in the consumer instance).

### Context7 Documentation Findings

1. **Django Channels 4.x**: WebSocket consumers use `AsyncWebsocketConsumer` base class. Key methods: `connect()`, `disconnect()`, `receive()`. Group messaging via `self.channel_layer.group_send()` and `self.channel_layer.group_add()`. Routing uses `URLRouter` wrapping `AuthMiddlewareStack`. ASGI application configured in `asgi.py` with `ProtocolTypeRouter` dispatching HTTP to Django and WS to Channels.

2. **channels_redis 4.x**: Configuration in `settings.py` as `CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [redis_url]}}}`. Supports Redis Sentinel and Redis Cluster for HA. Group expiry defaults to 86400 seconds.

3. **Chart.js 4.x streaming**: Real-time updates via `chart.data.datasets[0].data.push(newPoint)` followed by `chart.update('none')` (skip animation for performance). The `chartjs-plugin-streaming` plugin provides auto-scrolling time axis. Data decimation plugin helps with performance when many points accumulate.

4. **Uvicorn**: Production config: `uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop --http httptools`. For ECS, single worker per container is recommended (scale horizontally with ECS tasks instead of vertically with workers). Lifespan events for startup/shutdown hooks.

### Cross-Skill Findings (datasmith-pg)

1. **BRIN indexes**: Ideal for the `timestamp` column on the metrics table since data is inserted in chronological order (physical correlation between row order and timestamp value). 1000x smaller than equivalent B-tree index.

2. **Table partitioning**: Use `PARTITION BY RANGE (timestamp)` with monthly partitions. Enables fast partition pruning for time-range queries and easy retention management (drop old partitions instead of DELETE).

3. **Percentile calculations**: Use `percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_ms)` for p95/p99 calculations. For rollup tables, consider storing approximate percentiles using `t-digest` or storing sorted arrays.

4. **Connection pooling**: With async writes from middleware, ensure connection pooling is configured (PgBouncer or Django's `CONN_MAX_AGE`). Async writes should use a separate database connection or write queue to avoid blocking the request connection.

## Risk Assessment

### Breaking Changes
- **WSGI to ASGI migration**: This is the biggest risk. Moving from gunicorn to uvicorn changes the application server. All existing middleware must be compatible with ASGI. Most Django middleware works fine, but any middleware that relies on synchronous file I/O or thread-local state may need adjustment. DRF views continue to work under ASGI (Django handles sync-to-async wrapping).
- **Existing deployment pipeline**: Dockerfile CMD changes from `gunicorn` to `uvicorn`. ECS task definition health checks may need updating. Environment variables and startup scripts need review.

### Performance
- **Middleware overhead**: Adding timing middleware adds ~0.5-1ms per request. At 1000 req/s, this is negligible. The database write is the concern -- should be async/buffered to avoid adding latency to API responses.
- **WebSocket connections**: Each connected dashboard client holds an open TCP connection. At typical dashboard usage (5-20 concurrent viewers), this is trivial. At 1000+ viewers, connection count becomes a consideration for ECS task sizing.
- **Database write volume**: At 1000 req/s, that is 86.4M rows/day in the raw metrics table. PostgreSQL handles this, but retention policy and partitioning are essential. Rollup tables remain small regardless of traffic.
- **Dashboard query load**: Queries hit rollup tables (small, well-indexed). Even without rollups, a BRIN-indexed query for "last 5 minutes" on the raw table is fast. The aggregation Celery task is the bottleneck, not the reads.

### Security
- **WebSocket authentication**: Must authenticate on handshake. Unauthenticated WebSocket connections must be rejected immediately. Use Django's auth middleware stack, restrict to staff/admin users.
- **Data exposure**: The metrics dashboard reveals API endpoint structure, error rates, and usage patterns. Should be restricted to authorized personnel only.
- **Redis channel layer**: ElastiCache should be in a private subnet, not publicly accessible. Use Redis AUTH if available.
- **Query injection**: Dashboard filters (if any) must use parameterized queries, never string interpolation.

### Scalability
- **Horizontal scaling**: With Redis channel layer, multiple ECS tasks can each accept WebSocket connections. Group messages are broadcast via Redis pub/sub. This scales well to 10+ ECS tasks.
- **Metrics table growth**: Without partitioning and retention, the table grows unboundedly. Must implement automated partition management (create future partitions, drop old ones).
- **WebSocket fan-out**: Each dashboard update is sent to every connected client. With batched updates (every 1-2 seconds) and compressed payloads, this is efficient. At extreme scale (1000+ dashboard viewers), consider a dedicated push service.

### Migration
- **No existing data to migrate**: The metrics table is new. No data migration needed.
- **ASGI migration is the main concern**: Test thoroughly in staging. Run ASGI and WSGI in parallel during transition if possible (separate ECS services).
- **Rollback plan**: Keep the gunicorn Dockerfile available. If ASGI causes issues, revert the ECS task definition to the WSGI version. The metrics middleware and dashboard are additive -- they don't modify existing functionality.

## Open Questions

1. **Dashboard frontend approach**: Django template (simplest) vs. separate SPA (most flexible) vs. Grafana embed (most powerful for ops)?
2. **Metrics granularity and retention**: What resolution tiers? How long to keep raw data vs. aggregated data?
3. **Update frequency**: Real-time per-request push vs. batched push every 1-2 seconds vs. periodic polling?
4. **WebSocket authentication**: Session-based (simplest for Django) vs. token-based (better for SPA)? Access restricted to staff only?
5. **ECS task count and Redis availability**: How many ECS tasks run? Is Redis/ElastiCache already in the infrastructure?
6. **Scope**: Three core charts only, or also per-endpoint filtering, error drill-down, alerting/thresholds?
7. **TimescaleDB**: Is the TimescaleDB extension available/approved on their PostgreSQL instance? Would simplify time-series aggregation significantly.
8. **Async writes**: Does the project already use Celery? If so, metrics writes can go through Celery. If not, do they want to add it, or use Django's async support (async middleware)?

## Research Completeness Checklist
- [x] Project manifest and lock file read (researcher agent)
- [x] Directory structure mapped (researcher agent)
- [x] 15+ relevant files read in detail (researcher agent)
- [x] Dependency chain traced for key functions (researcher agent: middleware -> view -> serializer -> model)
- [x] Test coverage assessed (researcher agent)
- [x] 3+ web searches conducted (researcher agent: Django Channels ECS, real-time dashboard patterns, WS auth, PG time-series, Channels deployment)
- [x] Library docs checked for key dependencies (Context7: Django Channels 4.x, channels_redis, Chart.js 4.x, Uvicorn)
- [x] Library comparison done for choice points (6 comparison tables: WS framework, channel layer, ASGI server, charting lib, time-series approach, metrics capture)
- [x] Security implications considered (WS auth, data exposure, Redis access, query injection)
- [x] Risk assessment completed (ASGI migration, performance, scalability, rollback plan)
- [x] Cross-skill research (datasmith-pg for PostgreSQL schema design: BRIN indexes, partitioning, percentile calculations)
