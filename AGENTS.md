# Repository Guidelines

For architectural context across the Mint family (core vs TDD, distribution, evals), read and write to the **ngvoicu-sme** brain through kluris — `/kluris-ngvoicu-sme` (Claude Code skill: search, learn, remember, create) or `kluris search "<query>" --brain ngvoicu-sme` (CLI). Never edit brain files by hand.

## Project Structure & Module Organization
- `SKILL.md`: universal, cross-tool skill instructions (Claude Code, Codex, Cursor, Windsurf, Cline, Gemini CLI) — the full forge/implement/resume workflow.
- `references/researcher.md`: deep-research subagent brief, spawned via the Task tool during forge.
- `references/spec-format.md`: canonical `SPEC.md` format and markers.
- `references/command-contracts.md`: behavioral contract checklist for the skill.
- `skills/specmint-core/SKILL.md`: symlink to `../../SKILL.md` for skills-CLI discovery (never replace with a real file).
- `.specs/`: local dogfooding output for specs (gitignored in this repo).

## Build, Test, and Development Commands
- `rg --files`: fast inventory of repository files before editing.
- `sed -n '1,160p' SKILL.md`: inspect skill content in terminal.
- `npx skills add ngvoicu/specmint-core -g -a codex`: smoke-test skill installation flow.
- `git log --oneline -n 10`: review recent commit style before committing.

This repository has no compile/build pipeline; Markdown and JSON are consumed directly by host tools.

## Coding Style & Naming Conventions
- Keep content ASCII Markdown/JSON with concise, imperative instructions.
- Use lowercase, hyphenated filenames for reference docs (for example `references/spec-format.md`).
- Keep workflow docs procedural (numbered steps, explicit file paths, deterministic behavior).
- Follow spec naming in examples: spec IDs are lowercase-hyphenated (`user-auth-system`), task codes are `[AUTH-01]`, and phase markers use `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`.

## Testing Guidelines
- No automated test suite currently exists in this repository.
- Perform manual validation for each change:
  - Confirm referenced paths/files exist.
  - Smoke-test the install/use flow in a disposable project when skill behavior changes (e.g. `npx skills add ./. -g -a claude-code`, or copy `SKILL.md` into the tool's skills directory, then exercise forge / resume / implement).
- If you change spec-format rules, update both `SKILL.md` and `references/spec-format.md` in the same PR.

## Commit & Pull Request Guidelines
- Git history is mostly terse `update` commits, with occasional Conventional Commit messages (for example `feat:`).
- Prefer descriptive, scoped commit messages (for example `docs: tighten openapi command generation rules`).
- PRs should include purpose, affected files, behavior changes (before/after prompt snippets), and linked issue/context when available.
