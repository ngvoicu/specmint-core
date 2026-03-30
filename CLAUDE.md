# CLAUDE.md — Spec Mint Core

## Project Overview

Spec Mint Core is a markdown-only Claude Code plugin (no build step, no dependencies) that replaces ephemeral AI coding plans with persistent, resumable specs. It also ships as a universal skill (`SKILL.md`) that works with Codex, Cursor, Windsurf, Cline, and Gemini CLI via `npx skills add`.

Version: 1.0.0 (`plugin.json`)

## Architecture

The plugin has two conceptual layers:

**Plugin layer** — `commands/*.md` (one file per slash command), `agents/researcher.md` (Opus-model deep research subagent), `.claude-plugin/` (metadata). Claude Code reads these markdown files as behavioral instructions.

**Data layer** — `.specs/` directory created in the *consuming* project root (not this repo). All tools share this directory. SPEC.md frontmatter is authoritative; `registry.md` is a denormalized index for quick lookups. See `references/spec-format.md` for the full format specification.

### File Relationships

These files must stay in sync — changing one without the other will cause behavioral drift:

| Source of truth | Must match |
|----------------|------------|
| `references/spec-format.md` | Spec format rules in `SKILL.md` |
| `commands/*.md` | Behavioral contracts in `references/command-contracts.md` |
| `.claude-plugin/plugin.json` | Version references in `README.md` and `marketplace.json` |

`skills/specmint-core/SKILL.md` is a symlink to `../../SKILL.md` — never replace it with a real file.

## Key Conventions

- `CLAUDE.md`, `AGENTS.md`, and `.specs/` are intentionally untracked in this repo
- `AGENTS.md` provides Codex-specific guidelines (see `SKILL.md` for details)
- `SKILL.md` must work for all AI tools — the Claude Code Plugin section at the top is tool-specific and kept to ~20 lines
- Spec format details (IDs, task codes, phase markers, sections) are in `references/spec-format.md` — that is the single source of truth
- Workflow details (forge phases, implement lifecycle) are in the respective `commands/*.md` files

## Working on This Codebase

- Edit `commands/*.md` to change slash command behavior
- Edit `SKILL.md` to change universal skill behavior
- Edit `references/spec-format.md` to change the SPEC.md format
- Validate `.claude-plugin/*.json` stays valid JSON after edits
- Smoke-test changes: `claude plugin add /path/to/specmint-core` in a disposable project, then run `/forge`, `/resume`, etc.
- Windsurf users must replace the symlink at `.windsurf/skills/specmint-core/SKILL.md` with a real file copy (Cascade doesn't follow symlinks)

## Eval Infrastructure

Eval workspace at `specmint-workspace/` (gitignored). Contains iterations 1-5 with evals covering forge workflow, resume, spec-then-stop, research depth, spec quality, implement, researcher spawn, acceptance criteria, and progress tracking. Eval definitions in `specmint-workspace/evals/evals.json`.
