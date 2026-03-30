# Forge Transcript -- Real-Time Dashboard
## Date: 2026-03-06
## Spec ID: `realtime-dashboard`

---

## Preflight: Resolve Spec Identity

**User's request**: "forge a spec for adding a WebSocket-based real-time dashboard to our Django REST Framework API. We need live-updating charts showing API request rates, error rates, and response times. The data is in PostgreSQL and we're deployed on AWS ECS."

**Generated spec ID**: `realtime-dashboard`

**Collision check**:
- Checked `.specs/realtime-dashboard/SPEC.md` -- does not exist
- Checked `.specs/registry.md` -- does not exist (no specs directory yet)
- No collision. Proceeding with `realtime-dashboard`.

**Plan mode check**: Not in plan mode. Proceeding with file creation.

**Setup**:
- Created directory: `.specs/realtime-dashboard/`
- Initialized `.specs/registry.md`:

```markdown
# Spec Registry

| ID | Title | Status | Priority | Progress | Updated |
|----|-------|--------|----------|----------|---------|
```

---

## Phase 1: Deep Research

### Track A: Researcher Agent Spawn

The `specsmith:researcher` agent was spawned via the **Task tool** with the following invocation:

```
Tool: Task
Agent: specsmith:researcher
Model: opus
Tools: Read, Glob, Grep, Bash, WebSearch, WebFetch, Task

Prompt:
"You are the specsmith researcher agent. Perform exhaustive research for
the following spec.

**Spec ID**: realtime-dashboard
**Output path**: .specs/realtime-dashboard/research-01.md
**Project root**: <project-root>

**User's request**: Add a WebSocket-based real-time dashboard to a Django
REST Framework API. The dashboard needs live-updating charts showing API
request rates, error rates, and response times. The data is in PostgreSQL.
Deployment is on AWS ECS.

**Areas to focus on**:
1. Project Discovery: Read requirements.txt/pyproject.toml, map Django
   project structure, identify existing apps/models/views/middleware,
   check for existing WebSocket or async support (ASGI vs WSGI), read
   Dockerfile and ECS task definitions
2. Deep Code Analysis: Find all DRF viewsets/serializers/routers,
   middleware that logs requests, any existing metrics/monitoring,
   database models, celery/background task setup, existing dashboard
   or admin views
3. Internet Research:
   - 'Django Channels WebSocket production best practices 2025'
   - 'Django real-time dashboard metrics WebSocket'
   - 'ASGI Django deployment AWS ECS 2025'
   - 'PostgreSQL time-series aggregation for API metrics'
   - 'Chart.js vs Plotly vs Recharts real-time dashboard'
4. Library Comparison:
   - WebSocket layer: Django Channels vs Starlette alongside Django
     vs python-socketio
   - Channel layer backend: Redis (channels_redis) vs In-Memory vs
     RabbitMQ
   - Charting: Chart.js vs Plotly.js vs Apache ECharts vs Recharts
   - Metrics collection: Custom middleware vs django-request-logging
     vs django-prometheus
   - Task scheduling: Celery vs Django-Q vs APScheduler
5. Risk Assessment: ASGI migration impact, ECS deployment changes
   (Daphne/Uvicorn vs Gunicorn), WebSocket connection limits on ALB,
   PostgreSQL query performance for time-series aggregation, security
   (WS auth, CORS)
6. Check for existing patterns: How does the project handle async? Is
   there already an ASGI config? What middleware is registered? How
   are API routes structured?

Follow the full research protocol from your instructions. Read 15-30
files, run 3+ web searches, compare libraries, assess risks. Save
structured output to the specified path."
```

