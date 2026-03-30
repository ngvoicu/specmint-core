# Research Notes -- Express API Response Caching with Redis
## Date: 2026-03-06
## Researcher: specsmith:researcher agent + Track B (Context7 + cross-skill)

---

## Project Architecture

> **Note**: This is a simulated research output. In a real forge session, the
> researcher agent would have read 15-30 actual project files. The findings
> below represent what the researcher would produce given the user's
> description: an Express.js API with ~30 REST endpoints, Redis already used
> for sessions, and large JSON payloads on some endpoints.

### Expected Project Structure (to be confirmed by researcher)
```
project-root/
├── src/
│   ├── app.ts / index.ts          # Express app entry point
│   ├── routes/                    # ~30 REST endpoint route files
│   ├── middleware/                 # Auth, error handling, session middleware
│   ├── controllers/               # Request handlers
│   ├── services/                  # Business logic layer
│   ├── models/                    # Data models (ORM/ODM)
│   ├── config/                    # Redis config, env vars, app config
│   └── utils/                     # Shared utilities
├── tests/                         # Test files
├── package.json
├── tsconfig.json (if TypeScript)
└── .env / .env.example
```

### Key Architectural Questions for Researcher
- Is this TypeScript or JavaScript?
- What ORM/database is backing the endpoints?
- How are routes organized (feature-based, resource-based)?
- Is there an existing middleware pipeline? What order?
- How is the existing Redis session store configured?
- Are there any existing caching attempts (in-memory, ETags, etc.)?

## Tech Stack & Dependencies

### Confirmed by User
- **Runtime**: Node.js (version TBD)
- **Framework**: Express.js (version TBD)
- **Cache Store**: Redis (already in use for sessions)
- **Endpoints**: ~30 REST endpoints
- **Payload characteristic**: Some return large JSON payloads

### To Be Discovered by Researcher
- Node.js version (from `.nvmrc`, `engines` in package.json)
- Express version (from lock file)
- Redis client library (likely `redis`, `ioredis`, or `connect-redis`)
- Session library (likely `express-session` with `connect-redis`)
- Database (PostgreSQL? MongoDB? MySQL?)
- TypeScript version (if applicable)
- Testing framework (Jest? Vitest? Mocha?)

## Relevant Code Analysis

### Researcher Agent Prompt (Track A)

The following prompt would be sent to the `specsmith:researcher` agent via the Task tool:

```
Research the codebase for adding a response caching layer to this Express.js API.

Spec ID: api-response-caching
Output path: .specs/api-response-caching/research-01.md

USER REQUEST:
Adding a caching layer to our Express.js API. We're using Redis for sessions
already but need proper response caching with cache invalidation for our REST
endpoints. We have about 30 endpoints and some return large JSON payloads.

FOCUS AREAS:
1. Find and read the Express app entry point - understand the middleware pipeline
2. Map ALL ~30 route/endpoint files - categorize them by:
   - Read-heavy vs write-heavy
   - Payload size (small JSON vs large JSON)
   - Whether they serve user-specific or shared data
   - Authentication requirements
3. Find the existing Redis configuration:
   - Which Redis client library (ioredis, redis, connect-redis)?
   - Connection config (host, port, password, TLS, cluster?)
   - Session store setup
4. Identify the data access patterns:
   - Which ORM/query builder is used?
   - Are there existing model hooks or lifecycle events?
   - Which endpoints trigger writes that would need cache invalidation?
5. Check for existing caching:
   - Any ETag headers set?
   - Any Cache-Control headers?
   - Any in-memory caching (lru-cache, node-cache)?
   - Any CDN configuration?
6. Read the test suite:
   - Framework and patterns used
   - How are routes tested (supertest?)
   - Are there integration tests that hit Redis?
7. Web research:
   - "Express.js response caching Redis middleware best practices 2025"
   - "Redis cache invalidation patterns REST API"
   - "cache-manager vs custom Redis caching Node.js"
   - "Express ETag caching vs application-level caching"
   - "HTTP cache-control headers REST API guide"
8. Library comparison:
   - cache-manager (with @tirke/cache-manager-ioredis) vs custom Redis wrapper
   - ioredis vs redis (node-redis) v4+
   - apicache vs custom middleware
9. Security: Can cached responses leak between users?
10. Performance: Compression of cached payloads, memory limits, eviction policies
```

