# Forge Workflow Transcript -- Without Skill (Run 1)

## User Prompt

> I need to add real-time notifications to my Next.js app. Users should get notified when someone comments on their post, when they get a new follower, and when their post gets liked. I'm using Prisma with PostgreSQL and the app is deployed on Vercel. I was thinking SSE or WebSockets but I'm not sure which is better for Vercel's serverless setup. Can you forge a spec for this?

## Claude Code Response (No Plugin/Skill Loaded)

Good question about SSE vs WebSockets on Vercel. Let me share what I know about the constraints and trade-offs, then ask you some questions so we can nail down the right approach before building anything.

### Technical Context: Vercel and Real-Time

**WebSockets on Vercel**: Vercel's serverless functions do NOT support persistent WebSocket connections. Serverless functions have execution time limits (10s on Hobby, 60s on Pro, 300s on Enterprise) and are stateless -- they spin up, handle a request, and die. WebSockets require a persistent, long-lived connection, which fundamentally conflicts with this model.

**SSE on Vercel**: Server-Sent Events work better because they're built on top of regular HTTP responses with streaming. Vercel supports streaming responses (used by Next.js AI SDK, for example). However, SSE connections are still subject to function timeout limits. On the Pro plan, you get up to 60 seconds per connection, meaning the client would need to reconnect periodically.

**The realistic options for Vercel:**

1. **Polling** -- Simple, works perfectly with serverless. Client hits an API endpoint every N seconds. Not truly "real-time" but can feel close (5-10s intervals).

2. **SSE with reconnection** -- Streaming response that pushes events as they happen, with automatic reconnection when the function times out. Better latency than polling, but adds complexity.

3. **External real-time service** -- Use a dedicated service like Pusher, Ably, or Supabase Realtime alongside Vercel. These maintain the persistent connections on infrastructure designed for it, while your Vercel functions trigger events via API calls.

4. **Vercel + separate WebSocket server** -- Deploy a small WebSocket server on Railway, Fly.io, or a similar platform alongside your Vercel app. More infrastructure to manage.

### Questions Before I Write a Spec

I need to understand your situation better before designing this. Here are my questions:

**1. Which Vercel plan are you on?**
This determines your function timeout limits (10s Hobby vs 60s Pro vs 300s Enterprise), which directly impacts whether SSE is viable or if we need an external service.

**2. What's your tolerance for latency vs complexity?**
- **Polling (simplest)**: Notifications arrive within 5-15 seconds. Dead simple to implement. No new infrastructure.
- **External service like Pusher/Ably (moderate complexity)**: Sub-second delivery. Adds a dependency and a small cost (~$25/mo for moderate usage).
- **SSE with reconnection (more complex)**: Near-real-time but requires careful handling of reconnection, missed events during gaps, and function timeouts.

Which trade-off feels right for your use case?

**3. Do you have existing Prisma models for User, Post, Comment, and Follow?**
I'd like to understand your current schema so the notification system integrates cleanly. Can you share the relevant parts of your `schema.prisma`?

**4. Do you need in-app notifications, push notifications (browser/mobile), or both?**
- In-app only: bell icon with dropdown, unread count badge
- Browser push: service worker + Web Push API for notifications even when the tab is closed
- Both

**5. What's your expected scale?**
- Roughly how many users?
- How many notifications per day are we talking about?

This affects whether a simple `Notification` table with polling is perfectly adequate or whether you need something more sophisticated.

**6. Should notifications be grouped or individual?**
For example, if 10 people like a post, should the user see "10 people liked your post" (grouped) or 10 separate "X liked your post" notifications?

---

Once you answer these, I can do a deeper dive into the specific approach and write up a proper spec with phases, tasks, and architecture. What are your thoughts?

---

## Observations on Claude Code Behavior (Without Skill)

### What Claude Code Did

1. **Recognized "forge a spec"** as the user wanting structured planning, but had no formal workflow to follow.
2. **Attempted web research** (WebSearch calls) to gather current information about Vercel's SSE/WebSocket support -- these were denied by permissions.
3. **Read specsmith's own files** (spec-format.md, forge.md) since it was in the specsmith repo -- but ultimately did not follow the forge workflow since it's not loaded as a plugin.
4. **Provided technical analysis** of the SSE vs WebSocket trade-off on Vercel, drawing from built-in knowledge.
5. **Asked interview-style questions** (6 questions) to clarify requirements before proceeding.

### What Claude Code Did NOT Do

1. **No `.specs/` directory created** -- no spec ID was generated, no directory structure was set up, no registry was initialized.
2. **No research artifacts saved** -- no `research-01.md` file was written with structured findings.
3. **No interview artifacts saved** -- no `interview-01.md` file was created to persist the Q&A.
4. **No researcher agent spawned** -- no parallel deep-dive agent was launched to exhaustively scan the codebase.
5. **No Context7 lookups** -- no library documentation was fetched for Prisma, Next.js, Pusher, or other relevant libraries.
6. **No spec document written** -- no SPEC.md was produced with frontmatter, phases, tasks, architecture diagrams, library comparison tables, testing strategy, or decision log.
7. **No structured workflow** -- the response was a single-shot analysis + questions rather than a multi-phase research-interview-research-interview-spec pipeline.
8. **No collision check** -- no check for existing specs with the same ID.
9. **No codebase scanning** -- while Claude noted there was no Next.js codebase to scan (correct), a skill-driven workflow would have explicitly documented this gap and adapted its research accordingly.

### Quality of the Response

The response was **reasonable for a generic Claude Code session**:
- The technical analysis of Vercel's limitations was accurate and useful.
- The questions were relevant and well-targeted.
- The latency-vs-complexity framing was helpful for decision-making.

However, compared to what the forge workflow would produce:
- **No persistent artifacts** -- if the session ends, everything is lost. There's nothing to resume from.
- **No structured research** -- the analysis was inline text, not a saved research document with sections for architecture, risks, library comparisons, etc.
- **No phased approach** -- the response was a monolithic block rather than a structured multi-round process.
- **Shallow depth** -- 6 questions in a single round vs. the forge workflow's iterative research-interview loops that go deeper with each round.
- **No spec output** -- the user asked to "forge a spec" and did not receive a spec document. They received questions (which is appropriate as a first step), but the forge workflow would have also produced research-01.md and started building toward a SPEC.md.
- **No architecture diagrams, no library comparison tables, no testing strategy** -- all standard components of a forged spec.
