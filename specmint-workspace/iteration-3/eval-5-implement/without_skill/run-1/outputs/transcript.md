# Transcript: "implement phase 1" without skill

## Setup

- Read `.specs/registry.md` -- found one spec: `quick-auth` (Quick Auth Setup), status `active`, priority `high`, progress `0/10`.
- Read `.specs/quick-auth/SPEC.md` -- full spec for JWT-based auth on Express.js.
- Checked project root -- completely empty aside from `.specs/`. No `package.json`, no `src/`, no existing code.

## User Prompt

> "implement phase 1"

## How I Would Naturally Respond

Given the spec and the empty project, here is my natural response to the user:

---

I can see Phase 1 of the Quick Auth Setup spec has 4 tasks:

- **[QA-01]** Create `src/middleware/auth.ts` -- JWT verification middleware
- **[QA-02]** Create `src/models/user.ts` -- User interface and Prisma schema
- **[QA-03]** Create `src/auth/tokens.ts` -- `generateAccessToken()` and `generateRefreshToken()`
- **[QA-04]** Add `POST /auth/register` endpoint in `src/routes/auth.ts`

Before I start implementing, I have a few questions:

1. **No project scaffold exists.** There is no `package.json`, `tsconfig.json`, or any existing source code. Should I initialize the Express.js + TypeScript project from scratch (npm init, install dependencies, set up tsconfig), or do you have an existing project I should be working in?

2. **Database setup.** The spec references Prisma for the user model. Should I initialize Prisma as well (`npx prisma init`), pick a database (PostgreSQL, SQLite for dev?), and create the initial migration?

3. **Environment config.** JWT requires secrets (`JWT_SECRET`, `REFRESH_SECRET`, token expiry durations). Should I create a `.env` file with sensible defaults, or do you have specific values?

4. **Spec libraries and versions.** The spec pins `jsonwebtoken@9.0.2`, `argon2@0.31.2`, and `zod@3.22.4`. Should I install exactly those versions?

If you want me to just go ahead and scaffold everything with reasonable defaults (TypeScript, Express, Prisma with SQLite for local dev, `.env` with placeholder secrets), I can do that and implement all 4 tasks. Just confirm and I will proceed.

---

## Analysis: What Happened Without the Skill

### What I did well (natural behavior):
1. **Found and read the spec.** The `.specs/` directory was mentioned in the prompt, so I read both the registry and the SPEC.md to understand the full context.
2. **Identified the 4 tasks in Phase 1** and listed them clearly.
3. **Noticed blockers.** Recognized that the project has no scaffold, which is a prerequisite for implementing any of the tasks.
4. **Asked clarifying questions** rather than making assumptions about project setup.

### What I did NOT do (things the skill would provide):
1. **Did not automatically start implementing.** Without skill instructions telling me to "work through tasks, update checkboxes," I defaulted to asking questions first. The skill would push toward immediate implementation.
2. **Did not update the SPEC.md.** I did not mark QA-01 with `<- current`, update the frontmatter status, or touch the resume context. The skill has explicit instructions about updating spec state during implementation.
3. **Did not update the registry.** Progress would remain `0/10`. The skill instructs updating the registry after each task.
4. **Did not follow a task-by-task workflow.** The skill defines a loop: pick task, implement, check box, update resume context, move to next. Without it, I would likely implement all 4 tasks in one batch and report back.
5. **Did not pause/save context.** The skill has explicit pause behavior (save resume context with file paths, function names, exact next step). Without it, I would just stop when done.
6. **Did not use the `<- current` marker convention.** I recognized it in the spec but would not have maintained it systematically without skill instructions.
7. **No interview or research phase trigger.** The skill has natural language triggers for "resume", "what was I working on", etc. Without it, "implement phase 1" is just a direct request I handle ad hoc.

### Key Difference: Structured Lifecycle vs. Ad Hoc

Without the skill, my response is a one-shot: read spec, ask questions, implement (if told to proceed), report done. There is no structured lifecycle -- no checkpointing, no resume context updates, no registry syncing, no systematic task-by-task progression with state tracking. The skill turns implementation into a stateful, resumable process. Without it, it is a stateless conversation that loses all context if the session ends.

### Would I have implemented correctly?

If the user said "yes, go ahead with defaults," I would have:
- Scaffolded the project correctly (package.json, tsconfig, dependencies)
- Implemented all 4 files (auth middleware, user model, token utils, register route)
- Used the libraries specified in the spec (jsonwebtoken, argon2, zod)
- Probably delivered working code

But I would NOT have:
- Updated SPEC.md checkboxes after each task
- Updated the registry progress from `0/10` to `4/10`
- Written a resume context block with specific file paths and next steps
- Created a clean handoff point for a future session to pick up at Phase 2