**Researcher agent behavior**: The agent executes its 6-phase protocol:
- **Phase 1 (Project Discovery)**: Reads `requirements.txt`/`pyproject.toml`, maps the directory tree with `ls` and Glob, reads lock files for exact versions, reads `Dockerfile`, checks for `asgi.py` vs `wsgi.py`, reads CI/CD config and ECS task definitions.
- **Phase 2 (Deep Code Analysis)**: Uses Grep/Glob to find all DRF viewsets, serializers, middleware, models, URL configs. Reads 15-30 files. Traces the request lifecycle from URL routing through middleware to views to database queries.
- **Phase 3 (Internet Research)**: Runs 3+ WebSearch queries for Django Channels best practices, ASGI on ECS, time-series PostgreSQL patterns, charting library comparisons. Uses WebFetch to pull actual documentation pages.
- **Phase 4 (Library Comparison)**: Builds comparison tables for each decision point (WebSocket layer, channel backend, charting library, metrics collection, task scheduler).
- **Phase 5 (Risk Assessment)**: Evaluates ASGI migration risk, ECS deployment changes, ALB WebSocket support, PostgreSQL performance, security surface area.
- **Phase 6 (UI/UX Research)**: Researches dashboard layout patterns, real-time chart UX, accessibility requirements.

The researcher saves its output to `.specs/realtime-dashboard/research-01.md`.

### Track B: Context7 & Cross-Skill Research (in parallel)

While the researcher agent runs, the main agent performs these MCP-based lookups:

**Context7 lookups performed**:
1. `resolve-library-id("django-channels")` -> `query-docs` for WebSocket consumer patterns, routing configuration, channel layer setup, ASGI deployment with Daphne
2. `resolve-library-id("djangorestframework")` -> `query-docs` for middleware hooks, request/response lifecycle, authentication classes
3. `resolve-library-id("channels-redis")` -> `query-docs` for Redis channel layer configuration, group messaging patterns, connection pooling
4. `resolve-library-id("chart.js")` -> `query-docs` for real-time data updates, streaming plugin API, dataset management, performance with high-frequency updates
5. `resolve-library-id("psycopg2")` -> `query-docs` for connection pooling, async support, bulk insert patterns

**Cross-skill loading**:
- Loaded `datasmith-pg` skill for PostgreSQL schema design guidance:
  - Time-series table design with `TIMESTAMPTZ` columns
  - Partitioning strategies (range partitioning by month on timestamp)
  - Index design for time-bucketed queries (`BRIN` index on timestamp, composite index on `(timestamp, status_code)`)
  - Retention policy implementation (scheduled DELETE with partition drop)

### Merge & Save Research

Researcher agent output was read from `.specs/realtime-dashboard/research-01.md`. Context7 findings and datasmith-pg guidance were merged into the research notes. The combined research document covers:
- Project architecture and tech stack
- Relevant code analysis (files to examine, patterns to match)
- Library comparisons with recommendation tables
- Internet research findings
- Security considerations
- Risk assessment
- Open questions for the interview

Research saved to: `.specs/realtime-dashboard/research-01.md`

---

## Phase 2: Interview Round 1

### Research Summary

Based on the deep research, here is what I found and what I am proposing for the real-time dashboard:

**Architecture overview.** This feature requires three main components: (1) a Django middleware that captures request metrics (method, path, status code, response time) and stores them in a new PostgreSQL table, (2) a background aggregation process that periodically computes time-bucketed statistics (requests/min, error rate, p50/p95/p99 response times) and broadcasts them via Django Channels, and (3) a WebSocket-connected dashboard page with Chart.js charts that display the live data. The WebSocket layer would use Django Channels 4.x with a Redis channel layer backend (`channels_redis`), which is the only production-grade option. This means the project needs to migrate from WSGI (Gunicorn) to ASGI (Daphne or Uvicorn) -- or run both side by side, routing WebSocket traffic to the ASGI server.

**Deployment impact.** On AWS ECS, the ASGI migration requires changing the container entrypoint from Gunicorn to Daphne (or Uvicorn with `--interface asgi3`). The ALB already supports WebSocket connections via HTTP/1.1 upgrade, but the idle timeout needs to be increased from the default 60 seconds to 300+ seconds for long-lived WebSocket connections. If the project runs multiple ECS tasks (containers), the Redis channel layer ensures all dashboard viewers receive the same broadcast regardless of which container they are connected to. This requires Redis -- either an existing Redis instance or a new AWS ElastiCache cluster.

