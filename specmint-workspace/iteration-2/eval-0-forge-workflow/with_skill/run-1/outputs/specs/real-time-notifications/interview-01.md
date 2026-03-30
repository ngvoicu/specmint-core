# Interview Round 1 — Real-Time Notifications

## Date: 2026-03-06

## Questions Asked

1. **What is your PostgreSQL hosting provider?** (Supabase, Neon, AWS RDS, other?)
   If you're on Supabase, its built-in Realtime feature would be the simplest path — subscribe to INSERT events on a notifications table with zero additional infrastructure. If you're on Neon or another provider, we'd need a different transport.
   **Answer**: [awaiting response]

2. **How critical is truly instant delivery?** For a social app like Twitter/Instagram, notifications arrive within 1-2 seconds. Is that level of immediacy required, or would a 10-30 second polling delay be acceptable for your use case? This significantly changes the architecture complexity.
   **Answer**: [awaiting response]

3. **What's your expected concurrent user count?** (rough order of magnitude: tens, hundreds, thousands, tens of thousands?) This determines whether a third-party service like Pusher makes sense cost-wise, or if SSE with reconnection is sufficient.
   **Answer**: [awaiting response]

4. **Should notifications be grouped?** For example, if 5 people like a post in quick succession, should the user see "Alice, Bob, and 3 others liked your post" or 5 separate notifications?
   **Answer**: [awaiting response]

5. **In-app only, or also browser push notifications and/or email digests?** If browser push (Web Push API) is needed, that's a separate subsystem. Email digests add another layer. Want to scope this spec to in-app only and add the others later?
   **Answer**: [awaiting response]

6. **Is there an existing notification model in your Prisma schema, or is this greenfield?** Also, do you already have any real-time infrastructure (WebSocket server, Pusher account, etc.)?
   **Answer**: [awaiting response]

## Key Decisions
- [pending user responses]

## New Research Needed
- If Supabase: research Supabase Realtime subscription patterns with Next.js App Router
- If third-party chosen: research Pusher/Ably integration with Next.js server actions
- If SSE chosen: research Vercel streaming response patterns and reconnection strategies
- Notification grouping algorithms if user wants grouped notifications
