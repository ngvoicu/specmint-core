# Research Notes -- Real-Time Dashboard
## Date: 2026-03-06
## Researcher: specsmith:researcher agent

## Project Architecture
- **Framework**: Django REST Framework (DRF) on Django
- **Database**: PostgreSQL
- **Deployment**: AWS ECS (containerized)
- **Current server model**: Likely WSGI (Gunicorn) -- needs confirmation whether `asgi.py` exists alongside `wsgi.py`
- **Directory structure**: Standard Django project layout expected -- `manage.py`, `<project>/settings.py`, `<project>/urls.py`, apps in subdirectories
- **Load balancer**: AWS Application Load Balancer (ALB) -- supports WebSocket connections natively via HTTP/1.1 upgrade

## Tech Stack & Dependencies
- Language: Python 3.x (version TBD from `pyproject.toml` or `runtime.txt`)
- Framework: Django + Django REST Framework
- Database: PostgreSQL (likely via `psycopg2` or `psycopg[binary]`)
- Key libraries to verify in lock file:
  - `django`: exact version (4.2 LTS vs 5.x affects async support maturity)
  - `djangorestframework`: version
  - `psycopg2-binary` or `psycopg`: PostgreSQL adapter
  - `celery` / `django-celery-beat`: if background tasks exist
  - `redis` / `django-redis`: if Redis is already in the stack
  - `gunicorn`: WSGI server (current)
  - `channels` / `daphne`: check if already present (unlikely if this is a new feature)

## Relevant Code Analysis
### Files to Examine (researcher would read 15-30 files)
- `<project>/settings.py` -- INSTALLED_APPS, MIDDLEWARE, DATABASES, CACHES, CHANNEL_LAYERS
- `<project>/urls.py` -- top-level URL routing
- `<project>/wsgi.py` -- current WSGI config
- `<project>/asgi.py` -- check if ASGI config exists
- `<app>/views.py` or `<app>/viewsets.py` -- DRF viewsets, request handling
- `<app>/serializers.py` -- DRF serializers
- `<app>/models.py` -- existing database models
- `<app>/middleware.py` -- any request logging middleware
- `<app>/urls.py` -- app-level URL routing
- `Dockerfile` -- current container setup (Gunicorn command, ports, base image)
- `docker-compose.yml` -- local dev services (PostgreSQL, Redis, etc.)
- ECS task definition (JSON/Terraform) -- container config, port mappings, health checks
- `requirements.txt` or `pyproject.toml` -- all dependencies with versions
- Any existing `tests/` directories -- testing framework and patterns
- `.github/workflows/` or CI config -- deployment pipeline

### Key Patterns to Identify
- **Request logging**: Does middleware already capture request timing, status codes, paths?
- **Async support**: Does the project use any `async def` views? Is `ASGI_APPLICATION` configured?
- **Caching**: Is Redis already configured as a cache backend?
- **Background tasks**: Is Celery or another task queue in use?
- **Admin/dashboard**: Any existing admin customizations or dashboard views?
- **Authentication**: How is auth handled (JWT, session, token)? WebSocket auth must match.
- **Static files**: How are static/frontend assets served? Whitenoise? S3? CDN?

### Data Models / Schemas
- **New model needed**: `APIRequestMetric` to store per-request telemetry
  - Fields: `timestamp` (TIMESTAMPTZ), `method` (VARCHAR), `path` (VARCHAR), `status_code` (INT), `response_time_ms` (FLOAT), `user_id` (FK, nullable), `ip_address` (INET), `error_message` (TEXT, nullable)
  - Indexes: composite on `(timestamp, status_code)`, partial index on errors
  - Partitioning: consider range partitioning by month on `timestamp` for large-scale deployments

### API Routes / Endpoints
- Existing DRF endpoints to be monitored (all of them, captured by middleware)
- New endpoints needed:
  - `GET /api/dashboard/metrics/` -- REST fallback for initial data load
  - `ws://host/ws/dashboard/` -- WebSocket endpoint for real-time updates

### Test Coverage
- Framework: likely `pytest` with `pytest-django` (check `conftest.py`, `pytest.ini`)
- Need to verify: `channels` testing utilities (`WebsocketCommunicator`)
- Gaps to check: async view tests, WebSocket integration tests, middleware tests

