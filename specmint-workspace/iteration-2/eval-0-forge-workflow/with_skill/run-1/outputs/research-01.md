# Research Notes — Real-Time Notifications

## Date: 2026-03-06

## Project Architecture

The user describes a Next.js application deployed on Vercel, using Prisma ORM with a PostgreSQL database. This is a social-platform-style app where users create posts, follow each other, comment, and like posts.

**Notification triggers identified:**
1. Comment on a post (commenter -> post author)
2. New follower (follower -> followed user)
3. Post liked (liker -> post author)

**Deployment constraint:** Vercel's serverless/edge architecture, which has significant implications for real-time transport selection.

## Relevant Code (Simulated — No Codebase Available)

No existing codebase was available to scan. The user described the stack but did not provide access to the project files. Research is based on the described stack: Next.js + Prisma + PostgreSQL + Vercel.

**Typical file structure for this stack:**
```
src/
├── app/                    # Next.js App Router
│   ├── api/                # API routes (serverless functions on Vercel)
│   │   └── notifications/  # Where notification endpoints would live
│   ├── (auth)/             # Auth-related pages
│   └── layout.tsx          # Root layout
├── lib/
│   ├── prisma.ts           # Prisma client singleton
│   └── ...
├── components/
└── ...
prisma/
├── schema.prisma           # Database schema
└── migrations/
```

## Tech Stack & Dependencies

| Component | Technology | Notes |
|-----------|-----------|-------|
| Framework | Next.js (App Router assumed) | Serverless on Vercel |
| ORM | Prisma | PostgreSQL adapter |
| Database | PostgreSQL | Hosted externally (Supabase, Neon, AWS RDS, etc.) |
| Hosting | Vercel | Serverless functions, edge functions available |
| Auth | Unknown | Likely NextAuth.js / Auth.js or Clerk |

## External Research

### SSE (Server-Sent Events) on Vercel

**How SSE works:** Server keeps an HTTP connection open and pushes text events to the client. Unidirectional (server -> client). Uses the `text/event-stream` content type. Native browser support via `EventSource` API.

**Vercel SSE support:**
- Vercel serverless functions support streaming responses, which enables SSE
- However, serverless functions have **hard timeout limits**:
  - Hobby plan: 10 seconds (streaming extends to 25s)
  - Pro plan: 60 seconds (streaming extends to ~300s / 5 minutes)
  - Enterprise: configurable, up to 900s
- Streaming responses (including SSE) keep the function alive for the duration of the connection, which counts against function invocation duration and billing
- After the timeout, the connection is forcefully closed — client must reconnect
- Each reconnection spins up a new serverless function invocation
- **Edge Functions** have a 25-second wall-clock limit but much cheaper execution
- SSE with reconnection on Vercel is viable but requires careful handling of the timeout cycle

**Vercel SSE pattern (practical approach):**
- Client connects via EventSource
- Server streams events until timeout approaches (~55s on Pro)
- Server sends a "reconnect" event or client handles `onerror` to auto-reconnect
- On reconnect, client sends `Last-Event-ID` header so server can resume
- This creates a "long-polling-like" experience with SSE semantics

**Pros of SSE on Vercel:**
- Works with serverless (no persistent server needed beyond function lifetime)
- Native browser support (EventSource API with auto-reconnect)
- Simple protocol — just HTTP
- Unidirectional is fine for notifications (server -> client only)
- No additional infrastructure needed

**Cons of SSE on Vercel:**
- Connection drops every 60-300 seconds (depending on plan), requiring reconnect
- Each reconnect = new function invocation = cost
- Missed events during reconnection window (need catch-up mechanism)
- Not truly "instant" — small delay on reconnect cycles
- Function cold starts add latency on reconnect

### WebSockets on Vercel

**Vercel does NOT support WebSockets on serverless functions.** This is a fundamental architectural limitation:
- Serverless functions are request-response oriented
- WebSocket connections require persistent, long-lived server processes
- Vercel's infrastructure terminates idle connections aggressively

**Workarounds for WebSockets:**
1. **Third-party WebSocket services**: Pusher, Ably, Socket.io Cloud, Soketi
2. **Separate WebSocket server**: Run a WebSocket server on a different platform (Railway, Fly.io, AWS EC2/ECS, DigitalOcean) alongside the Vercel frontend
3. **Vercel's own real-time offering**: As of 2025, Vercel has been exploring real-time capabilities but does not natively support persistent WebSocket connections in serverless functions

### Third-Party Real-Time Services (Recommended by Vercel)

