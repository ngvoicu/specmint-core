# Transcript: "Forge a spec for adding a caching layer" (Without Skill)

## User Prompt

> forge a spec for adding a caching layer to our Express.js API. We're using Redis for sessions already but need proper response caching with cache invalidation for our REST endpoints. We have about 30 endpoints and some return large JSON payloads. Can you forge a spec for this?

## Claude's Response (No Skill Loaded)

---

I can help you plan out a caching layer for your Express.js API. Before I put together a detailed spec, I have some questions that will shape the design significantly. Let me break them into categories:

### Architecture & Infrastructure Questions

1. **Redis setup**: You mentioned Redis is already used for sessions. Are you using a single Redis instance, or do you have a cluster? Would you want the cache to share the same Redis instance or use a separate one to isolate session data from cache data?

2. **Deployment topology**: Is this a single-server deployment or do you run multiple instances behind a load balancer? This affects whether cache invalidation needs to be coordinated across instances.

3. **Current middleware stack**: What middleware are you using? (e.g., `express-session`, `helmet`, `cors`, `compression`). Knowing the middleware order matters for where caching middleware would slot in.

### Endpoint & Data Questions

4. **Endpoint breakdown**: Of the ~30 endpoints, roughly how many are:
   - Read-only (GET) vs. write (POST/PUT/PATCH/DELETE)?
   - Public (same response for all users) vs. user-specific (personalized data)?
   - Frequently hit vs. rarely accessed?

5. **Payload sizes**: When you say "large JSON payloads," what range are we talking about? 100KB? 1MB? 10MB+? This affects whether we should compress cached values and whether Redis memory becomes a concern.

6. **Data freshness requirements**: Are there endpoints where stale data is acceptable (e.g., product listings that update daily) vs. endpoints that must always be fresh (e.g., account balance, inventory counts)?

7. **Query parameters and variations**: Do your GET endpoints use a lot of query parameters (pagination, filtering, sorting)? This significantly affects cache key design -- more parameter combinations means more cache entries and potentially lower hit rates.

### Invalidation Questions

8. **Write-through patterns**: When data changes via a POST/PUT/DELETE, do changes typically affect:
   - A single cached endpoint (e.g., updating a user invalidates GET /users/:id)?
   - Multiple related endpoints (e.g., updating a product invalidates GET /products, GET /products/:id, GET /categories/:id/products)?
   - Hard to predict relationships?

9. **External data mutations**: Does data change outside of your API? (e.g., database migrations, admin scripts, other services writing to the same database). If so, cache invalidation purely based on API writes won't be sufficient.

10. **Acceptable staleness window**: Would a TTL-based approach (e.g., cache for 60 seconds, then refetch) be acceptable for most endpoints, or do you need immediate invalidation on writes?

### Performance & Operational Questions

11. **Current pain points**: What's driving this? Slow database queries? High latency on specific endpoints? Rate limiting from upstream services? This helps prioritize which endpoints to cache first.

12. **Monitoring**: Do you have observability tooling in place (e.g., Datadog, Prometheus, Grafana)? Cache hit/miss ratios and latency metrics are critical for validating the caching layer.

13. **Authentication model**: Are you using JWT, session cookies, or something else? This affects how we determine if a response is user-specific vs. cacheable across users.

### Preliminary Design Direction

While I wait for your answers, here is the general direction I would take based on what you have shared:

**Approach: Express middleware + Redis cache store**

```
Request → Auth → Cache Middleware → Route Handler → Response
                    |                      |
                    |← cache hit (fast) ←--|
                    |→ cache miss → handler → store in Redis → Response
```

Key components I'd expect in the spec:

- **Cache middleware** that intercepts GET requests, builds a cache key from the route + query params + user context, checks Redis, and either serves the cached response or passes through to the handler
- **Cache key strategy** using a structured format like `cache:v1:{route}:{hash(query+user)}` with key prefixes for efficient pattern-based invalidation
- **Invalidation layer** that hooks into write operations (POST/PUT/PATCH/DELETE) and invalidates related cache entries -- likely using Redis key patterns or a tag-based system
- **Per-route configuration** so each endpoint can specify its own TTL, whether it's user-specific, and its invalidation dependencies
- **Cache headers** (ETag, Cache-Control) for client-side caching that works alongside server-side Redis caching
- **Graceful degradation** so if Redis goes down, the API continues to work (just without caching)
- **Compression** for large payloads stored in Redis (gzip/brotli before storing)

Once you answer those questions, I can put together a detailed implementation plan with specific tasks, file structures, and phased rollout approach. I would recommend starting with the 5-10 highest-traffic GET endpoints rather than trying to cache all 30 at once.

---

## Observations on This Response (Without Skill)

### What happened:
- Claude treated "forge" as a normal English word, not a command
- No file system actions were taken (no `.specs/` directory, no research files, no spec documents)
- No codebase research was performed -- Claude could not look at the actual Express.js project because no project path was provided and the skill's research workflow was not triggered
- The response is a single conversational reply with questions and a preliminary design sketch

### Characteristics of the response:
1. **No structured research phase**: Claude did not use tools (Grep, Glob, Read, Bash) to investigate the actual codebase. It had no way to discover the real endpoint structure, existing middleware, Redis configuration, or data models.
2. **No persistent artifacts**: Nothing was written to disk. No spec file, no research notes, no interview records. If the session ends, all context is lost.
3. **No phased workflow**: There was no structured progression through research -> interview -> deeper research -> spec writing -> implementation. It was a single-shot Q&A response.
4. **Questions were generic**: The 13 questions asked are reasonable but generic -- they are the kind of questions any experienced developer would ask about API caching. They are NOT informed by actual codebase analysis. With the skill, the research phase would have already answered many of these by reading the code.
5. **Preliminary design is surface-level**: The design direction is sound but generic. It describes what most Redis caching middleware looks like without any specifics about this particular codebase's patterns, conventions, or constraints.
6. **No spec format**: No structured document with frontmatter, phases, task codes, status markers, or resume context. Just prose and a code diagram.
7. **No implementation plan**: No concrete tasks, no file paths, no phased approach with checkboxes. The user would need to continue the conversation significantly to get to actionable work.

### What the skill would have added:
- **Deep codebase research**: The researcher agent would have scanned the Express app, found all route files, identified the existing Redis session setup, catalogued middleware, and analyzed endpoint patterns
- **Structured interview**: Questions would have been informed by what the research actually found in the code, not generic
- **Persistent spec document**: A SPEC.md file with YAML frontmatter, phased implementation plan, task codes, and resume context
- **Research artifacts**: Saved research notes that could be referenced later
- **Resumability**: The spec could be paused and resumed across sessions with full context preserved
- **Actionable tasks**: Specific file paths, function names, and implementation steps based on the actual codebase