### Researcher Would Execute These Web Searches

1. `"Express.js Redis response caching middleware best practices 2025"`
2. `"Redis cache invalidation patterns REST API tag-based"`
3. `"cache-manager vs apicache vs custom Redis caching Node.js 2025"`
4. `"HTTP cache-control headers ETag REST API guide"`
5. `"ioredis vs node-redis performance comparison 2025"`
6. `"Redis cache aside pattern Node.js implementation"`
7. `"Express middleware response caching large JSON payloads compression"`

### Researcher Would Read These File Categories (15-30 files)

1. `package.json` / `package-lock.json` -- dependencies and versions
2. `tsconfig.json` -- TypeScript config if present
3. App entry point (`src/app.ts`, `src/index.ts`, `server.ts`)
4. All route files in `src/routes/` (sample of 10-15)
5. Middleware directory -- all files
6. Redis/session configuration files
7. Database models (3-5 relevant models)
8. Service layer files (3-5 key services)
9. Test files (2-3 representative tests)
10. Environment config (`.env.example`, config files)
11. CI/CD pipeline files
12. Docker/deployment files

## Context7 Research (Track B)

### Attempted Context7 Lookups

Context7 was unavailable in this session. In a real forge session, the following
lookups would be performed:

**1. Express.js Documentation**
- Library: `expressjs/express`
- Query: "middleware for response caching, cache-control headers, ETag configuration"
- Expected findings: Express built-in `etag` option, `res.set()` for cache headers,
  middleware ordering best practices, `express.static` cache options

**2. ioredis Documentation**
- Library: `redis/ioredis`
- Query: "Redis caching patterns, pipeline commands, key expiration, pub/sub for invalidation"
- Expected findings: Pipeline/multi for atomic operations, key expiration with `EX`/`PX`,
  Pub/Sub for cache invalidation across instances, Lua scripting for atomic cache operations,
  cluster mode considerations

**3. cache-manager Documentation**
- Library: `node-cache-manager/node-cache-manager` or `jaredwray/cacheable`
- Query: "Redis store setup, multi-tier caching, cache wrap pattern, TTL configuration"
- Expected findings: `caching()` factory function, store configuration, `wrap()` pattern
  for cache-aside, TTL per key, multi-store (memory + Redis) tiered caching, tag-based
  invalidation (if supported)

**4. node-redis (redis) v4+ Documentation**
- Library: `redis/node-redis`
- Query: "Redis client v4 caching, JSON support, key scanning, cache invalidation"
- Expected findings: Modern async/await API, RedisJSON module support, `SCAN` for
  pattern-based invalidation, client-side caching support

**5. apicache Documentation** (if relevant)
- Library: `kwhitley/apicache`
- Query: "Express API response caching middleware with Redis"
- Expected findings: Simple middleware approach, group-based invalidation,
  NOTE: apicache is largely unmaintained -- this would be discovered

### What Context7 Would Have Revealed

Based on current library ecosystem knowledge:

**Express.js (v4.x / v5.x)**
- Built-in ETag generation (weak ETags by default)
- `res.set('Cache-Control', ...)` for HTTP cache headers
- No built-in application-level response caching
- Middleware ordering is critical -- cache middleware must run before route handlers

**ioredis (v5.x)**
- Mature, feature-rich Redis client with TypeScript support
- Built-in cluster support, Sentinel support
- Pipeline and multi/exec for atomic operations
- Pub/Sub for cross-instance cache invalidation
- Lua scripting support for complex atomic operations
- `SCAN` command support for pattern-based key deletion (safer than `KEYS`)

**cache-manager (v5.x / v6.x)**
- Complete rewrite in v5 with modern async/await API
- Multi-store support (memory L1 + Redis L2)
- `wrap()` function for cache-aside pattern
- Configurable TTL per operation
- Store adapters: `@tirke/cache-manager-ioredis` or `cache-manager-redis-yet`
- No built-in tag-based invalidation (must implement manually)
- No built-in HTTP middleware (must wrap it yourself)

**node-redis v4+**
- Complete rewrite from v3 with async/await
- Client-side caching support (Redis 6+ protocol)
- RedisJSON module support
- `SCAN` iterator for safe key enumeration

## Library Comparisons

### Decision Point 1: Redis Client Library