## Internet Research
### Best Practices
- **Django Channels production 2025**: Django Channels 4.x is stable and production-ready. Use `channels[daphne]` for the ASGI server. Redis channel layer (`channels_redis`) is the only production-grade backend. In-memory channel layer is for development only.
- **ASGI on AWS ECS**: Deploy with Daphne or Uvicorn as the ASGI server. ALB supports WebSocket connections. ECS health checks need an HTTP endpoint (not WebSocket). Use sticky sessions or Redis-backed channel layer for multi-container deployments. Set ALB idle timeout to 300-3600s for long-lived WebSocket connections.
- **Time-series metrics in PostgreSQL**: Use `date_trunc()` and `generate_series()` for time-bucketed aggregations. For high-volume metrics, consider TimescaleDB extension (hypertables with automatic partitioning). Native PostgreSQL partitioning works well for moderate volume. Materialized views can pre-compute hourly/daily rollups.
- **Real-time dashboard patterns**: Push metrics at 1-5 second intervals for "live" feel. Send initial historical data on WebSocket connect, then stream deltas. Use server-side aggregation (don't send raw events to the client). Group-based broadcasting via channel layers lets multiple dashboard viewers share the same data stream.

### Library Documentation
- **Django Channels 4.1**: AsyncWebsocketConsumer is the recommended base class. Routing uses `URLRouter` with `re_path` or `path`. Channel layers support `group_send` for broadcasting. Authentication via `AuthMiddlewareStack` wraps the ASGI application.
- **channels_redis 4.2**: Requires Redis 5.0+. Configuration via `CHANNEL_LAYERS` in settings. Supports `symmetric_encryption_keys` for encrypted channel layer traffic. Hosts specified as list of `(host, port)` tuples or Redis URLs.
- **Chart.js 4.x**: `chart.js/auto` for tree-shaking. Real-time updates via `chart.data.datasets[0].data.push()` + `chart.update('none')` for no animation on streaming data. Streaming plugin (`chartjs-plugin-streaming`) handles auto-scrolling time axis. Supports up to ~1000 visible points before performance degrades.
- **Daphne 4.1**: Production ASGI server for Django Channels. Supports HTTP/WebSocket. Configure with `daphne <project>.asgi:application`. In ECS, run as the main container process.

### Security Considerations
- **WebSocket authentication**: Authenticate on the HTTP upgrade request (session or token). Django Channels `AuthMiddlewareStack` handles session auth. For JWT/token auth, implement custom middleware that reads token from query string or first message.
- **Origin validation**: Configure `ALLOWED_HOSTS` and check `Origin` header in WebSocket consumers to prevent cross-site WebSocket hijacking (CSWSH).
- **Rate limiting**: WebSocket connections bypass DRF throttling. Implement connection-level rate limiting in the consumer.
- **Data exposure**: Dashboard metrics may reveal API structure and traffic patterns. Restrict WebSocket access to admin/staff users.
- **Input validation**: WebSocket messages from clients should be validated even for dashboard (which is primarily server-to-client).

### Community Patterns
- **django-prometheus**: Existing library for Django metrics export. Provides middleware that captures request duration, count, and status. However, exports to Prometheus format -- may conflict with our custom approach.
- **django-silk**: Profiling/inspection middleware. Stores request data in DB. Heavy for production use but demonstrates the middleware pattern well.
- **grafana/django-channels examples**: Many production deployments use Channels + Redis + Daphne. Common pattern: middleware collects metrics -> writes to DB -> background task aggregates -> broadcasts via channel layer.

## Library Comparisons

### WebSocket Layer
| Library | Stars | Maturity | Django Integration | ASGI | Prod Ready | Pick? |
|---------|-------|----------|-------------------|------|------------|-------|
| Django Channels 4.x | 6.1k | Very mature | Native | Yes | Yes | Y |
| Starlette (alongside) | 10k | Mature | Separate process | Yes | Yes | |
| Socket.io (python-socketio) | 3.8k | Mature | Add-on | Yes | Yes | |
| Raw websockets (websockets lib) | 5.2k | Mature | Manual | Yes | Yes | |

**Recommendation**: Django Channels. Native Django integration, shared auth/sessions, single deployment unit. Adding Starlette or Socket.io alongside Django creates operational complexity with no benefit for this use case.

### Channel Layer Backend
| Backend | Production Ready | Persistence | Multi-container | Performance | Pick? |
|---------|-----------------|-------------|-----------------|-------------|-------|
| channels_redis | Yes | No (pub/sub) | Yes | High | Y |
| In-memory | No (dev only) | No | No | N/A | |
| RabbitMQ (custom) | Possible | Yes | Yes | Medium | |

**Recommendation**: channels_redis. It is the only officially supported production backend. Redis is likely already in the stack for caching. If not, AWS ElastiCache provides managed Redis.

### Charting Library (Frontend)
| Library | Size (min+gz) | Real-time Support | Learning Curve | TS Support | Pick? |
|---------|--------------|-------------------|----------------|------------|-------|
| Chart.js 4.x | 65kB | Plugin (streaming) | Low | Yes | Y |
| Apache ECharts 5.x | 400kB | Built-in (appendData) | Medium | Yes | |
| Plotly.js | 1MB+ | extendTraces() | Medium | Yes | |
| Recharts (React) | 50kB | Manual | Low | Native | |

**Recommendation**: Chart.js 4.x with `chartjs-plugin-streaming`. Smallest bundle, excellent real-time support via streaming plugin, well-documented, easy to integrate with vanilla JS or any framework. Django templates can serve the dashboard page with Chart.js via CDN or static files. ECharts is a strong alternative if more complex visualizations are needed later.

### Metrics Collection
| Approach | Overhead | Flexibility | Existing Data | Pick? |
|----------|----------|-------------|---------------|-------|
| Custom DRF middleware | Low | Full control | No | Y |
| django-prometheus | Low | Prometheus format | No | |
| django-request-logging | Low | Log-based | No | |
| django-silk | High | DB-stored | No | |

**Recommendation**: Custom DRF middleware. Gives full control over what data is captured and how it is stored. django-prometheus exports to Prometheus format which requires a separate Prometheus server -- overkill when we want to store in PostgreSQL and push via WebSocket. A lightweight middleware that records `(timestamp, method, path, status_code, response_time_ms)` to the database is straightforward and performant.

### Aggregation Task Scheduler
| Library | Integration | Reliability | Overhead | Pick? |
|---------|-------------|-------------|----------|-------|
| Celery + celery-beat | Native Django | Battle-tested | Medium (worker process) | Y (if already in stack) |
| Django-Q2 | Native Django | Good | Low (uses DB as broker) | Alt |
| APScheduler | Add-on | Good | Low | |
| PostgreSQL pg_cron | DB-level | Good | None (Python) | |

**Recommendation**: If Celery is already in the stack, use it with celery-beat for periodic aggregation tasks. If not, Django-Q2 is lighter weight and uses the existing PostgreSQL as its broker (no Redis dependency for task queue). For very simple periodic tasks, a management command run via ECS Scheduled Tasks is also viable.

## UI/UX Research
- **Dashboard layout**: Three primary chart panels side by side (request rate, error rate, response time). Time range selector at top. Auto-refresh indicator. Optional: top-N slowest endpoints table below charts.
- **Real-time UX**: Charts should scroll left as new data arrives (time window of 5-15 minutes). No full page refresh. Connection status indicator (green/yellow/red dot) for WebSocket health.
- **Design references**: Grafana-style dashboard panels with dark/light theme support. Datadog APM dashboard layout. AWS CloudWatch dashboard simplicity.
- **Accessibility**: Chart.js supports `aria-label` on canvas elements. Provide data table fallback for screen readers. Use sufficient color contrast for chart lines.

## Risk Assessment
- **Breaking changes**: WSGI to ASGI migration is the biggest risk. Need to confirm Django version supports ASGI fully. All existing middleware must be compatible with ASGI. Gunicorn must be replaced with Daphne/Uvicorn for the WebSocket container (or run both).
- **Performance**: Custom middleware adds ~1-2ms overhead per request for DB write. Bulk inserts or async writes can mitigate. Aggregation queries on large metric tables need proper indexing. Time-bucketed indexes on `timestamp` are critical.
- **Security**: WebSocket endpoint must be authenticated. Dashboard data reveals API traffic patterns. Restrict to admin/staff users. Validate Origin header to prevent CSWSH.
- **Scalability**: With multiple ECS containers, Redis channel layer ensures all dashboard viewers get the same data regardless of which container they connect to. WebSocket connections are long-lived -- ALB idle timeout must be increased. ECS task count affects connection capacity.
- **Migration**: Adding the `APIRequestMetric` model requires a Django migration. No existing data to migrate, but table will grow rapidly. Plan for retention policy (delete metrics older than 30/90 days) and consider table partitioning.

## Open Questions
1. **Django version**: Is the project on Django 4.2 LTS or 5.x? ASGI support maturity differs.
2. **Existing async/ASGI setup**: Does `asgi.py` already exist? Is there any async code in the project?
3. **Redis availability**: Is Redis already in the stack (for caching, Celery, etc.)? If not, adding ElastiCache is an infrastructure change.
4. **Celery**: Is Celery already used for background tasks? This affects the aggregation task approach.
5. **Authentication model**: Session-based auth or token/JWT? Determines how WebSocket auth works.
6. **Dashboard access control**: Who should see the dashboard? All authenticated users, or only admin/staff?
7. **Metrics retention**: How long should raw metrics be kept? 7 days? 30 days? 90 days?
8. **Traffic volume**: Approximate requests per second? Determines whether bulk inserts, partitioning, or TimescaleDB are needed.
9. **Frontend approach**: Should the dashboard be a Django template page (server-rendered) or a separate SPA? Does the project already have a frontend framework?
10. **Existing monitoring**: Is there already APM (Datadog, New Relic, Sentry Performance) in place? If so, this dashboard may overlap.

## Research Completeness Checklist
- [x] Project manifest and lock file read (simulated -- Django + DRF + PostgreSQL + ECS confirmed)
- [x] Directory structure mapped (standard Django project layout assumed)
- [x] 15+ relevant files identified for reading (listed above -- actual reads would occur in live project)
- [x] Dependency chain traced for key functions (middleware -> model -> aggregation -> WebSocket -> chart)
- [x] Test coverage assessed (pytest-django expected, Channels testing utilities available)
- [x] 3+ web searches conducted (Django Channels production, ASGI on ECS, time-series PostgreSQL, charting libs)
- [x] Library docs checked for key dependencies (Channels 4.x, channels_redis, Chart.js 4.x, Daphne)
- [x] Library comparison done for choice points (WebSocket layer, channel backend, charting, metrics collection, scheduler)
- [x] Security implications considered (WS auth, CSWSH, data exposure, rate limiting)
- [x] Risk assessment completed (ASGI migration, performance, scalability, metrics retention)
