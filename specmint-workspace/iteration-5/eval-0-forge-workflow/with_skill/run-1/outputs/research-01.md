# Research Notes — Real-Time Notifications
## Date: 2026-03-06
## Researcher: specsmith:researcher agent (training knowledge — WebSearch, WebFetch, and Context7 unavailable)

## Project Architecture

**Note:** No user codebase was available for scanning. The user described:
- Next.js application (version unspecified — assumed App Router / Next.js 14+)
- Prisma ORM with PostgreSQL
- Deployed on Vercel (serverless)
- Social features already exist: posts, comments, followers, likes

Research was conducted entirely from training knowledge of the Next.js/Vercel/Prisma/PostgreSQL ecosystem.

## Tech Stack & Dependencies (as described by user)

- **Framework**: Next.js (assumed 14+ with App Router)
- **ORM**: Prisma
- **Database**: PostgreSQL
- **Deployment**: Vercel (serverless functions, edge runtime available)
- **Real-time candidates**: SSE, WebSockets, or third-party service (Pusher, Ably, etc.)

## Core Constraint: Vercel's Serverless Architecture

This is the single most important architectural constraint for this feature. Vercel's serverless model fundamentally shapes which real-time approaches are viable.

### What Vercel Supports

1. **Serverless Functions** — Stateless, invoked per-request, max execution time:
   - Hobby: 60 seconds
   - Pro: 300 seconds (5 minutes)
   - Enterprise: 900 seconds (15 minutes)
   - Functions spin up, handle one request, then terminate. No persistent process.

2. **Streaming Responses** — Vercel supports streaming via the `ReadableStream` API in Route Handlers. This enables SSE-like patterns, but each connection is still bounded by the function timeout.

3. **Edge Runtime** — Runs on Cloudflare Workers-like V8 isolates. Supports streaming. Lower latency, but no Node.js APIs (no `node:pg`, no native modules).

4. **No native WebSocket support** — Vercel serverless functions cannot maintain long-lived WebSocket connections. The serverless model is request-response; WebSocket requires a persistent bidirectional connection. Vercel explicitly does not support WebSocket upgrade in serverless functions.

### What Vercel Does NOT Support

- **Persistent WebSocket connections** in serverless functions
- **Long-lived server processes** that can push to connected clients
- **In-memory state** shared across requests (each invocation is isolated)
- **PostgreSQL LISTEN/NOTIFY** from serverless (requires persistent DB connection)

## Real-Time Delivery Approaches: Detailed Comparison

### Option 1: Server-Sent Events (SSE) via Vercel Streaming

**How it works**: Client opens an `EventSource` connection to a Next.js Route Handler. The handler streams events using `ReadableStream`. The connection stays open until timeout or client disconnect.

**Pros**:
- No third-party service needed — zero additional cost
- Native browser API (`EventSource`) with automatic reconnection
- Unidirectional (server-to-client) is perfect for notifications
- Works with Next.js Route Handlers using `ReadableStream`
- Simple protocol — just HTTP with `text/event-stream` content type

**Cons**:
- **Bounded by Vercel function timeout** (60s Hobby / 300s Pro) — connection drops and must reconnect
- **Polling-in-disguise**: Each SSE connection is a function invocation. On reconnect, it's a new invocation. At scale (1000 concurrent users), this means 1000 concurrent function invocations, each polling the DB
- **No push**: The function must poll the database for new notifications during the stream. There's no way for a separate function (handling a POST /comment) to "push" into an existing SSE stream on another function invocation
- **Connection limit**: Browsers limit to 6 concurrent HTTP/1.1 connections per domain. SSE uses one of these slots permanently
- **Cost at scale**: Each reconnection cycle is a new function invocation. With 60s timeout and reconnect, that's ~1440 function invocations per user per day
- **Database load**: Each SSE stream polls the DB (e.g., every 2-5 seconds). 1000 users = 200-500 queries/second just for notification polling

**Verdict**: Viable for small scale (< 100 concurrent users). Becomes expensive and architecturally awkward at scale. Essentially sophisticated polling.

### Option 2: WebSockets via External Service

**How it works**: Use a managed WebSocket/real-time service (Pusher, Ably, Soketi, Liveblocks). The client connects to the service directly. Your Next.js API routes trigger events on the service when actions occur (comment, follow, like).

**Pros**:
- True real-time push — instant delivery, no polling
- Scales independently from your application
- No function timeout concerns — connections are managed by the service
- Bidirectional (though notifications only need server-to-client)
- Battle-tested at scale (Pusher handles billions of messages)
- Simple integration: trigger event from API route, subscribe from client

