---
name: specsmith
description: >
  Persistent spec management for AI coding workflows. Use this skill when the
  user explicitly mentions specs, forging, or structured planning: says "forge",
  "forge a spec", "write a spec for X", "create a spec", "plan X as a spec",
  "resume", "what was I working on", "spec list/status/pause/switch/activate",
  "implement the spec", "implement phase N", "implement all phases",
  "generate openapi", or exits plan mode (offer to save as a spec). Also
  trigger when a `.specs/` directory exists at session start. Do NOT trigger
  on general feature requests, coding tasks, or questions that don't mention
  specs or forging — those are normal coding tasks, not spec management.
---

# Spec Smith

Turn ephemeral plans into structured, persistent specs built through deep
research and iterative interviews. Specs have phases, tasks, resume context,
and a decision log. They live in `.specs/` at the project root and work
with any AI coding tool that can read markdown.

Whether `.specs/` is committed is repository policy. Respect `.gitignore`
and the user's preference for tracked vs local-only spec state.

## Critical Invariants

1. **Single-file policy**: Keep this workflow in one `SKILL.md` file.
2. **Canonical paths**:
   - Registry: `.specs/registry.md`
   - Per-spec files: `.specs/<id>/SPEC.md`, `.specs/<id>/research-*.md`,
     `.specs/<id>/interview-*.md`
3. **Authority rule**: `SPEC.md` frontmatter is authoritative. Registry is a
   denormalized index for quick lookup.
4. **Active-spec rule**: Target exactly one active spec at a time.
5. **Parser policy**: Use best-effort parsing with clear warnings and repair
   guidance instead of hard failure on malformed rows.

## Claude Code Plugin

If running as a Claude Code plugin, slash commands like `/specsmith:forge`,
`/specsmith:resume`, `/specsmith:pause` etc. are available. See the
plugin's `commands/` directory for the full set. The `/forge` command
replaces plan mode with deep research, iterative interviews, and spec
writing.

## Session Start

If active-spec context was injected by host tooling, use it directly
instead of reading files. Otherwise, fall back to reading files manually:

1. Read `.specs/registry.md` to check for a spec with `active` status
2. If one exists, briefly mention it:
   "You have an active spec: **User Auth System** (5/12 tasks, Phase 2).
   Say 'resume' to pick up where you left off."
3. Don't force it — the user might want to do something else first

## Deterministic Edge Cases (Best-Effort)

| Situation | Required behavior |
|-----------|-------------------|
| `.specs/registry.md` missing | If `.specs/` exists, report "No registry yet" and offer to initialize it. If `.specs/` is missing, report "No specs yet" and continue normally. |
| Malformed registry row | Skip malformed row, emit warning with row text, continue parsing remaining rows. |
| Multiple `active` rows | Warn user. Pick the row with the newest `Updated` date (or first active row if dates are unavailable) for this run. On next write, normalize to a single active spec. |
| Registry row exists but `.specs/<id>/SPEC.md` missing | Warn and continue. Keep row visible in list/status with `(SPEC.md missing)`. |
| Registry and SPEC conflict | Trust `SPEC.md`, then repair registry values on next write. |
| No active spec | List available specs and ask which to activate or resume. |

## Working on a Spec

### Resuming

When the user says "resume", "what was I working on", or similar:

1. Read `.specs/registry.md` — find the spec with `active` status. If none, list specs and ask which to resume
2. Load `.specs/<id>/SPEC.md`
3. Parse progress:
   - Count completed `[x]` vs total tasks per phase
   - Find current phase (first `[in-progress]` phase)
   - Find current task (`← current` marker, or first unchecked in current phase)
4. Read the **Resume Context** section
5. Present a compact summary:

   ```
   Resuming: User Auth System
   Progress: 5/12 tasks (Phase 2: OAuth Integration)
   Current: Implement Google OAuth callback handler
   Context: Token exchange is working. Need to handle the callback
   URL parsing and store refresh tokens in the user model.
   Next file: src/auth/oauth/google.ts
   ```

