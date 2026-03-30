# Forge Transcript -- Commenting System

## Session Info
- Date: 2026-03-06
- Spec ID: `commenting-system`
- Skill: specsmith (SKILL.md loaded)
- Forge Phase: Step 5 -- Write the Spec

---

## Context

Research (research-01.md) and interview (interview-01.md) rounds are complete. The user confirmed:

- Next.js 14 App Router, PostgreSQL with Prisma, NextAuth.js v5
- Tiptap for rich text editing (chosen over Slate and Lexical for Yjs collab support)
- Pusher for real-time updates (serverless-compatible, existing account)
- Nested replies up to 3 levels deep, then flatten
- Per-user per-comment mark-as-read tracking
- @mentions deferred to v2 (but design data model for it)
- Basic moderation: report button, soft-delete by author/admin

---

## Step 5: Write the Spec

### Process

1. Read `references/spec-format.md` for the full SPEC.md template
2. Synthesized all research notes and interview answers
3. Generated spec ID: `commenting-system`
4. Task code prefix: `CMT` (from "commenting")
5. Wrote comprehensive SPEC.md with:
   - YAML frontmatter (id, title, status: active, created, updated, priority: high, tags)
   - Overview section (4 sentences covering scope, key technologies, and boundaries)
   - Requirements section (6 concrete acceptance criteria)
   - Architecture section with 3 diagrams:
     - ASCII art system diagram showing component relationships and data flow
     - Mermaid flowchart showing the comment creation data flow including auth, depth validation, Pusher trigger, and read tracking
     - Mermaid ER diagram showing Comment, CommentRead, CommentReport entities with all fields
   - Library Choices table comparing 6 technology needs with alternatives and rationale
   - 6 phases with 32 total tasks, all using `[CMT-NN]` codes auto-incrementing from 01 to 32
   - Testing Strategy section with unit, integration, e2e, and edge case coverage
   - Resume Context with specific file paths and next steps
   - Decision Log with 8 entries from the interview
   - Empty Deviations table

### Phase Breakdown

| Phase | Name | Tasks | Status |
|-------|------|-------|--------|
| 1 | Database Schema & Models | CMT-01 through CMT-05 | [in-progress] |
| 2 | API Layer (Server Actions & Routes) | CMT-06 through CMT-11 | [pending] |
| 3 | Comment UI Components | CMT-12 through CMT-16 | [pending] |
| 4 | Real-Time & Read Tracking | CMT-17 through CMT-21 | [pending] |
| 5 | Moderation & Polish | CMT-22 through CMT-26 | [pending] |
| 6 | Testing | CMT-27 through CMT-32 | [pending] |

---

## Coherence and Logic Review (Mandatory)

Per the skill's Step 5 instructions, performing the 8-point coherence check before presenting the spec.

### 1. Does the spec tell a coherent story?

YES. The overview establishes the goal (threaded commenting with real-time updates and read tracking), the requirements define acceptance criteria, the architecture diagrams show how the pieces fit together, and the phases build the system bottom-up from database to UI to real-time to polish to testing. A developer reading this from top to bottom would understand what to build and why.

### 2. Are phases in logical dependency order?

YES. Verified dependency chain:
- Phase 1 (Database) -- no dependencies, must come first because all other phases depend on Prisma models
- Phase 2 (API Layer) -- depends on Phase 1 models; creates server actions and API routes that Phase 3 UI will call
- Phase 3 (UI Components) -- depends on Phase 2 API layer for data fetching and submission
- Phase 4 (Real-Time & Read Tracking) -- depends on Phase 2 (Pusher trigger in API) and Phase 3 (components to wire hooks into)
- Phase 5 (Moderation & Polish) -- depends on Phases 2-4 being functional; adds report flow, admin page, accessibility, and polish
- Phase 6 (Testing) -- depends on all prior phases being implemented; tests the complete system

No phase requires work from a later phase. Confirmed.

### 3. Is every task concrete and actionable?

YES. Verified each task includes:
- **Specific file paths**: Every task names the exact file to create or modify (e.g., `prisma/schema.prisma`, `src/lib/actions/comments.ts`, `src/components/comments/CommentEditor.tsx`)
- **Function/component names**: Tasks reference specific functions (`createComment()`, `generateHTML()`, `getServerSession()`), components (`CommentEditor`, `CommentItem`, `CommentThread`, `CommentSection`), and hooks (`usePusher`, `useCommentRealtime`, `useReadTracker`)
- **Expected behavior**: Each task describes what the code should do, not just "implement X"
- **Technical details**: Schema fields with types, API response codes, Prisma operations, Tiptap extensions, IntersectionObserver usage

No task says "figure out X" or "research Y" -- all are implementation-ready.

### 4. Does the architecture diagram match the task descriptions?

YES. Cross-checked:
- ASCII diagram shows: `CommentEditor` -> `POST /api/comments` -> `createComment()` -> Prisma -> PostgreSQL -> Pusher. Tasks CMT-06 (createComment server action), CMT-12 (CommentEditor component), CMT-11 (Pusher server instance) match this flow exactly.
- ASCII diagram shows: `CommentThread` <- Pusher Client SDK. Tasks CMT-17/CMT-18 (usePusher/useCommentRealtime hooks) and CMT-19 (wire into CommentSection) match.
- ASCII diagram shows: `useReadTracker` -> IntersectionObserver -> `PATCH /api/comments/[id]/read`. Tasks CMT-20 (useReadTracker hook) and CMT-09 (read API route) match.
- Mermaid flow diagram shows auth check, depth validation, re-parenting, Pusher trigger. Tasks CMT-06 (auth + depth in createComment) and CMT-25 (depth-clamping polish) match.
- ER diagram shows Comment, CommentRead, CommentReport entities. Tasks CMT-01, CMT-02, CMT-03 create these exact models with matching fields.