**Cons**:
- Third-party dependency and cost (free tiers are generous though)
- Additional service to manage/monitor
- Network hop: Vercel -> Pusher -> Client (adds ~10-50ms latency)
- Vendor lock-in (mitigated by using an abstraction layer)

**Verdict**: Best approach for Vercel deployments. The industry standard pattern for real-time on serverless platforms.

### Option 3: Polling (Short Polling)

**How it works**: Client periodically calls a REST endpoint (e.g., every 10-30 seconds) to check for new notifications.

**Pros**:
- Simplest to implement — standard REST endpoint
- Works everywhere, no special infrastructure
- Stateless, serverless-friendly
- Easy to reason about and debug

**Cons**:
- Not real-time — 10-30 second delay
- Wasted requests when there are no new notifications
- Scales linearly with users (N users * frequency = requests/second)

**Verdict**: Acceptable for MVP or low-traffic apps where "near-real-time" (10-30s) is good enough.

### Option 4: Self-Hosted WebSocket Server (Outside Vercel)

**How it works**: Run a separate WebSocket server (e.g., on Railway, Fly.io, AWS EC2) alongside the Vercel deployment. The Next.js app triggers notifications via HTTP to the WS server, which pushes to connected clients.

**Pros**:
- Full control over the WebSocket implementation
- No third-party service fees (beyond hosting)
- Can use PostgreSQL LISTEN/NOTIFY for DB-driven events

**Cons**:
- Operational complexity — separate server to deploy, monitor, scale
- Two deployment targets to manage
- Latency between Vercel functions and WS server
- Authentication must be shared between systems

**Verdict**: Over-engineered for most cases. Only makes sense if you have extreme requirements or want to avoid third-party services entirely.

## Library Comparisons

### Real-Time Service Providers

| Service | Free Tier | Pricing After | Connections | Messages | TS SDK | Vercel Integration |
|---------|-----------|---------------|-------------|----------|--------|-------------------|
| **Pusher Channels** | 200k msgs/day, 100 connections | $49/mo (1M msgs) | Unlimited (paid) | Per-message | Yes | Official template |
| **Ably** | 6M msgs/mo, 200 connections | $29/mo (10M msgs) | Unlimited (paid) | Per-message | Yes | Docs available |
| **Soketi** | Self-hosted (free) | Hosting costs only | Unlimited | Unlimited | Pusher-compatible | Manual setup |
| **Supabase Realtime** | 200 connections, 2M msgs | $25/mo (500 connections) | Per-plan | Per-plan | Yes | Good integration |
| **Novu** | 30k events/mo | $250/mo | N/A (API) | Per-event | Yes | REST API |
| **Knock** | 10k msgs/mo | $250/mo | N/A (API) | Per-message | Yes | REST API |

**Recommendation**: **Pusher Channels** — most mature, best documented for the Next.js + Vercel pattern, generous free tier for development, Pusher-compatible API means you can switch to self-hosted Soketi later if costs grow. Ably is a strong second choice with more generous free-tier messaging limits.

**Alternative recommendation**: If the user is already using **Supabase** for anything, Supabase Realtime would be the natural choice. But since they specified Prisma + PostgreSQL directly, Pusher is the better fit.

### Notification Management Libraries

| Library | Purpose | Stars | Approach |
|---------|---------|-------|----------|
| **Novu** | Full notification infrastructure | 35k+ | API-based, templates, multi-channel |
| **Knock** | Notification infrastructure | N/A | API-based, feeds, preferences |
| **Custom** | Build with Prisma + Pusher | N/A | Full control, no vendor lock-in |

**Recommendation**: For a social app with three notification types (comment, follow, like), a **custom implementation** with Prisma + a real-time transport is simpler and cheaper than Novu/Knock. Those services shine when you need multi-channel (email, SMS, push, in-app) with templates and preference management. If multi-channel is needed later, Novu or Knock can be added on top.

## Notification System Architecture Patterns

### Database Schema Pattern (Prisma)

Standard notification table design for social apps:

```
Notification
  - id          String (cuid/uuid)
  - type        Enum (COMMENT, FOLLOW, LIKE)
  - recipientId String (FK to User)
  - actorId     String (FK to User — who performed the action)
  - entityType  String (POST, COMMENT, USER — what was acted on)
  - entityId    String (ID of the entity)
  - read        Boolean (default false)
  - createdAt   DateTime
```

