# CLAUDE.md — Spec Mint Core

## Project Overview

Spec Mint Core is a markdown-only universal skill (no build step, no dependencies) that replaces ephemeral AI coding plans with persistent, resumable specs. It ships as a universal skill (`SKILL.md`) that works with Claude Code, Codex, Cursor, Windsurf, Cline, and Gemini CLI via `npx skills add`.

## Knowledge base

Architectural details and distribution context for the Mint family live in the **ngvoicu-sme** brain. Read and write through kluris (never edit brain files by hand — the skill enforces an approval protocol):

- `/kluris-ngvoicu-sme` — Claude Code skill (search, learn, remember, create)
- `kluris search "<query>" --brain ngvoicu-sme` — direct search

Topics relevant to this repo: specmint-core overview, architecture, core-vs-tdd differences, distribution, evals.

## Architecture

The skill has two conceptual layers:

**Skill layer** — `SKILL.md` (the universal skill that drives the full workflow) and `references/researcher.md` (deep-research subagent brief, spawned via the Task tool during forge). AI tools read these markdown files as behavioral instructions.

**Data layer** — `.specs/` directory created in the *consuming* project root (not this repo). All tools share this directory. SPEC.md frontmatter is authoritative; `registry.md` is a denormalized index for quick lookups. See `references/spec-format.md` for the full format specification.

### File Relationships

These files must stay in sync — changing one without the other will cause behavioral drift:

| Source of truth | Must match |
|----------------|------------|
| `references/spec-format.md` | Spec format rules in `SKILL.md` |
| `SKILL.md` | Behavioral contracts in `references/command-contracts.md` |

`skills/specmint-core/SKILL.md` is a symlink to `../../SKILL.md` — never replace it with a real file.

## Key Conventions

- `CLAUDE.md`, `AGENTS.md`, and `.specs/` are intentionally untracked in this repo
- `AGENTS.md` provides Codex-specific guidelines (see `SKILL.md` for details)
- `SKILL.md` must work for all AI tools — keep its behavior tool-agnostic
- Spec format details (IDs, task codes, phase markers, sections) are in `references/spec-format.md` — that is the single source of truth
- Workflow details (forge phases, implement lifecycle) live in `SKILL.md`

## Working on This Codebase

- Edit `SKILL.md` to change universal skill behavior (forge, implement, resume, etc.)
- Edit `references/researcher.md` to change the deep-research subagent brief
- Edit `references/spec-format.md` to change the SPEC.md format
- Smoke-test changes: install the skill into a disposable project (e.g. `npx skills add ./. -g -a claude-code`, or copy `SKILL.md` into the tool's skills directory), then exercise the natural-language triggers (forge / resume / implement)
- Windsurf users must replace the symlink at `.windsurf/skills/specmint-core/SKILL.md` with a real file copy (Cascade doesn't follow symlinks)

## Eval Infrastructure

Eval workspace at `specmint-workspace/` (gitignored). Contains iterations 1-5 with evals covering forge workflow, resume, spec-then-stop, research depth, spec quality, implement, researcher spawn, acceptance criteria, and progress tracking. Eval definitions in `specmint-workspace/evals/evals.json`.
