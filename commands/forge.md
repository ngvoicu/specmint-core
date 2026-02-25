---
description: Research deeply, interview the user, then forge a structured spec with phases and tasks. This is your enhanced plan mode.
disable-model-invocation: true
---

# Forge a Spec

You are about to run the Spec Smith forge workflow. This replaces plan mode
with something far more thorough: deep research → interview → more research
→ more interview → write spec → implement.

The user's request: $ARGUMENTS

## Plan Mode Check

Before starting, check if you're in plan mode (read-only). If so:
- Skip the Setup phase (directory creation) — we'll do it later
- Proceed directly to Phase 1 (research) and Phase 2+ (interviews)
- When reaching Phase 5 (write spec), ask the user to exit plan mode
  first, then do Setup + write spec

If NOT in plan mode, proceed normally with Setup first.

## Phase 1: Deep Research

This is the most important phase. Be exhaustive. You are gathering every
piece of context needed to write a spec that won't need revision mid-build.

### 1a. Codebase Research

Scan the project thoroughly. Don't just grep for keywords — understand the
architecture:

- **Project structure**: Map the directory tree, identify patterns (monorepo?
  modules? packages?)
- **Tech stack**: Read package.json/Cargo.toml/go.mod/requirements.txt etc.
  Understand what's already in use
- **Related code**: Find every file, function, component, route, model, and
  test that touches the area the user wants to change
- **Patterns**: How does the existing code handle similar things? If adding
  auth, how is the existing middleware structured? If adding a feature, what
  patterns do similar features follow?
- **Tests**: What testing frameworks are used? What's the test coverage like
  in the relevant area?
- **Config**: Environment variables, build config, CI/CD pipelines that
  might be affected
- **Dependencies**: What libraries are relevant? Are there version
  constraints?

Use Glob, Grep, and Read aggressively. Read actual file contents, not just
file names. Open 10-20 files if needed. If Context7 is available
(resolve-library-id / get-library-docs tools), use it to pull documentation
for key libraries.

For large or unfamiliar codebases, spawn the `specsmith:researcher` agent
(Task tool) to run an exhaustive parallel research pass. It will save
structured findings to `.specs/<id>/research-01.md`.

### 1b. Web Research

If the task involves technologies, patterns, or approaches that benefit from
current documentation:

- Search for best practices, recent API changes, known pitfalls
- Look up library documentation for the specific version in use
- Find examples of similar implementations
- Check for security advisories if relevant

Use WebSearch and WebFetch. Don't be shy about multiple searches.

### 1c. UI Research (if applicable)

If the project has a UI and the changes affect it:

- Take screenshots of current state if browser tools are available
- Map the component hierarchy
- Understand the routing and state management

### 1d. Save Research

Write everything you found to:
```
.specs/<spec-id>/research-01.md
```

Structure it clearly:

```markdown
# Research Notes — <Title>
## Date: <today>

## Project Architecture
<what you found about the structure>

## Relevant Code
<key files, functions, patterns found>

## Tech Stack & Dependencies
<what's in use, versions>

## External Research
<web findings, library docs, best practices>

## UI State (if applicable)
<screenshots, component map>

## Open Questions
<things you couldn't determine from research alone>
```

## Phase 2: Interview Round 1

Now present your findings and ask targeted questions. The goal is NOT to ask
generic questions — your research should inform very specific questions.

**Structure the interview like this:**

1. **Summarize what you found** (2-3 paragraphs, not a wall of text)
2. **State your assumptions** — "Based on the codebase, I'm assuming we'll
   use X pattern because that's what similar features use. Correct?"
3. **Ask specific questions** that your research couldn't answer:
   - Architecture decisions: "Should this be a new module or extend the
     existing one in src/features/?"
   - Scope boundaries: "Should this handle X edge case or is that a
     separate spec?"
   - Technical choices: "I see you're using Library A for similar things.
     Should we stick with that or is there a reason to try Library B?"
   - User-facing behavior: "What should happen when X fails?"
4. **Propose a rough approach** and ask for reactions — don't wait for the
   user to design everything

Keep it to 3-6 questions max per round. More than that overwhelms.

**Save the interview:**
```
.specs/<spec-id>/interview-01.md
```

```markdown
# Interview Round 1 — <Title>
## Date: <today>

## Questions Asked
1. <question>
   **Answer**: <user's response>

2. <question>
   **Answer**: <user's response>

## Key Decisions
- <decision made during this interview>

## New Research Needed
- <things to look into based on answers>
```