6. Begin working on the current task — don't wait for permission

### Implementing

**After completing each task, immediately edit the SPEC.md file** to record
progress. Do not wait until the end of a session or until asked — update the
spec as you go:

1. Check off the completed task: `- [ ]` -> `- [x]`
2. Move `← current` to the next unchecked task
3. When all tasks in a phase are done:
   - Phase status: `[in-progress]` -> `[completed]`
   - Next phase: `[pending]` -> `[in-progress]`
4. Update the `updated` date in YAML frontmatter
5. Update progress (`X/Y`) and `updated` date in `.specs/registry.md`

**Update transaction (required order):**
1. Update `SPEC.md` first (status/task/phase/resume context).
2. Recompute progress directly from `SPEC.md` checkboxes.
3. Update the matching registry row (status/progress/updated).
4. Re-read both files to verify consistency.
5. If registry update fails, keep `SPEC.md` as source of truth and emit a
   warning with exact repair action for `.specs/registry.md`.

Also:
- If a task is more complex than expected, split it into subtasks
- Update resume context at natural pauses
- Log non-obvious technical decisions to the Decision Log
- If implementation diverges from the spec (errors found, better approach
  discovered, assumptions proved wrong), log it in the **Deviations** section

### Pausing

When the user says "pause", switches specs, or a session is ending:

0. If there is no active spec, report that there is nothing to pause and stop.
1. Capture what was happening:
   - Which task was in progress
   - What files were being modified (paths, function names)
   - Key decisions made this session
   - Any blockers or open questions
2. Write this to the **Resume Context** section in SPEC.md
3. Update checkboxes to reflect actual progress
4. Move `← current` marker to the right task
5. Add any session decisions to the **Decision Log**
6. Update `status: paused` in frontmatter
7. Update the `updated` date

**Resume Context is the most important part of pausing.** Write it as if
briefing a colleague who will pick up tomorrow. Include specific file paths,
function names, and the exact next step. Vague context like "was working on
auth" is useless — write "implementing `verifyRefreshToken()` in
`src/auth/tokens.ts`, the JWT verification works but refresh rotation isn't
hooked up to the `/auth/refresh` endpoint yet."

### Switching Between Specs

1. Validate the target spec ID first. If missing, list available specs.
2. Confirm `.specs/<target-id>/SPEC.md` exists. If not, stop with an error.
3. If target is already active, report and stop.
4. Pause the current active spec if one exists (full pause workflow).
5. Set target status to `active` in frontmatter and in `.specs/registry.md`.
6. Resume the target spec (full resume workflow).

## Command Ownership Map

- `SKILL.md`: global invariants, lifecycle rules, state authority, and conflict
  handling, plus cross-tool OpenAPI behavior.
- `commands/*.md`: command-specific entrypoints, prompts, and output shapes.
- If there is a conflict, preserve `Critical Invariants` from this file and
  apply command-specific behavior only where it does not violate invariants.

## Spec Format

### Frontmatter

YAML frontmatter with: `id`, `title`, `status`, `created`, `updated`,
optional `priority` and `tags`.

Status values: `active`, `paused`, `completed`, `archived`

### Phase Markers

`[pending]`, `[in-progress]`, `[completed]`, `[blocked]`

### Task Markers

- `- [ ] [CODE-01]` unchecked, `- [x] [CODE-01]` done
- Task codes: `<PREFIX>-<NN>` — prefix is a short (2-4 letter) uppercase
  abbreviation of the spec (e.g., `user-auth-system` → `AUTH`). Numbers
  auto-increment across all phases starting at `01`
- `← current` after the task text marks the active task
- `[NEEDS CLARIFICATION]` after the task code on unclear tasks

### Resume Context

Blockquote section with specific file paths, function names, and exact
next step. This is what makes cross-session continuity work.

### Decision Log

Markdown table with date, decision, and rationale columns. Log non-obvious
technical choices (library selection, architecture pattern, API design).

### Deviations