All diagram elements have corresponding tasks. No orphaned diagram components.

### 5. Does the testing strategy cover all feature tasks?

YES. Coverage mapping:

| Feature | Test Coverage |
|---------|-------------|
| Depth clamping (CMT-01, CMT-06, CMT-25) | CMT-27 (unit), CMT-29 (integration), CMT-31 (e2e) |
| Comment CRUD API (CMT-06, CMT-07, CMT-08) | CMT-29 (integration), CMT-31 (e2e) |
| Tiptap rendering (CMT-12, CMT-13) | CMT-28 (unit -- serialization and XSS) |
| Read tracking (CMT-09, CMT-20, CMT-21) | CMT-29 (integration -- upsert), edge cases (debounce) |
| Pusher real-time (CMT-11, CMT-17, CMT-18, CMT-19) | CMT-30 (integration -- mocked Pusher), CMT-32 (e2e -- two browsers) |
| Soft-delete (CMT-08) | CMT-29 (integration -- auth check), CMT-31 (e2e -- deleted placeholder) |
| Report flow (CMT-10, CMT-22) | CMT-29 (integration -- create report) |
| Auth boundary | Edge case tests (unauthenticated user rejection) |
| Concurrent writes | Edge case tests (two simultaneous replies) |
| Pusher failure | Edge case tests (graceful degradation) |

All 5 major feature areas (CRUD, threading, real-time, read tracking, moderation) have unit, integration, or e2e coverage. Edge cases section covers boundary conditions.

### 6. Are library choices consistent throughout?

YES. Verified no conflicts:
- Tiptap is used consistently: CMT-12 (create editor), CMT-13 (render via generateHTML), CMT-28 (test serialization). No references to Slate or Lexical in implementation tasks.
- Pusher is used consistently: CMT-11 (server SDK), CMT-17 (client SDK via pusher-js), CMT-06/CMT-08 (trigger events). No references to Socket.io or Ably in implementation tasks.
- Prisma is used consistently throughout for all database operations. No raw SQL or alternative ORM references.
- NextAuth.js v5 is used for auth in CMT-06, CMT-08, CMT-10. No alternative auth references.
- Tailwind is referenced in CMT-13 for indentation styling. No conflicting CSS approaches.

### 7. Does the overview accurately summarize what the phases deliver?

YES. The overview mentions:
- "threaded commenting system" -- Phase 1 (schema with self-relation), Phase 3 (CommentThread recursive component)
- "rich-text comments using Tiptap" -- Phase 3 (CommentEditor with Tiptap)
- "reply up to 3 levels deep (then flatten)" -- Phase 1 (depth field), Phase 2 (depth clamping in createComment), Phase 5 (polish depth-clamping logic)
- "real-time updates via Pusher" -- Phase 4 (Pusher hooks and wiring)
- "track read/unread state per user" -- Phase 4 (useReadTracker, read API)
- "Basic moderation (report, soft-delete)" -- Phase 5 (report flow, admin page)
- "data model to accommodate @mentions in v2" -- Phase 1 (mentionedUserIds field)

Every claim in the overview is delivered by a specific phase and task.

### 8. Are there any gaps?

CHECKED. Potential gaps and their resolution:

1. **Environment variables**: Resume Context explicitly lists all 6 Pusher env vars needed. No gap.
2. **Error handling in API routes**: CMT-06 includes auth validation, CMT-07 returns data, CMT-08 validates auth + ownership. CMT-24 adds error state with retry button in the UI. Covered.
3. **Loading states**: CMT-24 explicitly adds loading skeletons and empty state. Covered.
4. **Accessibility**: CMT-26 adds aria-labels, keyboard navigation, and role attributes. Covered.
5. **Optimistic updates**: CMT-15 mentions "manage optimistic state for new comments" and CMT-18 mentions "deduplicate against optimistic updates using comment id". Covered.
6. **Comment editing**: Not in scope (not mentioned in requirements or interview). Not a gap -- intentional scope boundary.
7. **Pagination for large threads**: Not explicitly tasked. For v1 with typical thread sizes this is acceptable, but could be a gap for posts with hundreds of comments. LOW RISK -- can be added as a follow-up task if needed.
8. **Rate limiting on comment creation**: Not explicitly tasked. The API routes use auth but don't have rate limiting. LOW RISK for v1 -- Vercel's built-in function invocation limits provide basic protection.

No critical gaps found. Two low-risk items (pagination, rate limiting) are acceptable for v1 and noted.

---

## Review Verdict

PASS. The spec is coherent, phases are correctly ordered, all tasks are concrete with file paths and function names, diagrams match implementation tasks, testing covers all features, library choices are consistent, the overview is accurate, and no critical gaps exist.

---

## Output Files

- `SPEC.md` -- Written to `.specs/commenting-system/SPEC.md`
- `registry.md` -- Updated with: `| commenting-system | Commenting System | active | high | 0/32 | 2026-03-06 |`

## Next Step

Present the spec to the user and wait for approval before beginning implementation.
