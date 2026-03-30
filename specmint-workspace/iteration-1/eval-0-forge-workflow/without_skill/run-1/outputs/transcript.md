# Transcript -- Forge Workflow: Real-Time Notifications

## Date: 2026-03-06

## User Prompt

> I need to add real-time notifications to my Next.js app. Users should get notified when someone comments on their post, when they get a new follower, and when their post gets liked. I'm using Prisma with PostgreSQL and the app is deployed on Vercel. I was thinking SSE or WebSockets but I'm not sure which is better for Vercel's serverless setup. Can you forge a spec for this?

---

## Phase 1: Research

### What I Did

Since I don't have access to the user's Next.js codebase (I'm working in the specsmith repository), I performed domain research based on the stated tech stack: Next.js + Prisma + PostgreSQL + Vercel.

I attempted web searches for current best practices on real-time notifications with Vercel's serverless architecture but WebSearch was unavailable. I proceeded with my existing knowledge of the platform constraints and common patterns.

### Key Research Findings

**The core constraint**: Vercel is serverless. This fundamentally limits real-time options:

1. **WebSockets**: Not supported on Vercel serverless functions. The platform cannot maintain persistent WebSocket connections. This is a non-starter without an external service.

2. **SSE (Server-Sent Events)**: Partially possible. Vercel serverless functions have execution time limits (10s Hobby, 60s Pro, 300s Enterprise), so long-lived SSE connections will be terminated. Edge Functions offer streaming but still have timeout constraints.

3. **Third-party real-time services** (Pusher, Ably, Novu, Knock): The standard solution for Vercel deployments. Offload the persistent connection management to a service designed for it.

4. **Polling**: The simplest approach. No infrastructure changes. Higher latency but perfectly Vercel-compatible. Good enough for notifications where 5-15 second delay is acceptable.

5. **Hybrid**: Use polling with optional upgrade to a third-party service for instant delivery.

**Notification data model**: Needs a `Notification` table in PostgreSQL with Prisma, notification type enum (COMMENT, FOLLOW, LIKE), and associations to the triggering entities.

Full research saved to: `research-01.md` (in the same outputs directory).

---

## Phase 2: Interview Round 1

### What I Would Say to the User

Here's what I found and the questions I need answered before writing the spec:

---

**Research Summary**

I researched the real-time delivery options for your Vercel + Next.js stack. The key finding is that neither WebSockets nor traditional SSE will work well on Vercel's serverless architecture. WebSockets are flat-out unsupported -- Vercel serverless functions can't maintain persistent connections. SSE is technically possible but your connections will be killed when the function times out (10s on Hobby, 60s on Pro).

The standard approach for real-time features on Vercel falls into two camps:

- **Third-party real-time service** (Pusher, Ably, or a notification-specific platform like Novu): You create notifications in your DB, then push them to a channel. The client subscribes via the service's SDK. This gives you true real-time delivery.
- **Polling**: Client fetches `/api/notifications` every N seconds. Simple, no extra infrastructure, but notifications arrive with a delay equal to your poll interval.

A hybrid approach is also possible: start with polling, add a real-time service later if latency matters.

**My assumptions based on common patterns:**

- You're using the App Router (Next.js 13+)
- You have existing `User`, `Post`, `Comment`, `Like`, and `Follow` (or similar) models in your Prisma schema
- Notifications should appear in-app (bell icon / dropdown), not email/SMS/push (at least for v1)
- Notification delivery within a few seconds is acceptable (not sub-100ms)

**Questions:**

1. **Real-time requirement**: How fast do notifications need to arrive? Is a 5-10 second polling delay acceptable for v1, or do you need instant (sub-second) delivery? This is the biggest architectural decision -- it determines whether you need a third-party service or can start with simple polling.

2. **Existing data model**: Do you already have `User`, `Post`, `Comment`, `Like`, and `Follow` models in your Prisma schema? And is there any existing notification infrastructure, or is this completely greenfield?

3. **Next.js version and router**: Are you on the App Router (Next.js 13+) or Pages Router? This affects how we structure the API routes and real-time subscription hooks.

4. **Notification scope**: For v1, is this in-app only (bell icon, dropdown/page)? Or do you also need email notifications, push notifications, or other channels?

5. **Notification grouping and batching**: Should notifications be individual ("Alice liked your post", "Bob liked your post") or grouped ("Alice and 2 others liked your post")? Grouping adds significant complexity.

6. **Third-party service budget**: If instant delivery is important, are you open to using a service like Pusher (free tier: 200k messages/day, 100 concurrent connections) or would you prefer to keep the stack dependency-free?

---

[WAITING FOR USER INPUT - STOPPING HERE]

---

## What Would Happen Next (Planned Workflow)

After receiving the user's answers to the interview questions, the forge workflow would continue:

### Phase 3: Deeper Research (informed by interview)

Based on the user's answers, I would:
- If they choose a third-party service: research the specific service's Next.js integration, pricing tiers, and Prisma webhook patterns
- If they choose polling: research optimal polling strategies, SWR/React Query integration for Next.js
- Look up their specific Prisma model structure to design the Notification schema
- Research notification grouping algorithms if they want grouped notifications
- Check their Next.js version for App Router vs Pages Router patterns

### Phase 4: Interview Round 2

Present deeper findings, ask about:
- Specific trade-offs discovered (e.g., Pusher vs Ably vs Novu)
- Edge cases: self-notifications, duplicate notifications, notification for deleted content
- UI specifics: unread count badge, mark-all-as-read, notification preferences
- Implementation sequence and phasing

### Phase 5: Write SPEC.md

Synthesize all research and interview answers into a structured spec with:
- YAML frontmatter (id: `real-time-notifications`, status: active)
- Overview capturing the goal and constraints
- Phases (likely 4-5): Database schema, API layer, Real-time delivery, UI components, Polish/edge cases
- Concrete tasks with file paths and function names
- Decision log with all architectural choices and rationale
- Resume context for cold-start implementation

### Phase 6: Implement

Work through the spec tasks, checking off each one, updating the SPEC.md as we go.

---

## Draft Spec (Pre-Interview)

Based on research alone, here's what the spec would likely look like. This would be refined significantly after the interview.

**Probable spec ID**: `real-time-notifications`
**Probable task prefix**: `NTF`

**Probable phases:**

1. **Database & Models** -- Notification model in Prisma, migration, seed data
2. **API Layer** -- CRUD endpoints for notifications (list, mark-read, count)
3. **Notification Triggers** -- Create notifications when comments/likes/follows happen
4. **Real-Time Delivery** -- Polling or third-party service integration (depends on interview)
5. **UI Components** -- Bell icon, dropdown, notification list, unread badge
6. **Polish & Edge Cases** -- Grouping, pagination, preferences, cleanup

---

## Files Created

- `/Users/gabrielvoicu/Projects/ngvoicu/specsmith/specsmith-workspace/iteration-1/eval-0-forge-workflow/without_skill/run-1/outputs/research-01.md` -- Full research document
- `/Users/gabrielvoicu/Projects/ngvoicu/specsmith/specsmith-workspace/iteration-1/eval-0-forge-workflow/without_skill/run-1/outputs/transcript.md` -- This transcript

## Notes

- No SPEC.md was written because the forge workflow requires completing the interview loop before writing the spec. Writing a spec without user input on the key architectural decisions (polling vs third-party, notification grouping, scope) would produce a spec that needs revision mid-build -- exactly what the forge workflow is designed to prevent.
- No `.specs/` directory was created because we haven't reached the Setup phase (which comes after interviews are complete).
- WebSearch was unavailable, so research was based on existing knowledge of Vercel's serverless constraints, Next.js patterns, and real-time notification architectures.
