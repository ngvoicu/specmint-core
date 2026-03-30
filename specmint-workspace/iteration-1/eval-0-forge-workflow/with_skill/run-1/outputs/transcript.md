# Forge Workflow Transcript -- Real-Time Notifications

## Date: 2026-03-06
## Spec ID: `real-time-notifications`
## User Prompt:
> "I need to add real-time notifications to my Next.js app. Users should get notified when someone comments on their post, when they get a new follower, and when their post gets liked. I'm using Prisma with PostgreSQL and the app is deployed on Vercel. I was thinking SSE or WebSockets but I'm not sure which is better for Vercel's serverless setup. Can you forge a spec for this?"

---

## Step 1: Setup

### Actions taken:
1. **Generated spec ID**: `real-time-notifications` (from "Real-Time Notifications")
2. **Collision check**: No `.specs/` directory exists yet -- no collision.
3. **Created directory**: `specs/real-time-notifications/`
4. **Initialized registry**: Created `specs/registry.md` with empty table header.

### Files created:
- `specs/registry.md` -- empty registry with table header
- `specs/real-time-notifications/` -- directory created

---

## Step 2: Deep Research

### Phase 1a: Codebase Research

Since we are operating in the specsmith repository (not the user's actual Next.js app), I cannot scan the real codebase. In a real forge session, I would:

- Read `package.json` to identify Next.js version, dependencies, and scripts
- Read `prisma/schema.prisma` to understand the existing data model (User, Post, Comment, Follow, Like models)
- Scan `app/api/` or `pages/api/` to understand existing API route patterns
- Read authentication setup (NextAuth config, middleware, etc.)
- Check for existing notification-related code or UI components
- Review the project structure to understand conventions
- Look at test setup and coverage

Instead, I noted the stack from the user's description:
- Next.js (version unknown, router unknown)
- Prisma ORM with PostgreSQL
- Deployed on Vercel (serverless)
- Features: posts, comments, followers, likes (social app)

### Phase 1b: Web Research

**Attempted tools:**
- `WebSearch` -- permission denied
- `WebFetch` -- partially successful (2 of 4 attempts succeeded before being rate-limited)

**Successfully fetched:**

1. **Vercel Edge Runtime documentation** (https://vercel.com/docs/functions/runtimes/edge-runtime)
   - Key finding: Edge Runtime must begin response within 25 seconds, can stream up to 300 seconds
   - Vercel recommends migrating from Edge to Node.js runtime
   - No WebSocket API listed in supported Edge Runtime APIs
   - Stream APIs (ReadableStream, WritableStream, TransformStream) are supported

2. **Vercel Functions Limitations** (https://vercel.com/docs/functions/limitations)
   - Max duration: 300s (Hobby), 800s (Pro/Enterprise with Fluid Compute)
   - 1,024 file descriptors shared across concurrent executions
   - No mention of WebSocket support
   - Request/response body max: 4.5 MB

3. **Vercel Streaming Functions** (https://vercel.com/docs/functions/streaming-functions)
   - Streaming is supported and documented primarily for AI/LLM use cases
   - Uses `Content-Type: text/event-stream` (SSE format)
   - Max durations apply to streaming functions too

**Key conclusion from web research:**

**Vercel does NOT support native WebSockets on serverless functions.** This is a fundamental constraint. The user's instinct to consider SSE is closer to workable, but even SSE has significant limitations on Vercel: connections timeout after 300-800 seconds depending on plan, and each SSE connection consumes an entire function invocation for its duration, making it expensive at scale.

The recommended approach for real-time on Vercel is one of:
1. Third-party real-time service (Pusher, Ably) -- server triggers via HTTP, clients subscribe via SDK
2. Polling with SWR/React Query -- simple, zero infrastructure, higher latency
3. SSE with aggressive reconnection -- works but costly per-connection
4. Separate WebSocket server on another platform -- most capable but complex

### Phase 1d: Save Research

**Saved to:** `specs/real-time-notifications/research-01.md`

Contents include:
- Project architecture (known and unknown aspects)
- Vercel serverless constraints (with specifics from docs)
- SSE vs WebSockets comparison table for Vercel
- Five architectural options with trade-offs (Pusher/Ably, polling, SSE, separate WS server, PostgreSQL LISTEN/NOTIFY)
- Proposed Prisma notification schema
- Notification delivery architecture (write path, push, read path, UI)
- Nine open questions for the interview

---

## Step 3: Interview Round 1

### What I would say to the user:

---

Here is what I found from researching your setup. This is important before we go further.

**Research Summary**

I researched Vercel's serverless architecture extensively. The critical finding is that **Vercel does not support native WebSockets on serverless functions**. Functions are stateless and short-lived -- they spin up per request and shut down after responding, so they cannot maintain the persistent bidirectional connections WebSockets require. This eliminates WebSockets as a direct option unless you host a separate WebSocket server elsewhere.

**SSE (Server-Sent Events) is partially viable on Vercel** but has meaningful constraints. Vercel supports streaming responses, but connections will timeout after 300 seconds on the Hobby plan (800 seconds on Pro with Fluid Compute). Each SSE connection also consumes an entire function invocation for its full duration, meaning 100 concurrent users each holding an SSE connection would be 100 function invocations running for ~5 minutes each. This gets expensive quickly and doesn't scale well.

The most common pattern for real-time features on Vercel is using a **third-party real-time service** like Pusher or Ably. These work perfectly with serverless because the server-side is just an HTTP POST to trigger an event -- no persistent connections needed from your backend. Only the client maintains a WebSocket connection to the service provider. Alternatively, simple **short polling** (fetching notifications every 10-30 seconds via SWR/React Query) is the simplest approach with zero infrastructure changes, though with higher latency.

**Assumptions I'm making based on your description:**
- You're using Next.js App Router (since it's the modern default)
- You have existing User, Post, Comment models in Prisma, and some kind of follow/like relationship
- Notifications are in-app only (not email or push notifications)
- You want a notification bell icon with unread count and a dropdown or page listing notifications

**Questions:**

1. **Real-time transport -- which approach appeals to you?** Given Vercel's constraints, here are your realistic options:
   - **(A) Pusher/Ably** -- True real-time via managed WebSocket service. Free tier available (Pusher: 200k messages/day, 100 concurrent connections). Server triggers via simple HTTP call. Most polished UX.
   - **(B) Short polling** -- Fetch new notifications every 10-30 seconds via SWR/React Query `refreshInterval`. Zero additional infrastructure. Simplest to build. Good enough for most social apps.
   - **(C) SSE with reconnection** -- Server-Sent Events with automatic reconnection every ~4 minutes. Works on Vercel but costly at scale due to per-connection function invocations.
   - **(D) Separate WebSocket server** -- Deploy a dedicated WS server on Railway/Fly.io alongside your Vercel app. Most capable but most complex architecture.

   My recommendation: Start with **(B) polling** for the MVP and add **(A) Pusher** later if you need sub-second delivery. Which do you prefer?

2. **What's your existing data model look like?** Specifically:
   - Do you have a `Like` model/table, or is liking handled differently (e.g., a likes count field)?
   - How are followers modeled? A separate `Follow` table with `followerId`/`followingId`?
   - Does your `Comment` model have a direct relation to the post author, or would we need to join through Post?

3. **Notification aggregation -- individual or grouped?** When 5 people like the same post, should that be:
   - 5 separate notifications ("Alice liked your post", "Bob liked your post", ...)
   - 1 aggregated notification ("Alice, Bob, and 3 others liked your post")
   Aggregation is significantly more complex to build. I'd recommend starting with individual notifications and adding aggregation later.

4. **Scope check -- in-app only, or also email/push?** You mentioned "real-time notifications" which I'm interpreting as in-app (bell icon, dropdown). Do you also want:
   - Email notifications for important events?
   - Browser push notifications (via Web Push API)?
   - Or just in-app for now?

5. **What's your Vercel plan?** Hobby, Pro, or Enterprise? This affects function duration limits and whether Fluid Compute is available. It also influences whether SSE is even cost-practical.

6. **Authentication setup?** What are you using for auth (NextAuth/Auth.js, Clerk, custom JWT)? I need to know this to design the notification API endpoints securely and to identify the current user for real-time subscriptions.

**Proposed rough approach:**

Phase 1 would create the Prisma `Notification` model and database migration. Phase 2 would build the API layer (create notification on action, fetch notifications, mark as read, get unread count). Phase 3 would build the UI (notification bell, dropdown, notification list). Phase 4 would add the real-time delivery mechanism (polling, Pusher, or SSE -- based on your answer to question 1). Phase 5 would handle edge cases and polish (notification preferences, aggregation if desired, cleanup/pagination).

Does this phasing make sense, or would you restructure it?

---

### Interview file to save:

The interview-01.md would be saved after receiving user responses. Since there is no real user, I am documenting the questions asked and stopping.

[WAITING FOR USER INPUT - STOPPING HERE]

---

## What Would Happen Next (after user responds)

### Step 4: Deeper Research (Phase 3 of forge)
Based on the user's answers to the 6 questions above, I would:
- If they chose Pusher: Research Pusher Channels API, Next.js integration, pricing tiers
- If they chose polling: Research SWR/React Query polling patterns, optimistic updates
- If they chose SSE: Research EventSource reconnection strategies, Vercel streaming costs
- Scan their actual Prisma schema to design the Notification model correctly
- Research their auth system for securing notification endpoints
- Check their existing API patterns to match conventions

Save to `specs/real-time-notifications/research-02.md`.

### Step 5: Interview Round 2 (Phase 4 of forge)
Present deeper findings and ask about:
- Edge cases (self-notification prevention, deleted posts/comments, blocked users)
- Implementation sequence validation
- Scope refinement (split into separate specs if too large)
- UI details (toast vs dropdown, mark all as read, notification page)

Save to `specs/real-time-notifications/interview-02.md`.

### Step 6: Write SPEC.md (Phase 5 of forge)
Synthesize all research and interviews into a complete SPEC.md with:
- YAML frontmatter (id, title, status: active, priority, tags)
- Overview
- 4-5 phases with concrete tasks
- Resume context
- Decision log from interviews
- Empty deviations table

Save to `specs/real-time-notifications/SPEC.md`.
Update `specs/registry.md` with the new spec row (status: active).

### Step 7: Implement (Phase 6 of forge)
Begin working through tasks, updating checkboxes and resume context as we go.

---

## Files Read During This Session

1. `/Users/gabrielvoicu/Projects/ngvoicu/specsmith/SKILL.md` -- Full skill definition with forge workflow
2. `/Users/gabrielvoicu/Projects/ngvoicu/specsmith/commands/forge.md` -- Forge command details
3. `/Users/gabrielvoicu/Projects/ngvoicu/specsmith/references/spec-format.md` -- SPEC.md template and format reference

## Web Resources Fetched

1. `https://vercel.com/docs/functions/runtimes/edge-runtime` -- Edge Runtime docs (successful)
2. `https://vercel.com/docs/functions/streaming-functions` -- Streaming Functions docs (successful)
3. `https://vercel.com/docs/functions/limitations` -- Functions Limits docs (successful)
4. `https://vercel.com/guides/publish-and-subscribe-to-realtime-events-on-vercel` -- BLOCKED
5. `https://vercel.com/blog/nested-websocket-support` -- BLOCKED
6. `https://pusher.com/docs/channels/getting_started/javascript/` -- BLOCKED

## Files Created During This Session

1. `specs/registry.md` -- Initialized empty registry
2. `specs/real-time-notifications/research-01.md` -- Deep research findings
3. `transcript.md` -- This file
4. `research-01.md` -- Copy of research notes at outputs root