## Phase 3: Deeper Research (informed by interview)

Based on the user's answers, do another round of research:

- Explore the specific code paths they mentioned
- Look up the libraries or patterns they chose
- Check feasibility of the approach discussed
- Find potential issues with the chosen direction

Save to:
```
.specs/<spec-id>/research-02.md
```

## Phase 4: Interview Round 2+

Present your deeper findings. Ask about:

- Trade-offs you discovered
- Edge cases that emerged from the deeper research
- Implementation sequence — "I'd suggest building X first because Y depends
  on it. Does that sequence make sense?"
- Scope refinement — "This feels like it could be split into two specs.
  Want to keep it together or separate?"

Save each round to `interview-02.md`, `interview-03.md`, etc.

**Repeat phases 3-4 as many times as needed.** The loop ends when:

- You have enough clarity to write a spec with no ambiguous tasks
- The user says they're satisfied with the direction
- Every task in the spec can be described concretely (not "figure out X")

It's fine if this takes 2 rounds or 5 rounds. Don't rush it.

## Setup (before writing)

Before writing the spec, ensure the directory structure exists:

1. Generate a spec ID from the user's request (lowercase, hyphenated)
2. **Collision check**: Before creating anything, check if
   `.specs/<spec-id>/SPEC.md` already exists or the ID appears in
   `.specs/registry.md`. If either is true, warn the user and ask:
   - **Resume** the existing spec (switch to resume workflow)
   - **Rename** the new spec (suggest `<spec-id>-v2` or ask for a new title)
   - **Archive** the old spec and create a new one in its place
   Do not proceed until the user chooses.
3. Create the spec directory:
   ```
   mkdir -p .specs/<spec-id>
   ```
4. If `.specs/` doesn't exist yet, also create `registry.md`

If you were in plan mode during earlier phases, confirm the user has exited
plan mode before proceeding. If directory creation fails (still read-only),
ask the user to exit plan mode (Shift+Tab) and wait for confirmation.

## Phase 5: Write the Spec

Now synthesize everything — all research notes, all interview answers, all
decisions — into a SPEC.md.

Read the skill's `references/spec-format.md` for the full template. The
spec should include:

1. **YAML frontmatter**: id, title, status (active), created, updated,
   priority, tags
2. **Overview**: 2-4 sentences capturing the goal and scope. Someone reading
   just this section should understand what's being built and why.
3. **Phases**: Major milestones (3-6 typical). Each phase should represent a
   coherent chunk of work that's independently testable or demoable.
4. **Tasks**: Concrete, actionable checkboxes within each phase. Each task
   should be completable in one focused session. Include specific file paths
   and function names where known.
5. **Resume Context**: Write the initial context as if briefing someone who
   will start implementing tomorrow.
6. **Decision Log**: Every decision from the interviews, with rationale.

**Quality check before presenting:**

- Every task should be concrete ("Add verifyToken() to src/auth/tokens.ts"),
  not vague ("implement token verification")
- Phases should have clear boundaries and dependencies
- The Decision Log should capture every non-obvious choice
- The Overview should be understandable without reading the interviews

Save to:
```
.specs/<spec-id>/SPEC.md
```

Update `.specs/registry.md` (set status to `active`).

**Present the spec to the user for review.** Walk through the phases and
ask if the structure, sequencing, and task granularity look right. Adjust
based on feedback.

## Phase 6: Implement

Once the user approves the spec:

1. Mark Phase 1 as `[in-progress]`
2. Mark the first task with `← current`
3. Begin implementing

**After completing each task, immediately edit the SPEC.md file** — don't
defer updates to the end of the session:
- Check off the task: `- [ ]` -> `- [x]`
- Move `← current` to the next unchecked task
- When all tasks in a phase are done: `[in-progress]` -> `[completed]`, next phase `[pending]` -> `[in-progress]`
- Update the `updated` date in frontmatter
- Update progress (`X/Y`) and `updated` date in `.specs/registry.md`
- Update Resume Context periodically
- Log any new decisions in the Decision Log
- If implementation diverges from the spec, log it in the **Deviations** section
- If a task reveals unexpected complexity, split it and update the spec

If the session is ending before the spec is complete, run the pause workflow
(save detailed resume context with file paths, function names, exact next
step).
