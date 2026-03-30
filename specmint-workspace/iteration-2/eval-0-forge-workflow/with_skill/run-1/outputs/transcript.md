# Forge Workflow Transcript — Real-Time Notifications

## Date: 2026-03-06

## User Prompt

> "I need to add real-time notifications to my Next.js app. Users should get notified when someone comments on their post, when they get a new follower, and when their post gets liked. I'm using Prisma with PostgreSQL and the app is deployed on Vercel. I was thinking SSE or WebSockets but I'm not sure which is better for Vercel's serverless setup. Can you forge a spec for this?"

---

## Step 1: Setup

**Trigger detected:** User said "forge a spec" — this activates the forge workflow per SKILL.md.

**Spec ID generated:** `real-time-notifications`
- Derived from title "Real-Time Notifications" (lowercase, hyphenated)

**Collision check:** No existing `.specs/` directory or registry. No collision.

**Actions taken:**
1. Created directory: `.specs/real-time-notifications/`
2. Initialized `.specs/registry.md` with empty table headers

**Files created:**
- `.specs/registry.md` — empty registry initialized
- `.specs/real-time-notifications/` — directory created

---

## Step 2: Deep Research (Phase 1 of Forge)

### 2a. Codebase Research

No existing codebase was available to scan. The user described their stack but did not provide project file access. Research is based on the described technology stack:

- **Framework:** Next.js (App Router assumed) deployed on Vercel
- **ORM:** Prisma
- **Database:** PostgreSQL (hosting provider unknown)
- **Deployment:** Vercel (serverless functions)

Since there is no codebase, the research focused heavily on external/architectural research.

### 2b. Web Research

Web search and fetch tools were unavailable (permission denied). Research was conducted from existing knowledge of the Vercel platform, SSE, WebSockets, and Next.js real-time patterns. This knowledge is well-established and current through early 2025.

**Key findings on SSE vs WebSockets on Vercel:**

#### WebSockets: NOT SUPPORTED on Vercel Serverless
- Vercel serverless functions are request-response oriented
- WebSocket connections require persistent, long-lived server processes
- Vercel's infrastructure terminates idle connections aggressively
- **Verdict:** WebSockets cannot be used directly on Vercel without an external service or separate server

#### SSE: PARTIALLY SUPPORTED on Vercel
- Vercel supports streaming responses, enabling SSE
- Hard timeout limits apply:
  - Hobby: 10s (streaming extends to ~25s)
  - Pro: 60s (streaming extends to ~300s)
  - Enterprise: configurable up to 900s
- After timeout, connection drops and client must reconnect
- Each reconnection = new function invocation = cost
- Viable but creates periodic gaps where events can be missed

#### Third-Party Real-Time Services: RECOMMENDED APPROACH
- Pusher, Ably, Supabase Realtime, Soketi are all viable
- Pattern: API route writes notification to DB + pushes to service; client subscribes via service SDK
- Truly real-time, no reconnection gaps, no timeout issues
- Additional cost and dependency

#### Polling: SIMPLEST APPROACH
- Client fetches `/api/notifications` every N seconds
- Works perfectly with serverless
- Latency = polling interval
- Many production apps (including GitHub) use this pattern

**Four architecture patterns identified:**
- Pattern A: SSE with reconnection (no external service)
- Pattern B: Third-party push service (Pusher/Ably)
- Pattern C: Supabase Realtime (if using Supabase for Postgres)
- Pattern D: Polling + optimistic UI (simplest, enhancement path later)

**Notification data model drafted** — Prisma schema for a `Notification` model with `userId`, `actorId`, `type` (enum: COMMENT, FOLLOW, LIKE), `entityId`, `entityType`, `read` flag, and proper indexes.

### 2c. Research Saved

All findings saved to `.specs/real-time-notifications/research-01.md`

---

## Step 3: Interview Round 1 (Phase 2 of Forge)

### Research Summary Presented to User

Here is what I found and what I would present to the user:

---

**Research Summary:**

I've researched the real-time notification landscape for your Next.js + Prisma + PostgreSQL + Vercel stack. The key finding is that **Vercel does not support native WebSocket connections** in serverless functions — they require persistent server processes that Vercel's architecture doesn't provide. SSE is partially supported through streaming responses, but connections are forcefully terminated at the function timeout limit (60 seconds on Pro, 10 seconds on Hobby), requiring periodic reconnection.

