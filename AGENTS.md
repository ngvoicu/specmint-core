# Repository Guidelines

## Project Structure & Module Organization
- `.claude-plugin/`: plugin metadata for Claude Code distribution (`plugin.json`, `marketplace.json`).
- `commands/`: one Markdown file per slash command (`forge.md`, `resume.md`, `pause.md`, `switch.md`, `list.md`, `status.md`, `openapi.md`).
- `agents/researcher.md`: subagent prompt used for deep codebase research.
- `references/spec-format.md`: canonical `SPEC.md` format and markers.
- `SKILL.md`: universal, cross-tool skill instructions (Codex, Cursor, Windsurf, Cline, Gemini CLI).
- `.specs/`: local dogfooding output for specs (gitignored in this repo).

## Build, Test, and Development Commands
- `rg --files`: fast inventory of repository files before editing.
- `sed -n '1,160p' commands/forge.md`: inspect command content in terminal.
- `npx skills add ngvoicu/specmint-core -g -a codex`: smoke-test skill installation flow.
- `git log --oneline -n 10`: review recent commit style before committing.

This repository has no compile/build pipeline; Markdown and JSON are consumed directly by host tools.

## Coding Style & Naming Conventions
- Keep content ASCII Markdown/JSON with concise, imperative instructions.
- Use lowercase, hyphenated filenames for command docs (for example `commands/openapi.md`).
- Keep command docs procedural (numbered steps, explicit file paths, deterministic behavior).
- Follow spec naming in examples: spec IDs are lowercase-hyphenated (`user-auth-system`), task codes are `[AUTH-01]`, and phase markers use `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`.

## Testing Guidelines
- No automated test suite currently exists in this repository.
- Perform manual validation for each change:
  - Verify `.claude-plugin/*.json` stays valid JSON.
  - Confirm referenced paths/files exist.
  - Smoke-test install/use flow in a disposable project when command behavior changes.
- If you change spec-format rules, update both `SKILL.md` and `references/spec-format.md` in the same PR.

## Commit & Pull Request Guidelines
- Git history is mostly terse `update` commits, with occasional Conventional Commit messages (for example `feat:`).
- Prefer descriptive, scoped commit messages (for example `docs: tighten openapi command generation rules`).
- PRs should include purpose, affected files, behavior changes (before/after prompt snippets), and linked issue/context when available.