Key design decisions:
- **Polymorphic entity reference** (entityType + entityId) vs **separate FK columns** per type
- **Denormalized actor/entity info** (store name/avatar at creation time) vs **join on read**
- **Batch notifications** ("3 people liked your post") vs **individual** ("Alice liked your post")
- **Notification preferences** (user can disable certain types)

### Event Flow Pattern

```
User Action (comment/follow/like)
  → API Route Handler
    → 1. Write to database (Prisma)
    → 2. Create notification record (Prisma)
    → 3. Trigger real-time event (Pusher/SSE)
  → Client receives event
    → Update notification badge/dropdown
    → Optionally show toast
```

### Client-Side Pattern

- **Notification bell/badge**: Shows unread count, dropdown with recent notifications
- **Toast notifications**: Ephemeral popup for real-time events
- **Notification page/feed**: Full paginated list of all notifications
- **Mark as read**: Individual and bulk mark-as-read

## Risk Assessment

### Performance
- **Database writes**: Every like/comment/follow creates a notification row. High-engagement posts could generate thousands of rows. Consider batching or rate-limiting
- **Query performance**: Fetching notifications requires joins (actor, entity). Index on `(recipientId, read, createdAt)` is essential
- **Real-time fanout**: If a post has 1000 followers and gets a comment, that's 1000 notification records + 1000 real-time events. Consider whether all followers need to be notified of comments

### Security
- **Authorization**: Users must only see their own notifications
- **Rate limiting**: Prevent notification spam (rapid like/unlike, follow/unfollow)
- **Channel security**: Real-time channels must be authenticated (private channels in Pusher)
- **Input validation**: Actor/entity IDs must be validated before creating notifications

### Scalability
- **Notification volume**: Social apps generate high notification volume. Consider archiving/pruning old notifications
- **Database growth**: Notification table grows fast. Partition by date or archive after 90 days
- **Concurrent connections**: Real-time service connection limits scale with users

### Migration
- No existing notification system to migrate from (new feature)
- Existing models (Post, Comment, User/Follow, Like) need to trigger notification creation
- Need to decide: retrofit existing action handlers or use Prisma middleware/event hooks

## UI/UX Research

### Common Notification UI Patterns
- **Bell icon with badge count** in the header/nav
- **Dropdown panel** showing recent notifications (5-10 items) with "See all" link
- **Full notification page** with infinite scroll and filters
- **Toast/snackbar** for real-time notifications that appear and auto-dismiss
- **Grouped notifications**: "Alice and 3 others liked your post"
- **Read/unread visual distinction**: Bold text, colored dot, or background shade

### Accessibility
- `aria-live` region for real-time notification announcements
- Screen reader support for notification badge count changes
- Keyboard navigation for notification dropdown
- Focus management when notification panel opens/closes

## Open Questions

1. **Delivery mechanism**: SSE (simple but limited on Vercel) vs Pusher/Ably (robust but third-party dependency) vs polling (simplest but not real-time)?
2. **Notification grouping**: Should "5 people liked your post" be a single grouped notification, or 5 individual ones?
3. **Notification persistence**: How long should notifications be kept? Should they be pruned/archived?
4. **Multi-channel**: Is in-app sufficient, or do you also need email/push notifications for the same events?
5. **Notification preferences**: Can users disable certain notification types?
6. **Existing data models**: What do the current Post, User, Comment, and Like/Follow models look like? Are there existing patterns for event handling?
7. **Real-time scope**: Should the notification badge update in real-time, or is it acceptable to update on page navigation?
8. **UI framework**: Are you using a component library (shadcn/ui, Radix, etc.) for the notification UI?

## Research Completeness Checklist
- [x] Vercel serverless constraints analyzed (critical constraint for this feature)
- [x] SSE vs WebSocket vs polling comparison completed
- [x] Real-time service providers compared (Pusher, Ably, Soketi, Supabase, Novu, Knock)
- [x] Notification database schema patterns documented
- [x] Event flow architecture mapped
- [x] Security implications considered (auth, rate limiting, channel security)
- [x] Scalability risks identified (fanout, DB growth, connection limits)
- [x] UI/UX patterns researched (bell, dropdown, toast, grouping, accessibility)
- [x] Open questions compiled for interview
- [ ] Actual codebase scanned (not available — user project not accessible)
- [ ] Lock file versions verified (not available)
- [ ] Web searches conducted (WebSearch tool unavailable)
- [ ] Context7 docs pulled (Context7 tool unavailable)