| Service | Protocol | Free Tier | Pricing Model | Notes |
|---------|----------|-----------|---------------|-------|
| **Pusher** | WebSocket | 200K messages/day, 100 connections | Per message + connection | Most popular, mature |
| **Ably** | WebSocket/SSE | 6M messages/month | Per message | Strong reliability guarantees |
| **Supabase Realtime** | WebSocket (Phoenix Channels) | Included with Supabase | Bundled with DB hosting | Great if already using Supabase for Postgres |
| **Neon** (with pg_notify) | PostgreSQL LISTEN/NOTIFY | Depends on plan | Bundled with DB | Requires persistent listener process |
| **Liveblocks** | WebSocket | 300 MAU | Per user | Focused on collaborative features |
| **Soketi** | WebSocket (Pusher-compatible) | Self-hosted (free) | Infrastructure costs | Open source, self-hosted Pusher alternative |

### PostgreSQL LISTEN/NOTIFY Pattern

Since the user already has PostgreSQL, `pg_listen`/`pg_notify` is worth considering:
- PostgreSQL has built-in pub/sub via `LISTEN`/`NOTIFY`
- When a notification-worthy event occurs (comment, follow, like), a database trigger or application code sends `NOTIFY` on a channel
- A listener process receives the notification and forwards it to clients
- **Problem on Vercel:** You need a persistent process to `LISTEN` — serverless functions can't do this. Would require a separate always-on service.

### Polling as a Baseline

Simple polling (client fetches `/api/notifications` every N seconds) is the simplest approach:
- No infrastructure beyond what already exists
- Works perfectly with serverless
- Latency = polling interval (5-30 seconds typically)
- Higher database load with many users
- Can be optimized with "long polling" but still fundamentally pull-based

## Architecture Patterns for Notifications

### Pattern A: SSE with Reconnection (No External Service)
```
Client (EventSource) <--SSE--> Vercel Serverless Function <--query--> PostgreSQL
                                     |
                              (reconnects every ~60s)
```
- On each connection/reconnect, query for new notifications since last seen
- Send `Last-Event-ID` to avoid duplicates
- Simple but periodic reconnection gaps

### Pattern B: Third-Party Push Service (Recommended)
```
Client (WebSocket via Pusher/Ably SDK) <--WS--> Pusher/Ably
                                                    ^
                                                    |
Vercel API Route (on mutation) ------trigger------->|
                |
                v
            PostgreSQL (persist notification)
```
- When a comment/like/follow occurs, API route:
  1. Writes notification to DB (for history/unread count)
  2. Pushes event to Pusher/Ably channel for that user
- Client subscribes to their user channel
- Truly real-time, no polling, no reconnection gaps
- Additional dependency and cost

### Pattern C: Supabase Realtime (If Using Supabase)
```
Client (Supabase JS SDK) <--WS--> Supabase Realtime
                                       ^
                                       | (listens to notifications table)
Vercel API Route (on mutation) --> INSERT into notifications table
```
- If Postgres is hosted on Supabase, Realtime is built-in
- Subscribe to INSERT events on the notifications table
- No additional service needed beyond Supabase

### Pattern D: Polling + Optimistic UI
```
Client (fetch every 10-30s) --> Vercel API Route --> PostgreSQL
```
- Simplest approach
- Acceptable for many apps (GitHub, many social platforms use polling)
- Can add SSE/push later as an enhancement

## Notification Data Model (Prisma)

```prisma
model Notification {
  id          String             @id @default(cuid())
  userId      String             // recipient
  actorId     String             // who triggered it
  type        NotificationType
  entityId    String             // post/comment/user ID
  entityType  String             // "post", "comment", "user"
  read        Boolean            @default(false)
  createdAt   DateTime           @default(now())

  user        User               @relation("notifications", fields: [userId], references: [id])
  actor       User               @relation("actorNotifications", fields: [actorId], references: [id])

  @@index([userId, read, createdAt])
  @@index([userId, createdAt])
}

enum NotificationType {
  COMMENT
  FOLLOW
  LIKE
}
```

## Key Architectural Decisions Needed

1. **Transport mechanism**: SSE with reconnection, third-party push service, polling, or hybrid?
2. **PostgreSQL hosting provider**: Determines whether Supabase Realtime is an option
3. **Notification persistence**: Store all notifications in DB, or only unread? Retention policy?
4. **Real-time urgency**: Are instant notifications critical, or is a 10-30 second delay acceptable?
5. **Scale expectations**: How many concurrent users? This affects cost of third-party services
6. **Notification grouping**: "User A, B, and 3 others liked your post" or individual notifications?
7. **In-app only or also push/email**: Is this just in-app notifications or also browser push / email?

## Open Questions

1. What is the PostgreSQL hosting provider (Supabase, Neon, PlanetScale, AWS RDS, other)?
   - If Supabase, Realtime is a natural fit
2. Does the app use the Next.js App Router or Pages Router?
3. What authentication system is in use (NextAuth/Auth.js, Clerk, custom)?
4. What is the expected user concurrency (10s, 100s, 1000s, 10000s)?
5. Is there a budget constraint that rules out paid third-party services?
6. Does the user want a notification bell/dropdown, a full notification page, or both?
7. Should notifications generate browser push notifications or email digests?
8. Is there an existing notification model or is this greenfield?
