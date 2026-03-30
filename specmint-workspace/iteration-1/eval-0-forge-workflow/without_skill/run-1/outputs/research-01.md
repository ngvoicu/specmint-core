# Research Notes -- Real-Time Notifications

## Date: 2026-03-06

## Project Architecture

No access to the user's Next.js codebase. Research is based on the stated tech stack:
- Next.js (App Router assumed, version unspecified)
- Prisma ORM with PostgreSQL
- Deployed on Vercel (serverless)

## Tech Stack & Dependencies

### Stated Stack
- **Framework**: Next.js (version unknown -- need to confirm if App Router or Pages Router)
- **ORM**: Prisma
- **Database**: PostgreSQL
- **Deployment**: Vercel (serverless functions, edge functions available)

### Relevant Prisma/PostgreSQL Features
- PostgreSQL supports `LISTEN/NOTIFY` for real-time database change notifications
- Prisma does not natively expose `LISTEN/NOTIFY` -- would need raw `$queryRaw` or a separate `pg` client
- Prisma supports middleware/extensions that could hook into create operations for notifications

## Real-Time Options Analysis for Vercel

### Option 1: Server-Sent Events (SSE)

**How it works**: Client opens a long-lived HTTP connection. Server pushes events down the stream.

**Vercel compatibility**:
- Vercel serverless functions have execution time limits (10s on Hobby, 60s on Pro, 300s on Enterprise)
- SSE requires long-lived connections -- fundamentally at odds with serverless function timeouts
- Vercel Edge Functions support streaming responses and have longer execution limits, but are designed for quick responses, not persistent connections
- Vercel's infrastructure will terminate idle connections
- **Verdict**: SSE on Vercel is problematic for persistent real-time connections. Could work with short-lived SSE + client reconnection, but not ideal.

### Option 2: WebSockets

**How it works**: Full-duplex persistent connection between client and server.

**Vercel compatibility**:
- Vercel does NOT support WebSocket connections on serverless functions
- Next.js API routes on Vercel cannot upgrade to WebSocket
- WebSockets require a persistent server process
- **Verdict**: Not possible natively on Vercel without an external service.

### Option 3: Third-Party Real-Time Services

**Services**:
- **Pusher**: Managed WebSocket service with channels. Well-established, good Next.js integration.
- **Ably**: Similar to Pusher, more modern API, good reliability.
- **Supabase Realtime**: If using Supabase PostgreSQL, built-in realtime subscriptions. But user is using plain PostgreSQL + Prisma.
- **Liveblocks**: More focused on collaborative features.
- **Soketi**: Self-hosted Pusher-compatible server.
- **Novu**: Notification-specific infrastructure (in-app, email, push, SMS).
- **Knock**: Similar notification infrastructure platform.

**Verdict**: This is the standard approach for Vercel deployments. Pusher/Ably are most common for generic real-time. Novu/Knock are notification-specific.

### Option 4: Polling

**How it works**: Client periodically fetches new notifications via API route.

**Vercel compatibility**: Perfect -- standard request/response, no long connections.

**Trade-offs**:
- Simple to implement
- Higher latency (depends on poll interval)
- More database queries (though can be mitigated with caching)
- Can be combined with other approaches (poll as fallback)

**Verdict**: Simplest option. Good enough for many notification use cases where sub-second delivery isn't critical.

### Option 5: Vercel Edge + SSE Hybrid

- Use Edge Runtime for SSE endpoints (longer timeout, streaming support)
- Client reconnects automatically via EventSource API
- Still limited by edge function execution time
- More complex but avoids third-party dependency

## Notification Data Model Considerations

### Required Entities
- `Notification` table with fields: id, recipientId, type, data (JSON), read, createdAt
- Notification types: `COMMENT`, `FOLLOW`, `LIKE`
- Need to link to source entities: which post was commented on, who followed, which post was liked
- Consider a polymorphic approach vs separate notification type tables

### Trigger Points
- **Comment on post**: When a new Comment is created, notify the post author
- **New follower**: When a Follow relationship is created, notify the followed user
- **Post liked**: When a Like is created, notify the post author
- Edge case: Should users be notified of their own actions? (No)
- Edge case: Duplicate notifications? (e.g., same person likes/unlikes/likes)

### Delivery Architecture
1. **Write path**: Action occurs -> Create Notification record -> Push to real-time channel
2. **Read path**: Client connects -> Fetch unread notifications -> Subscribe to real-time updates
3. **Mark as read**: Individual or bulk mark-as-read endpoint

## Risk Assessment

- **Vercel lock-in**: SSE/WebSocket limitations push toward third-party services, adding cost and dependency
- **Database load**: If polling, frequent queries could strain the database
- **Notification storms**: Popular posts could generate many notifications quickly
- **Privacy**: Notifications could leak information if channels aren't properly scoped per-user
- **Scaling**: Need to ensure notification creation doesn't slow down the primary action (commenting, liking, following)

## Open Questions

1. Next.js version? App Router or Pages Router?
2. Is there an existing notification model or is this greenfield?
3. Are there existing user/post/comment/follow/like models in Prisma?
4. What's the Vercel plan tier? (affects function timeout limits)
5. Is sub-second notification delivery required, or is 5-10 second delay acceptable?
6. Budget for third-party services? (Pusher/Ably have free tiers)
7. Are there other notification channels needed beyond in-app? (email, push, SMS)
8. How should notification grouping work? ("Alice and 3 others liked your post")
9. Should notifications persist or expire after some time?
10. Is there an existing UI for notifications (bell icon, dropdown, dedicated page)?