| Library | Stars | Downloads/wk | TS Support | Cluster | Pipeline | Lua Scripts | Maintained | Pick? |
|---------|-------|-------------|------------|---------|----------|-------------|------------|-------|
| ioredis | ~14k | ~6M | Native (v5) | Yes (native) | Yes | Yes | Active | ** |
| node-redis (redis) | ~17k | ~8M | Native (v4+) | Via plugin | Yes | Yes | Active | |

**Recommendation**: If the project already uses `ioredis` for sessions, stick with it.
If using `redis` (node-redis), stick with that. Do not introduce a second Redis client.
Both are excellent. ioredis has slightly better cluster support and a more intuitive API
for Pub/Sub. node-redis v4 has client-side caching support (Redis 6+ protocol feature).

### Decision Point 2: Caching Approach

| Approach | Complexity | Flexibility | TTL Control | Invalidation | Multi-tier | Pick? |
|----------|-----------|-------------|-------------|-------------|------------|-------|
| cache-manager + Redis store | Low | Medium | Per-key | Manual (pattern/tag) | Yes (L1 mem + L2 Redis) | ? |
| Custom Redis middleware | Medium | High | Full control | Full control | Custom | ? |
| apicache | Very Low | Low | Per-route | Group-based | No | |

**Analysis**:

- **cache-manager**: Good abstraction, supports multi-tier caching (in-memory L1 + Redis L2),
  `wrap()` pattern simplifies cache-aside logic. Downside: no built-in HTTP middleware,
  no tag-based invalidation out of the box. Would need a custom Express middleware wrapper
  and custom invalidation logic. v5/v6 is actively maintained.

- **Custom Redis middleware**: Maximum control over caching behavior, key naming, TTL
  strategies, invalidation patterns, and compression. More code to write and maintain,
  but perfectly tailored to the project's needs. Good choice when cache invalidation
  requirements are complex.

- **apicache**: Simple drop-in middleware but largely unmaintained (last significant
  update years ago). Limited invalidation capabilities. Not recommended for production
  use with complex requirements.

**Recommendation**: Depends on complexity of invalidation requirements. If simple TTL-based
expiration suffices for most endpoints, cache-manager is the pragmatic choice. If the project
needs sophisticated tag-based invalidation (e.g., invalidate all caches touching "user:123"
when that user is updated), a custom approach built on the existing Redis client is better.
This is a key interview question.

### Decision Point 3: Cache Invalidation Strategy

| Strategy | Complexity | Precision | Performance | Scalability |
|----------|-----------|-----------|-------------|-------------|
| TTL-only (time-based expiration) | Very low | Low (stale windows) | Best | Excellent |
| Write-through (invalidate on write) | Medium | High | Good | Good |
| Tag-based (group keys by entity) | Medium-High | High | Good | Good |
| Pub/Sub (cross-instance notification) | High | High | Good | Excellent (multi-instance) |
| Event-driven (model hooks) | Medium | High | Good | Good |

**Recommendation**: A hybrid approach is typical for production APIs:
1. TTL-based as the baseline (every cached response expires)
2. Write-through invalidation for data consistency (when a mutation endpoint is called,
   explicitly invalidate related cache keys)
3. Tag-based grouping if entities are shared across many endpoints
4. Pub/Sub only needed if running multiple API server instances

### Decision Point 4: Cache Key Strategy

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| URL-based | `cache:/api/users?page=1` | Simple, works with middleware | Doesn't handle auth differences |
| URL + user | `cache:user:123:/api/profile` | User-specific caching | More keys, more memory |
| Resource-based | `cache:users:list:page:1` | Semantic, easier invalidation | Requires manual key construction |
| Hash-based | `cache:sha256(url+params+user)` | Collision-free | Opaque keys, hard to debug/invalidate |

**Recommendation**: Resource-based keys with a consistent prefix scheme. Example:
`cache:v1:users:list:page=1:limit=20` for shared data,
`cache:v1:user:123:profile` for user-specific data.
This makes pattern-based invalidation easy: `SCAN` for `cache:v1:users:*` to invalidate
all user list caches.

## Risk Assessment

### Breaking Changes
- Adding caching middleware changes the response pipeline -- existing tests that
  check exact response headers may fail
- If responses include timestamps or request-specific data, caching could serve
  stale/incorrect data
