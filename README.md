# Spec Mint Core

[![Benchmark +39%](https://img.shields.io/badge/benchmark-%2B39%25-brightgreen)](https://github.com/ngvoicu/specmint-core#evaluation-results)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-7c5cff)](https://github.com/ngvoicu/specmint-core)

**Plan mode, but actually good.**

Spec Mint Core replaces ephemeral AI coding plans with persistent, resumable specs built through deep research and iterative interviews. Create a spec, work through it task by task, pause, switch to another spec, come back a week later and pick up exactly where you left off.

Works with Claude Code, Codex, Cursor, Windsurf, Cline, Gemini CLI, and any AI coding tool that can read files — installed as a universal skill.

## The Problem

Every AI coding tool has some version of "plan mode" — think before you code. But these plans are ephemeral. They live in the conversation context. Close the terminal, start a new session, and the plan is gone. There's no way to:

- **Resume** a plan you were halfway through implementing
- **Switch** between multiple plans when juggling features
- **Track** which tasks are done and which are next
- **Persist** the research and decisions that informed the plan

Spec Mint Core fixes all of this.

## How It Works

### The Forge Workflow

Tell your AI tool to "forge a spec for user authentication with OAuth" and Spec Mint Core takes over:

**1. Deep Research** — Exhaustive codebase scan (reads 10-20+ actual files, not just file names), web search for best practices, Context7 library docs, library comparisons, cross-skill research (frontend-design, datasmith-pg, etc.), UI inspection if applicable. Everything saved to `.specs/<id>/research-01.md`.

**2. Interview** — Presents findings, states assumptions, asks targeted questions informed by the research. Not generic questions — specific ones like "I see you're using Express middleware pattern X in `src/middleware/`. Should the auth middleware follow the same pattern?" Saves answers to `interview-01.md`.

**3. Deeper Research** — Investigates the specific directions from the interview. Checks feasibility, finds edge cases.

**4. More Interviews** — As many rounds as needed until every task in the spec can be described concretely. No ambiguous "figure out X" tasks.

**5. Write Spec** — Synthesizes all research and interviews into a comprehensive SPEC.md with architecture diagrams (ASCII/Mermaid), library comparison tables, phases, tasks, testing strategy, a decision log, and resume context. Runs a coherence and logic review before presenting.

**6. Implement** — Works through the spec task by task during implementation, checking them off, updating progress, logging new decisions, writing tests as specified in the testing strategy.

### Specs Are Files

Specs live in `.specs/` at your project root — plain markdown with YAML frontmatter. They diff cleanly in git, are readable in any editor, and work with any AI tool.

```
.specs/
├── registry.md                     # Denormalized index for status/progress lookups
└── user-auth-system/
    ├── SPEC.md                     # The spec document
    ├── research-01.md              # Initial codebase + web research
    ├── interview-01.md             # First interview round
    ├── research-02.md              # Follow-up research
    └── interview-02.md             # Second interview round
```

**SPEC.md frontmatter is authoritative.** `.specs/registry.md` is a
denormalized index for quick lookups.

For this `specmint-core` repository, `.specs/` is intentionally gitignored for
local dogfooding. In consumer projects, you can choose to commit `.specs/`.

### A SPEC.md Looks Like This

```markdown
---
id: user-auth-system
title: User Auth System
status: active
created: 2026-02-10
updated: 2026-02-11
priority: high
tags: [auth, security, backend]
---

# User Auth System

## Overview
Add JWT-based authentication with OAuth (Google, GitHub) to the Express
API. Uses the existing middleware pattern in src/middleware/.

## Phase 1: Foundation [completed]
- [x] [AUTH-01] Set up auth middleware in src/middleware/auth.ts
- [x] [AUTH-02] Create User model with Prisma schema
- [x] [AUTH-03] Implement JWT generation and verification in src/auth/tokens.ts
- [x] [AUTH-04] Add refresh token rotation

## Phase 2: OAuth Integration [in-progress]
- [x] [AUTH-05] Google OAuth provider
- [ ] [AUTH-06] GitHub OAuth provider ← current
- [ ] [AUTH-07] Token exchange flow for both providers

## Phase 3: Testing & Hardening [pending]
- [ ] [AUTH-08] Unit tests for auth middleware
- [ ] [AUTH-09] Integration tests for OAuth flow
- [ ] [AUTH-10] Rate limiting on auth endpoints

---

## Resume Context
> Finished Google OAuth. GitHub OAuth callback handler is in progress at
> `src/auth/oauth/github.ts`. The authorization URL redirect works but
> the callback endpoint at `/auth/github/callback` needs to exchange the
> code for tokens. Use the same pattern as Google in `src/auth/oauth/google.ts`
> lines 45-82. The GitHub OAuth app credentials are in `.env` as
> GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.

## Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-10 | JWT over sessions | Stateless, scales for microservices |
| 2026-02-10 | Refresh token rotation | Limits damage from stolen tokens |
| 2026-02-11 | Prisma over raw SQL | Already used in the project for other models |

## Deviations
| Task | Spec Said | Actually Did | Why |
|------|-----------|-------------|-----|
| AUTH-05 | Use passport.js | Direct googleapis calls | Simpler for a single provider, avoids passport session overhead |
```

## Installation

Spec Mint Core installs as a **universal skill** — one command, and it works in Claude Code, Codex, Cursor, Windsurf, Cline, Gemini CLI, and any AI coding tool that reads files.

```bash
# Install globally (recommended)
npx skills add ngvoicu/specmint-core -g

# Or target a specific tool with -a
npx skills add ngvoicu/specmint-core -g -a claude-code
npx skills add ngvoicu/specmint-core -g -a codex
npx skills add ngvoicu/specmint-core -g -a cursor
npx skills add ngvoicu/specmint-core -g -a windsurf
npx skills add ngvoicu/specmint-core -g -a cline
npx skills add ngvoicu/specmint-core -g -a gemini
```

Once installed, the skill auto-triggers on natural language — "forge a spec for X", "what was I working on?", "implement the spec". No slash commands and no marketplace: the skill bundles the full spec workflow, the deep-research subagent brief (`references/researcher.md`), and the spec format reference.

> **Windsurf**: replace the symlink at `.windsurf/skills/specmint-core/SKILL.md` with a real file copy — Cascade doesn't follow symlinks.

## Usage

Talk to your AI tool in plain language — the skill recognizes the spec lifecycle and runs the right workflow:

| Goal | Say something like |
|------|--------------------|
| Start a new spec | "forge a spec for user authentication" |
| Implement it | "implement the spec" · "implement phase 2" · "implement all phases" |
| Resume where you left off | "what was I working on?" · "resume" |
| Pause and save context | "pause the spec" |
| Switch active spec | "switch to the api-refactor spec" |
| List all specs | "list my specs" |
| Show progress | "spec status" |
| Generate API docs | "generate openapi" |

Every action reads and writes plain files under `.specs/` — research notes, interviews, `SPEC.md`, and a `registry.md` index. Any tool that can read files shares the same `.specs/` directory, so you can forge in one tool and implement in another.

## The Forge Workflow (Detailed)

### Phase 1: Deep Research

Not a quick scan. The researcher reads 10-20+ files, following dependency chains, checking tests, examining config. Uses every available resource: web searches for best practices, Context7 for library docs, library comparisons, cross-skill research (frontend-design, datasmith-pg, etc.).

Output saved to `.specs/<id>/research-01.md`. Covers:
- Project architecture and directory structure
- Every file touching the area of change
- Tech stack versions (from lock files, not guesses)
- How similar features are currently implemented
- Library comparisons (2-3+ candidates per choice point)
- Test patterns and coverage
- Risk assessment
- UI/UX research and design references (if applicable)

### Phase 2-4: Interviews

Targeted questions based on what research found. Not generic "what do you want?" — specific questions like:

- "I see rate limiting middleware at `src/middleware/rateLimit.ts`. Should auth endpoints use the same limiter or a stricter one?"
- "The User model uses Prisma. Should OAuth tokens go in the same schema or a separate `AuthToken` model?"

Multiple rounds (typically 2-5) until every task can be described concretely. Each round saved to `interview-01.md`, `interview-02.md`, etc.

### Phase 5: Write Spec

Synthesizes everything into a comprehensive SPEC.md:
- Architecture diagrams (ASCII and/or Mermaid)
- Library comparison table with alternatives and rationale
- 3-6 phases, each with concrete tasks (file paths, function names)
- Comprehensive testing strategy (unit, integration, e2e, edge cases)
- Decision log captures non-obvious technical choices
- Resume context section ready for first pause
- Mandatory coherence and logic review before presenting

### Phase 6: Implement

Works through the spec task by task during implementation:
- Marks tasks `← current` as they start
- Checks off `- [x]` when done
- Updates phase status markers and registry
- Writes tests as specified in the testing strategy
- Logs new decisions to the Decision Log
- Logs deviations when implementation diverges from spec
- Updates Resume Context at natural pauses

## Plan Mode

Spec Mint Core **replaces** Claude Code's built-in plan mode. The forge workflow IS your planning phase — deep research, interviews, spec writing. You don't need plan mode at all.

If you happen to be in plan mode when you ask to forge a spec, Spec Mint Core
asks you to exit plan mode first (Shift+Tab), then start the forge workflow again.

## Project Structure

```
specmint-core/
├── SKILL.md                        # Universal skill (works with all tools)
├── skills/
│   └── specmint-core/
│       └── SKILL.md                # Symlink to ../../SKILL.md (skills-CLI discovery)
├── references/
│   ├── researcher.md               # Deep-research subagent brief
│   ├── spec-format.md              # SPEC.md format specification
│   └── command-contracts.md        # Behavioral contract checklist for the skill
├── README.md
└── LICENSE
```

## Spec Format

Full specification in [`references/spec-format.md`](references/spec-format.md).
Behavioral guardrails in
[`references/command-contracts.md`](references/command-contracts.md).

### Frontmatter

| Field | Required | Description |
|-------|:---:|-------------|
| `id` | Yes | URL-safe slug (e.g., `user-auth-system`) |
| `title` | Yes | Human-readable name |
| `status` | Yes | `active`, `paused`, `completed`, `archived` |
| `created` | Yes | ISO date (YYYY-MM-DD) |
| `updated` | Yes | ISO date of last modification |
| `priority` | No | `high`, `medium`, `low` (default: medium) |
| `tags` | No | YAML array |

### Conventions

- **Phase markers**: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`
- **Task codes**: `[PREFIX-NN]` — unique per task, auto-incrementing across phases
- **Task checkboxes**: `- [ ] [AUTH-01]` unchecked, `- [x] [AUTH-01]` done
- **Current task**: `← current` after the task text
- **Uncertainty**: `[NEEDS CLARIFICATION]` after the task code on unclear tasks
- **Architecture Diagram**: ASCII art or Mermaid diagrams (system design, data flow, ER, state machines)
- **Library Choices**: Comparison table with alternatives considered and rationale
- **Testing Strategy**: Unit, integration, e2e, and edge case tests with frameworks and file paths
- **Resume Context**: Blockquote with specific file paths, function names, exact next step
- **Decision Log**: Table with date, decision, rationale
- **Deviations**: Table tracking where implementation diverged from spec

## Evaluation Results

Spec Mint Core has been iteratively developed and evaluated using Anthropic's
[Skill Creator](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md)
— the official tool for building, testing, and benchmarking Claude Code skills.

Each iteration was validated through parallel eval runs (with-skill vs
without-skill baselines), automated assertion grading, and quantitative
benchmarking across multiple test scenarios — forge workflow fidelity,
interview gating, research depth, research subagent spawning, spec quality,
and implementation tracking.

**Latest benchmark (iteration 5):**

| Config | Pass Rate |
|--------|-----------|
| With Skill | **100%** (18/18 assertions) |
| Without Skill | 61% (11/18 assertions) |
| Delta | **+39%** |

For more on how Skill Creator works — evals, A/B comparisons, benchmarking,
and the iteration loop — see
[Improving skill-creator: Test, measure, and refine Agent Skills](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills).

## Why Not Just Use Plan Mode?

Plan mode is a good idea with a bad implementation. It restricts Claude to read-only tools and asks for a plan. That's it. No persistence, no research depth, no interviews, no progress tracking.

Spec Mint Core's forge workflow does what plan mode should do:

- **Research depth**: Reads 10-20+ files, searches the web, pulls library docs. Not a quick scan.
- **Interviews**: Asks you targeted questions based on what it found. Multiple rounds until there's no ambiguity.
- **Persistence**: Everything is saved to files. Research notes, interviews, the spec itself. Nothing lives only in context.
- **Resumability**: Close the terminal, come back next week. The spec remembers exactly where you were.
- **Multi-spec**: Juggle multiple features. Switch between them with one command.

## Pair with Kluris

Spec Mint Core reads your codebase. [Kluris](https://kluris.ngvoicu.dev) gives your agents the *other* half — the tribal knowledge that never made it into comments: architecture decisions, past incidents, vendor quirks, the "why" behind every weird choice.

Pair them and the forge workflow's Phase 1b (research) stops guessing. It consults the brain first.

**Inside your AI coding agent:**

```text
> write a spec for OAuth sign-in with GitHub — check the brain, the codebase, and the web

research · phase 1a · reading codebase ........ done
research · phase 1b · kluris wake-up ........... done
research · phase 1c · synthesis ............... done

> spec written to .specs/oauth-github.md — ready for interview.
```

The spec lands grounded in both the code *and* the knowledge your team already agreed to — no re-litigating decisions made six months ago.

**Why it works:**

- **Grounded research** — Phase 1b pulls from a curated brain instead of just the web.
- **Institutional memory** — new hires (and agents) inherit context instantly.
- **Spec reuse** — past specs and decisions surface automatically during research.

**Install Kluris:**

```bash
pipx install kluris
kluris wake-up
```

Full setup at [kluris.ngvoicu.dev](https://kluris.ngvoicu.dev).

## License

MIT

---

<!-- ngvoicu author section — identical across all ngvoicu repos, keep in sync -->
## Author

Built by [Gabriel Voicu](https://ngvoicu.dev) — AI-native consultant & software engineer.

I help companies become AI-native: talks ("Becoming an AI Native Company"), hands-on team training that teaches employees to use AI, and adoption engagements for engineering teams.

- Site: [ngvoicu.dev](https://ngvoicu.dev) — consulting, talks, team training
- Contact: [office@ngvoicu.dev](mailto:office@ngvoicu.dev) · +40 734 704 910
- [LinkedIn](https://www.linkedin.com/in/ngvoicu/) · [GitHub](https://github.com/ngvoicu)

Part of the ngvoicu AI-native toolkit: [Specmint](https://specmint.ngvoicu.dev) (durable AI coding specs) · [Kluris](https://kluris.ngvoicu.dev) (team knowledge brains) · [ConsensFlow](https://consensflow.ngvoicu.dev) (cross-agent second opinions)