Markdown table tracking where implementation diverged from the spec:
task, what the spec said, what was actually done, and why. Only log
changes that would surprise someone comparing the spec to the code.

See `references/spec-format.md` for the full SPEC.md template.

## Forging Specs

When asked to forge, plan, spec out, or "write a spec for X", follow the
full forge workflow: setup, research deeply, interview the user, iterate
until clear, then write the spec.

If the environment is in read-only plan mode, do not run forge in that mode.
Ask the user to exit plan mode (Shift+Tab) and rerun `/specsmith:forge`.

**The forge workflow never produces application code.** Its outputs are only
`.specs/` files: research notes, interview notes, and the SPEC.md. If the
user says "write a spec", that means write a SPEC.md — not implement the
feature. Implementation happens separately, after the user reviews and
approves the spec.

### Step 1: Setup

1. Generate a spec ID from the title (lowercase, hyphenated):
   `"User Auth System"` -> `user-auth-system`
2. **Collision check**: If `.specs/<id>/SPEC.md` already exists or the ID
   appears in `.specs/registry.md`, warn the user and ask:
   - **Resume** the existing spec
   - **Rename** the new spec (suggest `<id>-v2` or ask for a new title)
   - **Archive** the old spec and create a new one in its place
   Do not proceed until the user chooses.
3. Initialize directories:
   ```bash
   mkdir -p .specs/<id>
   ```
4. If `.specs/registry.md` doesn't exist, initialize it:
   ```markdown
   # Spec Registry

   | ID | Title | Status | Priority | Progress | Updated |
   |----|-------|--------|----------|----------|---------|
   ```

### Step 2: Deep Research

Research is the foundation of a good spec. Be exhaustive — use every available
resource. The goal is to gather enough context that the spec won't need revision
mid-build.

Research runs on two parallel tracks to maximize thoroughness and speed:

#### Track A: Spawn the Researcher Agent

**Always spawn the `specsmith:researcher` agent** for codebase + internet
research. Don't skip this — the researcher is purpose-built for exhaustive
multi-source analysis and runs in parallel so it doesn't slow down the
workflow.

Spawn it with the Task tool, providing:
- The user's request (what they want to build/change)
- The spec ID and output path: `.specs/<id>/research-01.md`
- Any Context7 findings you've already gathered (Track B)
- Specific areas to focus on, if known

The researcher will:
- Map the full project architecture (read manifests, lock files, directory tree)
- Read 15-30 relevant code files and trace dependency chains
- Run 3+ web searches for best practices and current patterns
- Compare 2-4 library candidates for every choice point
- Assess security risks and performance implications
- Produce a structured research document with a completeness checklist

#### Track B: Context7 & Cross-Skill Research (in parallel)

While the researcher runs, do these yourself — they use MCP tools that
the researcher agent doesn't have access to:

- **Context7**: If available (resolve-library-id / query-docs tools), pull
  up-to-date documentation for every key library involved. Check API changes,
  deprecated features, and recommended patterns for the specific versions in
  use. Do this for 2-5 key libraries — the ones central to the feature being
  built.
- **Cross-skill loading**: Load other available skills when relevant:
  - **frontend-design**: For UI-heavy specs — creative, professional design
  - **datasmith-pg**: For database specs — schema design, migrations, indexing
  - **webapp-testing**: For testing strategy — Playwright patterns
  - **vercel-react-best-practices**: For Next.js/React performance
  - Any other relevant skill that's available
- **UI research** (if applicable): Take screenshots, map component hierarchy,
  research modern UI patterns, note accessibility requirements

#### Merging Research

When the researcher agent completes, read its output at
`.specs/<id>/research-01.md`. Merge your Context7 and cross-skill findings
into the research notes — either append to the file or keep them in mind
for the interview. The combined research should cover:
architecture, relevant code, tech stack, library comparisons, internet
research, Context7 docs, UI research (if applicable), risk assessment,
and open questions.

### Step 3: Interview Round 1

Present your research findings and ask targeted questions. Your research
should inform specific questions, not generic ones.