- Rate limiting or analytics that depend on handler invocation counts will be
  affected by cache hits

### Performance
- **Positive**: Significant reduction in database queries for read-heavy endpoints;
  large JSON payloads benefit most (avoid serialization/query cost)
- **Negative**: Redis roundtrip adds ~0.5-2ms per request (but saves 50-500ms of
  DB query time); memory pressure on Redis if caching large payloads without limits
- **Compression**: Consider compressing cached payloads > 1KB with zlib/brotli
  before storing in Redis to reduce memory usage and network transfer
- **Serialization**: JSON.stringify/parse overhead for large payloads; consider
  MessagePack or Buffer storage for very large responses

### Security
- **Cache poisoning**: Ensure cache keys include authentication context where needed
  (user-specific data must never be served to different users)
- **Sensitive data**: Don't cache responses containing PII, tokens, or secrets
  unless the cache key is scoped to the authenticated user
- **Cache-Control headers**: Set appropriate `private` vs `public` directives;
  never set `public, max-age=...` on user-specific data
- **Redis ACLs**: If Redis is shared between sessions and cache, consider using
  different Redis databases (SELECT) or key prefixes with ACL rules

### Scalability
- **Memory limits**: Set `maxmemory` and `maxmemory-policy` on Redis (recommend
  `allkeys-lru` for cache workloads)
- **Key explosion**: With 30 endpoints, query params, and pagination, key count
  can grow fast. Monitor with `INFO keyspace`
- **Multi-instance**: If running multiple API servers, cache invalidation must
  propagate to all instances (Pub/Sub or shared Redis handles this naturally)
- **Thundering herd**: When a popular cache key expires, many requests may hit
  the database simultaneously. Consider cache stampede protection (lock + recompute)

### Migration
- No data migration needed (caching is additive)
- Rollback plan: Remove caching middleware and the feature is cleanly disabled
- Consider a feature flag to enable/disable caching per endpoint during rollout

## Open Questions (For Interview)

1. **Which Redis client library** is already in use for sessions? (ioredis vs node-redis)
2. **What database** backs the API? (Affects invalidation strategy -- ORM hooks vs manual)
3. **Are any endpoints user-specific** (return different data per authenticated user) vs
   shared/public (same data for everyone)?
4. **How many API server instances** run in production? (Affects invalidation architecture)
5. **What's the current latency** on the slowest endpoints? (Helps prioritize which to cache)
6. **Are there any real-time or webhook consumers** that expect immediate data freshness?
7. **Is the project TypeScript or JavaScript?**
8. **What's the acceptable staleness window?** (Can users tolerate 30s stale data? 5 min? 0?)
9. **Should cache be opt-in (whitelist endpoints) or opt-out (cache everything by default)?**
10. **Is response compression already in place** (e.g., `compression` middleware)?
11. **Are there admin/internal endpoints** that should never be cached?
12. **Does the API have versioning** (e.g., `/api/v1/...`) that would affect key namespacing?

## Research Completeness Checklist

- [x] Library comparison done for Redis client (ioredis vs node-redis)
- [x] Library comparison done for caching approach (cache-manager vs custom vs apicache)
- [x] Cache invalidation strategies compared (TTL, write-through, tag-based, Pub/Sub)
- [x] Cache key strategies compared (URL, URL+user, resource, hash)
- [x] Security implications considered (cache poisoning, PII leaking, ACLs)
- [x] Performance implications analyzed (compression, serialization, stampede)
- [x] Scalability considerations documented (memory limits, key explosion, multi-instance)
- [x] Risk assessment completed
- [x] Open questions identified for interview
- [ ] Project manifest and lock file read (requires researcher agent access to codebase)
- [ ] Directory structure mapped (requires researcher agent access to codebase)
- [ ] 15+ relevant files read in detail (requires researcher agent access to codebase)
- [ ] Dependency chain traced for key functions (requires researcher agent access to codebase)
- [ ] Test coverage assessed (requires researcher agent access to codebase)
- [ ] 3+ web searches conducted (would be done by researcher agent)
- [ ] Library docs checked via Context7 (Context7 unavailable in this session)
- [ ] Context7 docs for Express.js (unavailable -- used training knowledge)
- [ ] Context7 docs for ioredis (unavailable -- used training knowledge)
- [ ] Context7 docs for cache-manager (unavailable -- used training knowledge)