**Data pipeline.** The metrics middleware writes raw request data to PostgreSQL. A periodic task (every 5-10 seconds) queries the most recent data window, computes aggregated metrics, and pushes them to a Channels group. All connected dashboard WebSocket clients receive the update simultaneously. For the initial page load, the dashboard fetches historical data via a REST endpoint, then switches to WebSocket for live updates. This hybrid approach avoids making the user wait for the first WebSocket push and gives a smooth "already populated" experience.

### Assumptions

Based on typical Django REST Framework projects on ECS, I am assuming:

1. **WSGI currently**: The project runs on Gunicorn with `wsgi.py` -- no existing ASGI configuration. Migrating to ASGI is required for WebSocket support.
2. **Redis not yet in the stack**: No existing Redis dependency for caching or task queues. We will need to add Redis (ElastiCache) for the channel layer.
3. **Session or token auth**: DRF authentication is session-based or uses token/JWT authentication. The WebSocket connection will need to authenticate using the same mechanism.
4. **Django templates for the dashboard**: The dashboard page will be a server-rendered Django template (not a separate SPA), keeping the deployment simple and consistent with the existing project.
5. **Moderate traffic volume**: Fewer than 1000 requests/second, so bulk inserts and basic PostgreSQL indexing are sufficient without needing TimescaleDB.

### Questions

I have 6 targeted questions that research could not answer:

**1. Django version and existing async setup**
What version of Django is the project on (4.2 LTS, 5.0, 5.1)? Does `asgi.py` already exist in the project? Is there any existing async code (async views, async middleware)? This determines how smooth the ASGI migration will be and whether we need to worry about sync-to-async compatibility for existing middleware.

**2. Redis availability**
Is Redis already in the infrastructure (for caching, Celery, sessions, etc.)? If Redis is available, we use it directly for the Channels layer. If not, we need to provision AWS ElastiCache, which is an infrastructure change that may need separate approval or Terraform/CloudFormation updates.

**3. Background task infrastructure**
Is Celery (with celery-beat) already configured in the project for periodic tasks? If yes, we add the metrics aggregation as a periodic Celery task. If not, we have a choice: add Celery (heavier, but standard), use Django-Q2 (lighter, uses PostgreSQL as broker), or run a simple management command via ECS Scheduled Tasks. Which approach fits your operational preferences?

