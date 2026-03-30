# Research Notes -- Real-Time Notifications

## Date: 2026-03-06

## Project Architecture

The user describes a Next.js application deployed on Vercel, using Prisma ORM with PostgreSQL as the database. Since we are working in the specsmith repo (not the actual Next.js project), we cannot scan the real codebase. The following research is based on the user's description and external documentation.

**Known stack:**
- Next.js (App Router assumed, version unknown)
- Prisma ORM
- PostgreSQL database
- Deployed on Vercel (serverless)

**Unknown / needs clarification:**
- Next.js version (13, 14, 15?)
- App Router vs Pages Router (or both)
- Authentication system in use (NextAuth/Auth.js, Clerk, custom?)
- Current data model for users, posts, comments, followers
- Whether there's an existing notification table or system
- State management approach (React Query, SWR, Zustand, etc.)
- Whether the app uses any existing real-time features

## Relevant Code

Unable to scan actual codebase -- working from user description only.

**Expected models (Prisma):**
- User model (id, name, email, etc.)
- Post model (id, content, authorId, etc.)
- Comment model (id, content, postId, authorId, etc.)
- Follower/Follow relationship (followerId, followingId)
- Notification model (to be created)

**Expected API routes (Next.js):**
- POST /api/comments -- create comment (trigger notification)
- POST /api/follow -- follow user (trigger notification)
- POST /api/likes -- like post (trigger notification)
- GET /api/notifications -- fetch notifications
- PATCH /api/notifications/[id] -- mark as read

## Tech Stack & Dependencies

### Vercel Serverless Constraints (from official docs)

**Critical finding: Vercel does NOT support native WebSockets on serverless functions.**

Vercel Functions are stateless and short-lived. Key constraints from official documentation:

1. **No persistent WebSocket connections**: Serverless functions spin up per-request and shut down after responding. They cannot maintain long-lived bidirectional connections required by WebSocket protocol.

2. **SSE (Server-Sent Events) is partially supported**: Vercel supports streaming responses via both Node.js and Edge runtimes:
   - **Edge Runtime**: Must begin sending a response within 25 seconds, can continue streaming for up to 300 seconds (5 minutes).
   - **Node.js Runtime**: Default max duration is 300 seconds (Hobby), configurable up to 800 seconds on Pro/Enterprise with Fluid Compute.
   - SSE works for finite streams (e.g., AI responses) but is problematic for indefinite notification streams because connections will time out.

3. **Function execution limits**:
   - Hobby: 300s max
   - Pro: 800s max (with Fluid Compute)
   - Enterprise: 800s max (with Fluid Compute)
   - After timeout, connection drops with 504 error

4. **Concurrency**: Auto-scales up to 30,000 (Hobby/Pro). Each SSE connection occupies one function invocation for its entire duration, which could be expensive.

### SSE vs WebSockets on Vercel -- Analysis

| Factor | SSE on Vercel | WebSockets on Vercel |
|--------|--------------|---------------------|
| Native support | Partial -- streaming works but connections timeout | NOT supported natively |
| Connection duration | Max 300-800s depending on plan | N/A |
| Bidirectional | No (server-to-client only) | Yes |
| Cost implications | Each connection = 1 function invocation for entire duration | N/A |
| Reconnection | Built into EventSource API | Manual |
| Browser support | All modern browsers | All modern browsers |

### Recommended Approaches for Real-Time on Vercel

**Option A: Third-party real-time service (RECOMMENDED for Vercel)**
- **Pusher Channels**: Managed WebSocket service. Server triggers events via HTTP API, clients subscribe via Pusher client SDK. Works perfectly with serverless because the server side is just an HTTP POST.
- **Ably**: Similar to Pusher but with more features (presence, history, message persistence).
- **Soketi** (self-hosted): Open-source Pusher-compatible server. Would need separate hosting.
- **Supabase Realtime**: If willing to add Supabase, it provides real-time subscriptions over PostgreSQL changes.

**Option B: Polling**
- Simple short polling (GET /api/notifications every 10-30 seconds)
- Works on any serverless platform with zero infrastructure changes
- Higher latency, more API calls, but simpler architecture
- SWR/React Query can handle this elegantly with `refreshInterval`

**Option C: SSE with reconnection**
- Use SSE with automatic reconnection on timeout
- Clients reconnect every ~4 minutes (before 300s limit)
- Works but is wasteful (each connection = 1 function invocation for 4+ minutes)
- Cost could be significant at scale

