# CLAUDE.md — Spec Mint Core

## Project Overview

Spec Mint Core is a Claude Code plugin that replaces ephemeral AI coding plans with persistent, resumable specs. It has two layers:

1. **Plugin layer** — Markdown-based Claude Code plugin (commands, agents, skill)
2. **Skill layer** — Universal SKILL.md that works with any AI coding tool via `npx skills add`

## Repository Structure

```
specmint-core/
├── .claude-plugin/          # Plugin metadata
│   ├── plugin.json          # Name: specmint-core, version 1.0.0
│   └── marketplace.json     # Marketplace registration
├── commands/                # Plugin slash commands (markdown instructions)
│   ├── forge.md             # /forge — research → interview → spec
│   ├── implement.md         # /implement — implement spec tasks, update progress
│   ├── resume.md            # /resume — pick up where you left off
│   ├── pause.md             # /pause — save context and stop
│   ├── switch.md            # /switch — change active spec
│   ├── list.md              # /list — show all specs
│   ├── status.md            # /status — detailed progress
│   └── openapi.md           # /openapi — generate OpenAPI spec from codebase
├── agents/
│   └── researcher.md        # Deep research subagent (opus model)
├── references/
│   ├── spec-format.md       # Complete SPEC.md format specification
│   └── command-contracts.md # Behavioral contract checklist for commands/skill
├── skills/
│   └── specmint-core/
│       └── SKILL.md         # → ../../SKILL.md (symlink for Claude Code plugin discovery)
├── SKILL.md                 # Universal skill definition (works with all tools)
└── README.md
```

## Architecture

### Plugin Layer

The plugin is consumed directly by Claude Code — no build step. Markdown files define behavior:

- **`plugin.json`** — Plugin identity (name: `specmint-core`, version: `3.0.0`)
- **`commands/*.md`** — Each file is a slash command. Claude reads these as instructions.
- **`agents/researcher.md`** — Subagent definition. Uses Opus model with Read, Glob, Grep, Bash, WebSearch, WebFetch, Task tools for exhaustive codebase analysis.
- **`SKILL.md`** — Universal skill with sections for all tools + Claude Code plugin section. Defines natural language triggers ("resume", "what was I working on", "create a spec for X") and session lifecycle behavior.

### Data Layer — `.specs/` Directory

Created in the project root. All tools (Claude Code, Codex, Cursor, etc.) share this directory.

```
.specs/
├── registry.md             # Denormalized index for status/progress lookups
└── <spec-id>/              # Everything for one spec lives together
    ├── SPEC.md             # The spec document
    ├── research-01.md      # Research artifacts
    ├── interview-01.md     # Interview notes
    └── ...
```

**SPEC.md frontmatter is authoritative.** `.specs/registry.md` is a
denormalized index for quick lookups.

Repository policy: `CLAUDE.md`, `AGENTS.md`, and `.specs/` are intentionally
untracked local files in this repo. `AGENTS.md` is used by Codex (see SKILL.md).

## Key Conventions

### Spec Format

Full spec in `references/spec-format.md`. Summary:

- **Frontmatter**: YAML with `id`, `title`, `status`, `created`, `updated`, optional `priority` and `tags`
- **Spec IDs**: Lowercase hyphenated slugs derived from titles (e.g., "User Auth System" → `user-auth-system`)
- **Phase status markers**: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`
- **Task codes**: `[PREFIX-NN]` per task (e.g., `[AUTH-01]`), auto-incrementing across phases
- **Task markers**: `- [ ] [AUTH-01]` unchecked, `- [x] [AUTH-01]` done, `← current` marks the active task
- **Architecture Diagram**: ASCII art or Mermaid diagrams for system design, data flow, ER diagrams
- **Library Choices**: Comparison table with alternatives considered and rationale
- **Testing Strategy**: Unit, integration, e2e, and edge case tests with frameworks and file paths
- **Resume Context**: Blockquote with specific file paths, function names, exact next step
- **Decision Log**: Markdown table with date, decision, rationale

### Status Values

Specs: `active`, `paused`, `completed`, `archived`
Phases: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`

### Forge Workflow Phases

1. Deep Research (codebase + internet + Context7 + library comparison) → `research-01.md`
2. Interview Round 1 → `interview-01.md`
3. Deeper Research → `research-02.md`
4. Interview Round 2+ → repeat until no ambiguity
5. Write SPEC.md (with architecture diagrams, library choices, testing strategy, coherence review) → `SPEC.md`
6. Present spec and wait for user approval

### Implement Workflow

Triggered by "implement the spec", "implement phase N", or "implement all phases":
- Reads active spec, identifies target tasks
- Implements task by task, writing application code
- Updates checkboxes, phase markers, and registry after each task
- Writes tests as specified in the testing strategy
- Logs deviations and decisions

## Versions

- **Plugin**: v1.0.0 (`.claude-plugin/plugin.json`)
- **Author**: Gabriel Voicu (`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`)

## Working on This Codebase

- Plugin commands are pure markdown — edit `commands/*.md` to change behavior
- SKILL.md is universal — it must work for all AI tools, not just Claude Code
- The Claude Code Plugin section in SKILL.md is tool-specific (~20 lines at the top)
- All supported tools use `npx skills add` for setup
- No build step — markdown files are consumed directly
- Windsurf install copies SKILL.md directly to `.windsurf/skills/specmint-core/SKILL.md` (npx creates symlinks that Cascade doesn't follow, so users replace the symlink with a real copy)
- To test plugin changes locally: install the plugin in a test project (`claude plugin add /path/to/specmint-core`), then run slash commands (`/forge`, `/resume`, etc.) and verify behavior
