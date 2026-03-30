# Transcript: Forge a Spec for Express.js API Caching Layer (Without Skill)

## User Request

> "forge a spec for adding a caching layer to our Express.js API. We're using Redis for sessions already but need proper response caching with cache invalidation for our REST endpoints. We have about 30 endpoints and some return large JSON payloads. Can you forge a spec for this?"

## Claude's Response (No Skill Loaded)

Sure, I can help you plan out a caching layer for your Express.js API. Since you already have Redis running for sessions, we can leverage that same infrastructure for response caching. Let me put together a spec for this.

Before I dive into writing a full spec, I have a few questions that would help me tailor this better:

1. **Cache granularity**: Should all 30 endpoints be cached, or only specific ones (e.g., read-heavy GET endpoints)? Are there endpoints that should never be cached (e.g., user-specific data, real-time data)?

2. **Invalidation strategy**: When you say "cache invalidation," are you thinking:
   - Time-based TTL (simplest)
   - Event-driven invalidation (e.g., when a POST/PUT/DELETE modifies data, related GET caches are cleared)
   - Tag-based invalidation (group related caches and invalidate by tag)
   - Some combination?

3. **Cache key design**: Should caching be per-user (authenticated responses vary by user) or shared (same response for all users)? Do responses vary by query parameters, headers, or other factors?

4. **Large payloads**: How large are we talking? Are there payloads that might exceed Redis memory limits? Should we consider compression?

5. **Existing infrastructure**:
   - Are you using a single Redis instance or a cluster?
   - Is there a reverse proxy (Nginx, CloudFront) in front that could handle some caching?
   - What's your current Redis memory allocation?

6. **Cache warming**: Do you need to pre-populate caches on startup, or is lazy loading (cache on first request) sufficient?

7. **Monitoring**: Do you need cache hit/miss metrics? Dashboard integration?

That said, here's a draft spec based on reasonable defaults for your situation:

---

## Spec: Express.js API Response Caching Layer

### Overview

Add Redis-based response caching to the Express.js REST API, reusing the existing Redis infrastructure currently used for sessions. The system will cache GET endpoint responses with configurable TTLs, support multiple invalidation strategies, and handle large JSON payloads efficiently.

### Goals

- Reduce database load and response times for frequently accessed endpoints
- Provide configurable per-route caching with sensible defaults
- Support cache invalidation when data changes via mutations (POST/PUT/DELETE)
- Reuse existing Redis connection infrastructure
- Add cache hit/miss observability

### Non-Goals

- Full CDN/edge caching (can be layered on later)
- Caching of non-GET requests
- Response streaming or partial caching
- GraphQL caching

### Architecture

#### Middleware Approach

Create an Express middleware that intercepts GET requests and checks Redis for a cached response before hitting the route handler.

```
Request → Cache Middleware → [Cache Hit?] → Yes → Return cached response
                                          → No  → Route Handler → Cache response → Return
```

#### Cache Key Design

```
cache:<version>:<route-pattern>:<sorted-query-params>:<user-id-or-public>
```

Example: `cache:v1:GET:/api/products:category=electronics&page=1:public`

#### Redis Namespace Separation

Use a separate Redis key prefix (`cache:`) to avoid collisions with the existing session store (`sess:`).

#### Suggested Implementation

**1. Cache middleware factory:**

```javascript
const cacheMiddleware = (options = {}) => {
  const { ttl = 300, keyPrefix = 'cache:v1', vary = [], isPublic = true } = options;

  return async (req, res, next) => {
    if (req.method !== 'GET') return next();

    const cacheKey = buildCacheKey(keyPrefix, req, vary, isPublic);
    const cached = await redis.get(cacheKey);

    if (cached) {
      const parsed = JSON.parse(cached);
      res.set('X-Cache', 'HIT');
      return res.status(parsed.status).set(parsed.headers).json(parsed.body);
    }

    // Monkey-patch res.json to intercept the response
    const originalJson = res.json.bind(res);
    res.json = (body) => {
      const toCache = { status: res.statusCode, headers: { 'content-type': 'application/json' }, body };
      redis.setex(cacheKey, ttl, JSON.stringify(toCache));
      res.set('X-Cache', 'MISS');
      return originalJson(body);
    };

    next();
  };
};
```

**2. Per-route configuration:**

```javascript
router.get('/api/products', cacheMiddleware({ ttl: 600, isPublic: true }), productsController.list);
router.get('/api/products/:id', cacheMiddleware({ ttl: 300, vary: ['params.id'] }), productsController.get);
router.get('/api/user/profile', cacheMiddleware({ ttl: 60, isPublic: false }), userController.profile);
```

**3. Cache invalidation middleware:**

```javascript
const invalidateCache = (patterns) => {
  return async (req, res, next) => {
    const originalJson = res.json.bind(res);
    res.json = async (body) => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        for (const pattern of patterns) {
          const keys = await redis.keys(`cache:v1:GET:${pattern}*`);
          if (keys.length) await redis.del(...keys);
        }
      }
      return originalJson(body);
    };
    next();
  };
};

// Usage
router.post('/api/products', invalidateCache(['/api/products']), productsController.create);
router.put('/api/products/:id', invalidateCache(['/api/products']), productsController.update);
```

**4. Large payload handling:**

For payloads over a configurable threshold (e.g., 50KB), apply gzip compression before storing in Redis:

```javascript
const zlib = require('zlib');
const COMPRESSION_THRESHOLD = 50 * 1024; // 50KB

if (serialized.length > COMPRESSION_THRESHOLD) {
  const compressed = zlib.gzipSync(serialized);
  await redis.setex(cacheKey, ttl, compressed);
}
```

### Tasks

1. **Set up cache infrastructure**
   - Create Redis cache client (separate from session client, or shared with namespace)
   - Add cache configuration (default TTL, max entry size, compression threshold)
   - Add environment variables for cache settings

2. **Build cache middleware**
   - Implement `cacheMiddleware` factory function
   - Implement cache key builder with support for query params, user context
   - Add `X-Cache` response header (HIT/MISS)
   - Add compression for large payloads

3. **Build invalidation middleware**
   - Implement pattern-based cache invalidation
   - Add tag-based invalidation support
   - Wire invalidation to mutation endpoints (POST/PUT/DELETE)

4. **Apply caching to endpoints**
   - Audit all 30 endpoints and categorize (public vs. private, TTL requirements)
   - Apply cache middleware to appropriate GET endpoints
   - Apply invalidation middleware to mutation endpoints
   - Document which endpoints are cached and with what TTL

5. **Add observability**
   - Log cache hit/miss ratios
   - Add Redis memory usage monitoring for cache namespace
   - Add cache key count metrics

6. **Testing**
   - Unit tests for cache key builder
   - Integration tests for cache middleware (hit, miss, invalidation)
   - Load test to verify performance improvement
   - Test cache behavior under Redis failure (graceful degradation)

7. **Documentation**
   - Document caching strategy for the team
   - Add cache configuration to deployment docs

### Considerations

- **Redis memory**: With 30 endpoints and varying query params, cache size could grow. Set `maxmemory-policy` to `allkeys-lru` for the cache namespace, or use a separate Redis database/instance.
- **Cache stampede**: When a popular cache key expires, many requests may hit the database simultaneously. Consider implementing a mutex/lock pattern for cache population.
- **Conditional requests**: Consider supporting `ETag` and `304 Not Modified` responses.
- **Graceful degradation**: If Redis is unavailable, the API should still work (just uncached). Wrap all cache operations in try/catch.
- **SCAN vs KEYS**: Never use `KEYS` in production for invalidation -- use `SCAN` or tag-based sets instead.

### Open Questions

1. Should we use a separate Redis database (e.g., `db 1` for sessions, `db 2` for cache) or just key prefixes?
2. What's the acceptable staleness for different endpoint categories?
3. Are there endpoints returning user-specific data that need `Vary` by auth token?
4. Should cache warming be implemented for critical endpoints?
5. Is there a budget for a Redis cluster upgrade if memory becomes a concern?

---

That's a starting point. I'd want to look at your actual codebase to understand the route structure, existing Redis configuration, and payload sizes before finalizing. Want me to refine any section, or should I start implementing?

## Evaluation Notes

### What Claude Did Without the Skill

1. **Asked clarifying questions** -- Listed 7 important questions about cache granularity, invalidation strategy, key design, payload sizes, infrastructure, cache warming, and monitoring. This is good research instinct but was delivered inline rather than through a structured interview process.

2. **Produced a spec-like document** -- Created a reasonable technical plan with overview, goals, non-goals, architecture, implementation sketches, tasks, considerations, and open questions.

3. **Included code examples** -- Provided concrete implementation snippets for the middleware, invalidation, and compression approaches.

4. **No structured workflow** -- Did not follow any forge workflow (research -> interview -> spec). Instead produced everything in one pass.

5. **No persistent artifacts** -- Did not create any files in `.specs/` directory. The spec exists only in the conversation.

6. **No codebase research** -- Did not attempt to read the actual project's codebase, routes, Redis configuration, or existing middleware patterns. All recommendations are generic/hypothetical.

7. **No spec format** -- No frontmatter, no phase markers, no task codes, no resume context. The output is a general technical document, not a structured spec that could be resumed later.

### Research Depth Assessment

- **Codebase research**: None. Claude did not attempt to explore any Express.js project files, route definitions, Redis configuration, package.json, or existing middleware.
- **External research**: None. No Context7 lookups for Redis caching libraries (e.g., `apicache`, `express-redis-cache`, `cacheable`), no web searches for current best practices.
- **Domain knowledge applied**: Moderate. The response shows familiarity with Redis caching patterns (TTL, key design, compression, cache stampede, SCAN vs KEYS) but these are generic recommendations not tailored to any specific codebase.
- **Clarifying questions**: Good quality but delivered as a list rather than an interactive interview. No follow-up based on answers.
- **Completeness**: The spec covers the main concerns but lacks depth in several areas: no analysis of which specific endpoints would benefit most, no benchmarking strategy, no consideration of existing caching libraries vs. custom implementation, no Redis Cluster vs. single-instance analysis.

### Summary

Without the skill, Claude produced a reasonable but generic technical plan. The key gaps are:

1. **No codebase research** -- The most significant gap. A real spec should be grounded in the actual code.
2. **No structured interview** -- Questions were listed but not asked interactively; no iteration on requirements.
3. **No persistent spec** -- Nothing was saved to `.specs/` for future resumption.
4. **No spec format** -- No frontmatter, task codes, phase markers, or resume context.
5. **Single-pass output** -- Everything produced at once rather than through iterative refinement.
6. **No library research** -- Did not investigate existing caching middleware packages or compare approaches.