The most reliable approaches for real-time on Vercel are: (1) use a third-party push service like Pusher or Ably that handles the WebSocket infrastructure while your Vercel API routes just trigger events, (2) use Supabase Realtime if your PostgreSQL is hosted on Supabase, or (3) use polling as a simpler baseline that can be enhanced later. SSE with reconnection is also viable but has trade-offs around missed events during reconnection windows.

For the notification data model, I've drafted a Prisma `Notification` model with all three trigger types (COMMENT, FOLLOW, LIKE), actor tracking, read status, and proper database indexes for efficient querying.

**Assumptions (based on typical Next.js + Vercel setups):**
- You're using the App Router (not Pages Router)
- You have some form of authentication already in place (NextAuth, Clerk, or similar)
- The notification system is greenfield (no existing notification model)
- You want in-app notifications (bell icon with dropdown) as the primary interface

**Questions:**

1. **What is your PostgreSQL hosting provider?** (Supabase, Neon, AWS RDS, other?) If you're on Supabase, its built-in Realtime feature would be the simplest path — subscribe to INSERT events on a notifications table with zero additional infrastructure. If you're on Neon or another provider, we'd need a different transport.

2. **How critical is truly instant delivery?** For a social app like Twitter/Instagram, notifications arrive within 1-2 seconds. Is that level of immediacy required, or would a 10-30 second polling delay be acceptable for your use case? This significantly changes the architecture complexity.

3. **What's your expected concurrent user count?** (rough order of magnitude: tens, hundreds, thousands, tens of thousands?) This determines whether a third-party service like Pusher makes sense cost-wise, or if SSE with reconnection is sufficient.

4. **Should notifications be grouped?** For example, if 5 people like a post in quick succession, should the user see "Alice, Bob, and 3 others liked your post" or 5 separate notifications?

5. **In-app only, or also browser push notifications and/or email digests?** If browser push (Web Push API) is needed, that's a separate subsystem. Email digests add another layer. Want to scope this spec to in-app only and add the others later?

6. **Is there an existing notification model in your Prisma schema, or is this greenfield?** Also, do you already have any real-time infrastructure (WebSocket server, Pusher account, etc.)?

**Proposed rough approach:**

Given the Vercel constraint, I'd lean toward **Pattern B (third-party push service)** as the primary recommendation, with **polling as a fallback/initial implementation**. The flow would be:

1. Build the notification data model and persistence layer first (Prisma + PostgreSQL)
2. Build API routes for creating notifications (triggered on comment/follow/like)
3. Build the notification UI (bell icon, dropdown, unread count)
4. Start with polling (simple, works immediately)
5. Add real-time delivery via Pusher/Ably/Supabase Realtime
6. Add mark-as-read and notification preferences

This approach lets you ship a working notification system quickly (polling) and layer on real-time delivery without rewriting the core logic.

What do you think about this approach? And answers to the questions above will help me nail down the specific implementation details.

---

### Interview Saved

Questions and pending answers saved to `.specs/real-time-notifications/interview-01.md`

---

## Current Status: WAITING FOR USER INPUT

The forge workflow has completed:
- [x] Step 1: Setup (spec ID, directory, registry)
- [x] Step 2: Deep Research (saved to `research-01.md`)
- [x] Step 3: Interview Round 1 (questions presented, saved to `interview-01.md`)
- [ ] Step 4: Deeper Research (pending user answers)
- [ ] Step 5: Write SPEC.md (pending)
- [ ] Step 6: Present spec for approval (pending)

**The workflow is paused at the Interview Round 1 gate.** Per the forge workflow rules: "STOP after presenting questions. Wait for the user to answer before proceeding. Do not answer your own questions, do not assume answers, and do not continue to Step 4 or Step 5 until the user has responded."

---

## Files Created

| File | Purpose |
|------|---------|
| `.specs/registry.md` | Initialized empty spec registry |
| `.specs/real-time-notifications/research-01.md` | Deep research findings |
| `.specs/real-time-notifications/interview-01.md` | Interview round 1 questions (awaiting answers) |