**Option D: Separate WebSocket server**
- Deploy a dedicated WebSocket server on Railway, Fly.io, Render, or AWS
- Next.js app on Vercel communicates via HTTP to the WS server
- Most complex architecture but most capable

**Option E: PostgreSQL LISTEN/NOTIFY + SSE**
- PostgreSQL has a built-in pub/sub system (LISTEN/NOTIFY)
- Could trigger NOTIFY on INSERT into notifications table
- Problem: Serverless functions can't maintain persistent DB connections to LISTEN
- Would need a persistent process somewhere (back to Option D)

### Prisma Notification Schema Considerations

```prisma
model Notification {
  id        String   @id @default(cuid())
  type      NotificationType
  userId    String   // recipient
  actorId   String   // who triggered it
  postId    String?  // optional, for comment/like notifications
  commentId String?  // optional, for comment notifications
  read      Boolean  @default(false)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  user    User     @relation("notifications", fields: [userId], references: [id])
  actor   User     @relation("notificationActors", fields: [actorId], references: [id])
  post    Post?    @relation(fields: [postId], references: [id])
  comment Comment? @relation(fields: [commentId], references: [id])
}

enum NotificationType {
  COMMENT
  FOLLOW
  LIKE
}
```

Key considerations:
- Need two User relations (recipient and actor) -- requires relation names in Prisma
- Soft delete vs hard delete for dismissed notifications
- Aggregation: "3 people liked your post" vs individual notifications
- Indexing strategy: `userId + read + createdAt` composite index for efficient queries

### Notification Delivery Architecture

Regardless of real-time transport, the system needs:

1. **Write path**: When an action happens (comment, follow, like), create a Notification record in the database
2. **Real-time push**: Notify the recipient that a new notification exists
3. **Read path**: Fetch notifications list, mark as read, get unread count
4. **UI layer**: Bell icon with badge, dropdown/page with notification list

The write path should be decoupled from the API response. Options:
- Inline in the action handler (simpler, but adds latency to comment/follow/like responses)
- Background job via Vercel Cron or Inngest (more robust, no latency impact)
- Database trigger (PostgreSQL function on INSERT)

## External Research

### Vercel Official Documentation Findings

From https://vercel.com/docs/functions/runtimes/edge-runtime:
- Edge Runtime recommends migrating to Node.js for "improved performance and reliability"
- Edge functions must begin response within 25 seconds
- Can stream for up to 300 seconds after initial response
- No native WebSocket API listed in supported APIs

From https://vercel.com/docs/functions/limitations:
- Node.js max duration: 300s (Hobby) to 800s (Pro/Enterprise with Fluid Compute)
- 1,024 file descriptors shared across concurrent executions (limits connection count)
- No mention of WebSocket support for serverless functions
- Streaming is primarily documented for AI/LLM use cases, not persistent notification streams

### Industry Best Practices for Notifications on Serverless

1. **Most common pattern**: Third-party service (Pusher/Ably) for real-time push + database for persistence + polling as fallback
2. **Progressive enhancement**: Start with polling, add real-time later
3. **Notification aggregation**: Batch similar notifications ("Alice and 3 others liked your post")
4. **Notification preferences**: Let users control what they're notified about
5. **Read receipts**: Mark as read on view, not on delivery

## Open Questions

1. **Which Next.js version and router?** App Router vs Pages Router affects API route patterns and server component capabilities.

2. **What authentication system is in use?** Needed to identify the current user for notification delivery and to secure notification endpoints.

3. **What are the existing Prisma models?** Specifically User, Post, Comment, and any follow/like models. Need to understand the existing schema to design the Notification model correctly.

4. **Scale expectations?** How many concurrent users? This heavily influences whether polling is sufficient or a real-time service is needed.

5. **Budget for third-party services?** Pusher/Ably have free tiers but paid plans for scale. Is there budget for this, or does the solution need to be zero-cost?

6. **Is there an existing notification concept?** Any prior work on notifications (even a placeholder UI)?

7. **Notification aggregation needed?** Should "5 people liked your post" be a single notification, or 5 separate ones?

8. **Email/push notifications too, or just in-app?** The user mentioned real-time notifications but didn't specify the channel.

9. **Vercel plan?** Hobby vs Pro affects max function duration and Fluid Compute availability.