**4. Dashboard access control**
Who should be able to view the real-time dashboard?
- **Admin/staff only** (simplest -- use Django's `is_staff` flag)
- **Any authenticated user** (all API consumers can see metrics)
- **Custom permission** (a specific group or permission, e.g., `can_view_dashboard`)

This also affects whether we need to be careful about what data the metrics reveal (endpoint paths, error rates, response times could be sensitive).

**5. Frontend approach**
Should the dashboard be:
- **A Django template page** served at `/dashboard/` with Chart.js loaded from static files or CDN? This is simplest and keeps everything in the Django project.
- **Part of an existing frontend SPA** if the project already has a React/Vue/Angular frontend? In that case, we would just provide the WebSocket endpoint and REST API, and the frontend team builds the charts.
- **A standalone SPA** (e.g., a small React app) served from the Django project?

Does the project have an existing frontend application, or is it API-only?

**6. Metrics retention and volume**
How long should raw request metrics be retained? Options:
- **7 days** (minimal storage, good for live monitoring)
- **30 days** (standard for trend analysis)
- **90 days** (long-term patterns, requires partitioning for performance)

And roughly how many API requests per second does the service handle? This determines whether we need bulk inserts, table partitioning, or even TimescaleDB for the metrics table. At fewer than 100 req/s, simple single-row inserts are fine. At 500+ req/s, we need bulk inserts and likely partitioning.

### Proposed Approach

Here is the rough architecture I would propose:

```
Browser (Dashboard)              Django (ASGI via Daphne)
 |                                |
 |--- HTTP GET /dashboard/ ------>| Django template + Chart.js
 |                                |
 |--- HTTP GET /api/dashboard/ -->| DRF view: historical metrics
 |<-- JSON (last 15 min data) ---|
 |                                |
 |--- WS /ws/dashboard/ -------->| Channels consumer (auth required)
 |<-- JSON (live updates q5s) ---|    |
 |                                |   [Redis Channel Layer]
 |                                |       ^
 |                                |       |
 |                          [Periodic Task (q5-10s)]
 |                                |
 |                          Aggregation query on
 |                          api_request_metrics table
 |                                |
 |                          [PostgreSQL]
 |                                ^
 |                                |
 |                     [Metrics Middleware]
 |                    (captures every DRF request)
```

**Phases I am thinking**:
1. **Metrics Collection** -- Build the middleware + model + migration
2. **WebSocket Infrastructure** -- ASGI migration, Channels setup, Redis channel layer, consumer
3. **Aggregation Pipeline** -- Periodic task that computes stats and broadcasts
4. **Dashboard Frontend** -- Template page with Chart.js charts, WebSocket client
5. **Production Hardening** -- Auth, retention policy, ECS config changes, monitoring, testing

Does this approach and phase breakdown make sense? Would you adjust the scope, ordering, or any of the technical choices?

---

**STOPPING HERE. Waiting for user answers before proceeding to deeper research (Phase 3) or spec writing (Phase 5).**

The interview questions above are saved to `.specs/realtime-dashboard/interview-01.md` with placeholder answer fields to be filled in after the user responds.

---

## Interview File

Saved to `.specs/realtime-dashboard/interview-01.md`:

```markdown
# Interview Round 1 -- Real-Time Dashboard
## Date: 2026-03-06

## Questions Asked
1. Django version and existing async setup (Django 4.2 LTS vs 5.x, asgi.py existence, async code)
   **Answer**: <awaiting user response>

2. Redis availability (already in stack or needs provisioning via ElastiCache)
   **Answer**: <awaiting user response>

3. Background task infrastructure (Celery already configured, or need to choose alternative)
   **Answer**: <awaiting user response>

4. Dashboard access control (admin/staff only, any authenticated user, or custom permission)
   **Answer**: <awaiting user response>

5. Frontend approach (Django template, existing SPA, or standalone SPA)
   **Answer**: <awaiting user response>

6. Metrics retention and volume (7/30/90 days, approximate req/s)
   **Answer**: <awaiting user response>

## Key Decisions
- <to be filled after user responds>

## New Research Needed
- <to be determined based on user's answers>
```

---

## Artifacts Produced

| Artifact | Path | Status |
|----------|------|--------|
| Spec directory | `.specs/realtime-dashboard/` | Created |
| Registry | `.specs/registry.md` | Initialized (empty table) |
| Research notes | `.specs/realtime-dashboard/research-01.md` | Complete |
| Interview round 1 | `.specs/realtime-dashboard/interview-01.md` | Questions asked, awaiting answers |

## What Happens Next

After the user answers the 6 interview questions:

1. **Phase 3 (Deeper Research)**: Research the specific paths chosen by the user (e.g., if Celery is already in the stack, research celery-beat periodic task patterns for metrics; if Django 5.x, research the latest async middleware capabilities). Save to `research-02.md`.
2. **Phase 4 (Interview Round 2)**: Present deeper findings on trade-offs, edge cases, and implementation sequence. Ask about remaining ambiguities. Save to `interview-02.md`.
3. **Repeat** until all ambiguity is resolved and every task can be described concretely.
4. **Phase 5 (Write Spec)**: Synthesize all research and interviews into a comprehensive SPEC.md with phases, tasks, architecture diagram, library choices table, testing strategy, resume context, and decision log. Present for user approval.
5. **Implementation** happens only after user approves the spec, and only via `/specsmith:implement` -- the forge workflow never produces application code.
