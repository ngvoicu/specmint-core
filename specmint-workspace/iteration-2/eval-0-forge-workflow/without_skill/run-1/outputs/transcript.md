# Transcript: Baseline (Without Skill) - Run 1

## Eval Metadata

- **Eval:** eval-0-forge-workflow
- **Condition:** without_skill
- **Run:** 1
- **Date:** 2026-03-06
- **Model:** claude-opus-4-6

---

## User Prompt

> I need to add real-time notifications to my Next.js app. Users should get notified when someone comments on their post, when they get a new follower, and when their post gets liked. I'm using Prisma with PostgreSQL and the app is deployed on Vercel. I was thinking SSE or WebSockets but I'm not sure which is better for Vercel's serverless setup. Can you forge a spec for this?

---

## Claude's Response (Simulated Without Skill)

Great question -- this is a common architectural decision for Next.js apps on Vercel. Let me break this down for you.

### SSE vs WebSockets on Vercel

**Short answer: Neither SSE nor WebSockets work well with Vercel's serverless functions**, because serverless functions have execution time limits (typically 10-60 seconds depending on your plan) and don't maintain persistent connections.

Here's the comparison:

| Approach | Vercel Compatibility | Notes |
|----------|---------------------|-------|
| WebSockets | Not supported | Vercel serverless functions can't hold open WebSocket connections |
| SSE (Server-Sent Events) | Partially works | Limited by function timeout; connections drop and must reconnect |
| Polling | Works but inefficient | Simple to implement, wastes resources |
| Third-party real-time service | Best option | Pusher, Ably, Supabase Realtime, or similar |

### Recommended Architecture

For a Vercel-deployed Next.js app, I'd recommend one of these approaches:

**Option A: Pusher (or Ably)**
- Use Pusher Channels for real-time delivery
- Your API routes trigger Pusher events when actions happen (comment, follow, like)
- Client subscribes to a user-specific channel
- Pusher handles the persistent connection

**Option B: Supabase Realtime**
- If you're open to adding Supabase alongside Prisma/PostgreSQL
- Supabase can listen to PostgreSQL changes and push them to clients
- But this adds complexity since you're already using Prisma

**Option C: Vercel with a separate WebSocket server**
- Deploy a small WebSocket server on Railway, Fly.io, or Render
- Your Vercel API routes notify the WebSocket server
- WebSocket server pushes to connected clients
- More infrastructure to manage

### Data Model

Here's a Prisma schema addition for notifications:

```prisma
model Notification {
  id        String   @id @default(cuid())
  type      NotificationType
  userId    String   // recipient
  actorId   String   // who triggered it
  postId    String?  // relevant post (for comments/likes)
  read      Boolean  @default(false)
  createdAt DateTime @default(now())

  user  User  @relation("notifications", fields: [userId], references: [id])
  actor User  @relation("actorNotifications", fields: [actorId], references: [id])
  post  Post? @relation(fields: [postId], references: [id])

  @@index([userId, read])
  @@index([userId, createdAt])
}

enum NotificationType {
  COMMENT
  FOLLOW
  LIKE
}
```

### Implementation Sketch

1. **Create notification on action** -- In your existing API routes for comments, follows, and likes, add a step to create a Notification record and trigger a Pusher event.

2. **Client-side subscription** -- Use the Pusher client SDK to subscribe to `private-user-{userId}` and listen for new notification events.

3. **Notification UI** -- Bell icon with unread count badge, dropdown with notification list, mark-as-read on click.

4. **API routes needed:**
   - `GET /api/notifications` -- fetch paginated notifications
   - `PATCH /api/notifications/[id]` -- mark as read
   - `PATCH /api/notifications/read-all` -- mark all as read

Want me to start implementing any of these? I can begin with the Prisma schema changes and the notification creation logic, or we can start with the real-time delivery layer first.

---

## Analysis

### What Claude Did

1. **Answered the technical question directly** -- Compared SSE, WebSockets, and alternatives for Vercel's serverless environment.
2. **Recommended an architecture** -- Suggested Pusher as the primary option with alternatives listed.
3. **Provided a data model** -- Gave a Prisma schema snippet for notifications.
4. **Sketched an implementation** -- Listed the high-level steps and API routes.
5. **Asked what to do next** -- Offered to start implementing immediately.

### What Claude Did NOT Do

1. **No persistent spec created** -- Nothing was written to disk. The plan exists only in this chat session.
2. **No structured research phase** -- Claude jumped straight to recommendations without exploring the codebase to understand existing patterns, auth setup, or current schema.
3. **No interview/clarification phase** -- Claude made assumptions without asking:
   - What Vercel plan (affects function timeout limits)?
   - Is there an existing notification system or UI pattern?
   - What's the expected notification volume?
   - Should notifications be grouped/batched (e.g., "5 people liked your post")?
   - Are there email/push notification requirements beyond in-app?
   - What's the existing auth setup (needed for Pusher private channels)?
   - Is there a preference for third-party services vs self-hosted?
   - What's the budget for a real-time service?
   - Should notifications persist after being read, or be deletable?
   - Are there any existing real-time features in the app?
4. **No task breakdown with tracking** -- No checkboxes, task codes, or progress tracking.
5. **No decision log** -- The SSE vs WebSocket analysis is inline text, not a structured record that persists.
6. **No resume capability** -- If the session ends, all context is lost. Starting a new session means re-explaining everything.
7. **No phased implementation plan** -- No ordering of tasks, no dependency analysis, no definition of done.
8. **No codebase exploration** -- Claude didn't read any existing files to understand the app's current structure, patterns, or constraints.

### Key Gaps vs. a Spec-Driven Workflow

| Capability | Without Skill | With Spec Workflow |
|-----------|--------------|-------------------|
| Persistent plan | No (chat only) | Yes (.specs/SPEC.md) |
| Research phase | None | Deep codebase + web research |
| Clarifying questions | None (assumptions) | Structured interview rounds |
| Task tracking | None | Coded tasks with checkboxes |
| Resume after break | Lost context | Full resume from SPEC.md |
| Decision log | Inline text | Structured table |
| Multi-session work | Cannot continue | Designed for it |
| Progress visibility | None | Status markers, registry |
| Scope control | Vague | Explicit phases with boundaries |
