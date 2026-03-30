# Forge Transcript — Real-Time Notifications

## Preflight

**Spec ID**: `real-time-notifications`
**Collision check**: No existing spec with this ID. Proceeding.
**Directory created**: `.specs/real-time-notifications/`
**Registry initialized**: `.specs/registry.md`

---

## Phase 1: Deep Research

I conducted deep research into real-time notification architectures for Next.js applications deployed on Vercel with Prisma and PostgreSQL. External research tools (WebSearch, WebFetch, Context7) were unavailable, so findings are based on thorough knowledge of the Vercel serverless model, Next.js streaming capabilities, and the real-time service ecosystem.

Research saved to `.specs/real-time-notifications/research-01.md`.

---

## Phase 2: Interview Round 1

### Research Summary

The central challenge here is that **Vercel's serverless architecture fundamentally limits your real-time options**. Serverless functions are stateless and short-lived (60s on Hobby, 300s on Pro), which means they cannot maintain persistent connections the way a traditional server can.

**SSE on Vercel** is technically possible using Route Handlers with `ReadableStream` and `text/event-stream`, but it is effectively **polling in disguise**. Each SSE connection is a function invocation that must poll the database for new notifications during its lifetime. When the function times out (60-300s), the client's `EventSource` auto-reconnects, spinning up a new function. There is no way for a separate function invocation (the one handling "someone just commented") to push an event into an existing SSE stream on another invocation -- they are isolated processes. At scale, this means N concurrent users = N concurrent function invocations, each polling the DB every few seconds.

**WebSockets are not supported** on Vercel serverless functions at all. The serverless model does not support the HTTP upgrade handshake needed for WebSocket connections. If you want true WebSockets, you would need to run a separate persistent server on Railway, Fly.io, or similar -- which adds operational complexity.

**The industry-standard pattern for real-time on Vercel** is to use a managed real-time service like **Pusher Channels**, **Ably**, or **Supabase Realtime**. The flow is: your API route handles the action (comment, follow, like), writes to the database via Prisma, then triggers an event on the real-time service. The client subscribes to a private channel on the service and receives the event instantly. No long-lived connections on Vercel, no polling, true push delivery.

### Assumptions

Based on your description, I am making the following assumptions. Please correct any that are wrong:

1. **You are using Next.js App Router** (not Pages Router), since you mentioned Vercel deployment and this is the current standard.
2. **The social features (posts, comments, followers, likes) already exist** in your app with working Prisma models and API routes/server actions. We are adding notifications on top, not building the social features themselves.
3. **In-app notifications are the primary scope** -- a notification bell with a dropdown and/or a notifications page. We are not building email or mobile push notifications in this spec (though the architecture should not preclude adding them later).
4. **You do not currently have a notification model** in your Prisma schema -- this is a net-new feature.
5. **The app uses some form of authentication** (NextAuth, Clerk, or similar) so we can identify the logged-in user for notification delivery and channel authorization.

### Questions

I have **5 targeted questions** that my research could not answer. Your answers will determine the architecture and shape the spec:

**1. Real-time transport: Managed service or SSE?**

Given Vercel's constraints, I strongly recommend **Pusher Channels** (or Ably as an alternative). The free tier covers 200K messages/day and 100 concurrent connections -- enough for development and early production. You can switch to self-hosted **Soketi** (Pusher-compatible) later if costs grow.

However, if you want to avoid a third-party dependency entirely, SSE with polling is viable for small scale (under ~100 concurrent users). It is simpler but less efficient and not truly real-time.

**Which direction do you prefer?**
- (a) Managed real-time service (Pusher/Ably) -- true real-time push, recommended
- (b) SSE with database polling -- simpler, no third-party, but limited at scale
- (c) Simple short-polling (fetch every N seconds) -- simplest, no real-time feel
- (d) Something else you had in mind?

**2. Notification grouping and display: individual or batched?**

When 5 people like the same post in quick succession, should the user see:
- (a) **5 individual notifications**: "Alice liked your post", "Bob liked your post", ...
- (b) **1 grouped notification**: "Alice, Bob, and 3 others liked your post" (more complex to implement -- requires aggregation logic and updating existing notification records)

Grouping looks better in the UI but adds significant implementation complexity (deduplication, count updates, re-rendering grouped items when new actors are added).

**3. What does your current authentication setup look like?**

The notification system needs to:
- Know who the current user is (to deliver their notifications)
- Authorize real-time channel subscriptions (so users cannot listen to others' notifications)
- Associate actors with actions

Are you using **NextAuth.js (Auth.js)**, **Clerk**, **Supabase Auth**, or something custom? This affects how we secure the real-time channels and fetch the current user in API routes.

**4. What UI component library are you using, if any?**

For the notification bell, dropdown, toast, and notification page, are you using:
- (a) **shadcn/ui** (Radix-based)
- (b) **Radix UI** directly
- (c) **Another component library** (MUI, Ant Design, Chakra, etc.)
- (d) **Custom components** / Tailwind only

This determines whether we can leverage existing Popover, DropdownMenu, and Toast primitives or need to build them.

**5. Should notifications trigger beyond in-app?**

Right now you mentioned in-app notifications. Should this spec also include:
- (a) **Email notifications** for certain events (e.g., new follower, comment on your post) -- requires an email service (Resend, SendGrid, etc.)
- (b) **Browser push notifications** (Web Push API) -- works even when the tab is closed
- (c) **In-app only** for this spec, with architecture that allows adding email/push later

This significantly affects the scope. I would recommend (c) for this spec -- build the notification infrastructure and in-app delivery first, then add email/push as a follow-up spec.

### Proposed Rough Approach

Pending your answers, here is the direction I am leaning:

```
User Action (comment/follow/like)
  --> Next.js API Route / Server Action
    --> 1. Execute the action (Prisma write)
    --> 2. Create Notification record (Prisma)
    --> 3. Trigger real-time event (Pusher)
  --> Client (subscribed to private-user-{userId} channel)
    --> Receives event
    --> Updates notification bell count
    --> Shows toast notification
    --> Prepends to notification dropdown/page
```

**Database**: A `Notification` model in Prisma with a polymorphic entity reference pattern (type + entityType + entityId), indexed on `(recipientId, read, createdAt)`.

**Real-time**: Pusher Channels with private channels per user. Auth endpoint in Next.js to verify channel subscriptions.

**UI**: Notification bell with unread count badge, dropdown with recent notifications, full notifications page with pagination, toast for real-time events.

**Phases** (rough):
1. Database schema and notification service
2. Real-time transport integration
3. Hook into existing actions (comment, follow, like)
4. Notification UI (bell, dropdown, toasts, page)
5. Polish (mark as read, preferences, testing)

Does this direction feel right? What would you change?

---

**Waiting for your answers before proceeding.** Your responses will shape the research-02 deep dive and ultimately the SPEC.md. Take your time -- there are no wrong answers here, just trade-offs to navigate.