1. **Summarize findings** (2-3 paragraphs — not a wall of text)
2. **State assumptions** — "Based on the codebase, I'm assuming we'll use X
   pattern because that's what similar features use. Correct?"
3. **Ask 3-6 targeted questions** that research couldn't answer:
   - Architecture decisions ("New module or extend existing one?")
   - Scope boundaries ("Should this handle X edge case?")
   - Technical choices ("Stick with Library A or try Library B?")
   - User-facing behavior ("What should happen when X fails?")
4. **Propose a rough approach** and ask for reactions

**STOP after presenting questions.** Wait for the user to answer before
proceeding. Do not answer your own questions, do not assume answers, and do
not continue to Step 4 or Step 5 until the user has responded. The interview
is a conversation — the user's answers shape the spec. If you skip this, the
spec will be based on guesses instead of decisions.

Save to `.specs/<id>/interview-01.md` with: questions asked, user answers,
key decisions, and any new research needed.

### Step 4: Deeper Research + Interview Loop

Based on the user's answers, do another round of research — explore the
specific paths they chose, check feasibility, find potential issues. Save
to `.specs/<id>/research-02.md`.

Then present deeper findings and ask about trade-offs, edge cases,
implementation sequence, and scope refinement. Save each interview round
to `interview-02.md`, `interview-03.md`, etc.

**Repeat research-then-interview until:**
- You have enough clarity to write a spec with no ambiguous tasks
- The user is satisfied with the direction
- Every task can be described concretely (not "figure out X")

Two rounds is typical. Don't rush it — but don't drag it out either.

### Step 5: Write the Spec

Synthesize all research notes, interview answers, and decisions into a
comprehensive SPEC.md. See `references/spec-format.md` for the full template.

The spec should be thorough and detailed — someone reading it should be able
to implement the feature without guessing. Include:

- YAML frontmatter (id, title, status, created, updated, priority, tags)
- Overview (2-4 sentences — what's being built and why)
- **Architecture Diagram** — ASCII art or Mermaid diagram showing the system
  architecture, data flow, or component relationships. Every non-trivial spec
  should have at least one diagram. Use ASCII for simple flows, Mermaid for
  complex relationships.
- **Library Choices** — Table comparing evaluated libraries with the selected
  pick and rationale. Include version numbers.
- Phases with status markers (3-6 phases is typical)
- Tasks as markdown checkboxes with task codes (`[PREFIX-NN]`) — be specific:
  include file paths, function names, and expected behavior
- **Testing Strategy** — Comprehensive testing plan: unit tests, integration
  tests, e2e tests, edge case tests. Specify which testing frameworks to use
  and what test files to create. Every feature task should have a corresponding
  test task.
- Resume Context section (blockquote)
- Decision Log with non-obvious technical choices from the interviews
- Deviations table (empty — filled during implementation)

**Diagram guidelines:**
- Use ASCII art for simple request flows and data pipelines:
  ```
  Client → API Gateway → Auth Middleware → Route Handler → Database
                                              ↓
                                         Cache Layer
  ```
- Use Mermaid for complex architecture, state machines, and ER diagrams:
  ```mermaid
  graph TD
    A[Client] --> B[API Gateway]
    B --> C{Auth?}
    C -->|Yes| D[Handler]
    C -->|No| E[401]
  ```
- Include at least one diagram per spec (architecture, data flow, or state)

**Solution quality standards:**
- Proposed solutions should be simple, maintainable, and professional
- Prefer clean, modern patterns over clever hacks
- Choose the best available libraries — compare options, pick the most mature
  and well-maintained
- UI designs should be creative, sleek, and professional — not generic
- Code architecture should be innovative where appropriate but always clean

**Coherence and logic review (mandatory before presenting):**
1. Read through the entire spec as a whole — does it tell a coherent story?
2. Check that phases are in logical dependency order — no phase requires
   work from a later phase
3. Verify every task is concrete and actionable (file paths, function names)
4. Confirm the architecture diagram matches the task descriptions
5. Check that the testing strategy covers all feature tasks
6. Verify library choices are consistent throughout (no conflicting picks)
7. Ensure the overview accurately summarizes what the phases will deliver
8. Look for gaps — is there anything the implementation would need that
   isn't covered by a task?

Save to `.specs/<id>/SPEC.md`. Update `.specs/registry.md` — set
status to `active`.

**Present the spec and wait for approval.** Show the user the complete spec
and ask: "Does this look right? Want to adjust anything before we start?"
Do not begin implementing until the user explicitly approves. The forge
workflow produces only spec files (SPEC.md, research-*.md, interview-*.md) —
never application code. Implementation starts only after the user approves
the spec and says to proceed.

**Phase/task guidelines:**
- Mark Phase 1 as `[in-progress]`, the rest as `[pending]`
- Mark the first unchecked task with `← current`

## Implementing a Spec

When the user says "implement the spec", "implement phase N", "implement all
phases", or similar:

### Scope Detection

Parse the user's request to determine scope:
- **"implement the spec"** or **"implement"** → Start from the current task
  (the `← current` marker) and work forward
- **"implement phase N"** or **"implement phase <name>"** → Implement all
  tasks in that specific phase
- **"implement all phases"** or **"implement everything"** → Implement all
  remaining unchecked tasks across all phases, in order

### Implementation Flow

1. Read `.specs/registry.md` to find the active spec
2. Load `.specs/<id>/SPEC.md` and parse phases/tasks
3. Identify the target tasks based on scope
4. For each task, in order:
   a. Mark it with `← current`
   b. Implement it — write the actual code
   c. Check it off: `- [ ]` → `- [x]`
   d. Remove the `← current` marker
   e. When all tasks in a phase complete:
      - Phase status: `[in-progress]` → `[completed]`
      - Next phase: `[pending]` → `[in-progress]`
   f. Update `updated` date in frontmatter
   g. Update progress and date in `.specs/registry.md`
5. After each task completion, update Resume Context with current state
6. Log any new decisions to the Decision Log
7. If implementation diverges from the spec, log it in the Deviations section
8. If blocked on a task:
   - Keep the task unchecked and record blocker details in Resume Context
   - Set phase marker `[blocked]` only when the whole phase is blocked
   - Continue with another unblocked task only if sequencing allows it

### Testing During Implementation

When implementing, follow the testing strategy from the spec:
- Write tests as specified in the testing tasks
- Run tests after each task to verify correctness
- If a test task exists for the feature task you just completed, implement
  the test task immediately after

### Completion

When all tasks are done:
- Set all phases to `[completed]`
- Set spec status to `completed` in frontmatter and registry
- Update the `updated` date
- Present a summary of what was implemented
- Suggest next spec to activate if any are paused

## Generating OpenAPI Docs

When the user says "generate openapi", "update api docs", or similar:

1. Scan the codebase for API routes/handlers/controllers and request/response
   schemas.
2. Infer auth/security schemes and endpoint grouping (tags).
3. Write `.openapi/openapi.yaml` (OpenAPI 3.1.1) with:
   - `operationId` for every operation
   - Reusable `components/schemas` and `$ref` usage
   - Accurate parameters, request bodies, responses, and security
4. Write one endpoint doc per route under `.openapi/endpoints/` using
   `{method}-{path-slug}.md` names (e.g., `get-api-users-id.md`).
5. Preserve manual additions in existing `.openapi/` files when updating.
6. Report totals: endpoints, schemas, security schemes, and manual-review
   candidates.

## Before Session Ends

If the session is ending:

1. Pause the active spec (run full pause workflow)
2. Write detailed resume context
3. Confirm to the user that context was saved

## Directory Layout

All state lives in `.specs/` at the project root:

```
.specs/
├── registry.md               # Denormalized index for status/progress lookups
└── <spec-id>/
    ├── SPEC.md               # The spec document
    ├── research-01.md        # Deep research findings
    ├── interview-01.md       # Interview notes
    └── ...
```

## Registry Format

`.specs/registry.md` is a simple markdown table:

```markdown
# Spec Registry

| ID | Title | Status | Priority | Progress | Updated |
|----|-------|--------|----------|----------|---------|
| user-auth-system | User Auth System | active | high | 5/12 | 2026-02-10 |
| api-refactor | API Refactoring | paused | medium | 2/8 | 2026-02-09 |
```

**SPEC.md frontmatter is authoritative.** The registry is a denormalized
index for quick lookups. Always update both together — when you change
status, progress, or dates in SPEC.md, immediately mirror those changes
in the registry. If they ever conflict, SPEC.md wins.

## Listing Specs

Read `.specs/registry.md` and present specs grouped by status:

```
Active:
  -> user-auth-system: User Auth System (5/12 tasks, Phase 2)

Paused:
  || api-refactor: API Refactoring (2/8 tasks, Phase 1)

Completed:
  ok ci-pipeline: CI Pipeline Setup (8/8 tasks)
```

## Canonical Output Templates

Use these concise formats consistently:

**Resume**
```
Resuming: <Title> (<id>)
Progress: <done>/<total> tasks
Phase: <phase name>
Current: <task text>
Context: <one to three lines from Resume Context>
```

**List**
```
Active:
  -> <id>: <Title> (<done>/<total>, <phase>) [<priority>]
Paused:
  || <id>: <Title> (<done>/<total>, <phase>) [<priority>]
Completed:
  ok <id>: <Title> (<done>/<total>) [<priority>]
```

**Status**
```
<Title> [<status>, <priority>]
Created: <date> | Updated: <date>
Phase <n>: <name> [<marker>]
Progress: <done>/<total> (<pct>%)
Current: <task text or none>
```

## Completing a Spec

1. Verify all tasks are checked (warn if not, but allow override)
2. Set status to `completed` in frontmatter and registry
3. Update the `updated` date in both
4. Suggest next spec to activate if any are paused

## Archiving a Spec

Archive completed specs to keep the registry clean:

1. Set status to `archived` in frontmatter and registry
2. Research files (research-*.md, interview-*.md) in `.specs/<id>/` can optionally be deleted
   (the SPEC.md has all the decisions and context)

Specs can be archived from `completed` or `paused` status. To reactivate
an archived spec, set its status back to `active`.

## Deleting a Spec

To remove a spec entirely:

1. Delete `.specs/<id>/` (contains SPEC.md, research notes, interviews)
2. Remove the row from `.specs/registry.md`

This is irreversible — consider archiving instead if you might need it later.

## Cross-Tool Compatibility

The spec format is pure markdown with YAML frontmatter. Any tool that can
read and write files can use these specs:

- **Claude Code**: Full plugin support or skill via `npx skills add`
- **Codex**: Snippet in AGENTS.md or skill via `npx skills add`
- **Cursor / Windsurf / Cline**: Snippet in rules file
- **Gemini CLI**: Snippet in GEMINI.md
- **Humans**: Readable and editable in any text editor
- **Git**: Diffs cleanly, easy to track in version control

To configure another tool, run `npx skills add ngvoicu/specsmith -a <tool>`.

## Behavioral Notes

**Be proactive about spec management.** If you notice the user has been
working for a while and made progress, update the spec without being asked.
If a session is ending, offer to pause and save context.

**Specs should evolve.** It's fine to add tasks, reorder phases, or split a
phase into two as understanding deepens. Specs aren't contracts — they're
living documents that adapt as you learn more about the problem.

**The Decision Log matters.** When the user makes a non-obvious technical
choice (library selection, architecture pattern, API design), log it with
the rationale. Future-you resuming this spec will thank present-you.

**Don't over-structure.** A spec with 3 phases and 15 tasks is useful. A
spec with 12 phases and 80 tasks is a project plan, not a coding spec.
Keep it lean enough to parse and act on in one read.

**Respect the user's flow.** Don't interrupt deep coding work to update
the spec. Batch updates for natural pauses — task completion, phase
transitions, or session boundaries.
