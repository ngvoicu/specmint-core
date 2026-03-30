# Command Contracts

This file defines functional contracts for `commands/*.md` and the universal
`SKILL.md` behavior. Use it as a review checklist before releases.

## Global Contracts

1. `SPEC.md` frontmatter is authoritative; registry is denormalized.
2. Exactly one active spec should exist after any write operation.
3. All write workflows update `SPEC.md` first, then recompute/update registry.
4. Forge workflow never writes application code.
5. Phase markers use `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`.
   Task lines use checkboxes and `← current`; tasks are not tagged `[blocked]`.
6. **Progress tracking is sacred.** After every task completion: update SPEC.md
   (checkbox, current marker, phase marker), update registry (progress, date),
   then re-read both files to verify consistency. Never skip this.
7. **Acceptance criteria are required for feature specs.** Forge must include
   an `## Acceptance Criteria` section with testable checkbox conditions.
   Implement must check off criteria as they are satisfied and verify all are
   met before marking a spec complete.

## Command Contracts

### `/specmint-core:forge`

1. Resolve `<spec-id>` before research output paths are referenced.
2. Collision-check existing spec IDs before creating new files.
3. Forge must not run in plan mode; if plan mode is active, require exit before
   continuing.
4. Output scope is `.specs/` artifacts only (`research-*.md`, `interview-*.md`,
   `SPEC.md`, `registry.md` updates).
5. After approval, handoff to `/specmint-core:implement` instead of implementing
   inside forge.
6. Interview must ask about acceptance criteria ("What does 'done' look like?").
7. SPEC.md must include `## Acceptance Criteria` with testable checkboxes.

### `/specmint-core:implement`

1. Supports scope parsing: current flow, phase-specific, all phases, task code.
2. For each completed task: checkbox + current marker + phase markers +
   frontmatter `updated` + registry progress/date. Then re-read both files
   to verify consistency.
3. At phase completion, review and check off satisfied acceptance criteria.
4. At spec completion, verify all acceptance criteria are checked before
   marking complete.
5. Blocked handling:
   - Keep blocked tasks unchecked.
   - Mark phase `[blocked]` only when the phase is blocked.
   - Record blocker context in Resume Context/Decision Log/Deviations as needed.

### `/specmint-core:resume`

1. If no active spec exists, list specs and request target.
2. Include progress, current phase/task, and Resume Context in output.

### `/specmint-core:pause`

1. If no active spec exists, report no-op and stop.
2. Persist detailed Resume Context with concrete file/function references.
3. Set status `paused` and sync registry.

### `/specmint-core:switch`

1. Validate target ID and target `SPEC.md` existence before pausing current spec.
2. If target already active, report and stop.
3. Pause current (if any), activate target, resume target, sync registry.

### `/specmint-core:list`

1. Handle missing registry gracefully.
2. Group by status in order: active, paused, completed, archived.
3. If `SPEC.md` missing for a row, keep row visible and flag it.

### `/specmint-core:status`

1. Show detailed phase/task breakdown for active spec.
2. If no active spec, guide to activate one.

### `/specmint-core:openapi`

1. Generate/update `.openapi/openapi.yaml` and `.openapi/endpoints/*.md`.
2. Preserve manual additions when updating existing files.
3. Report endpoint/schema/security counts and manual-review candidates.

## Universal Skill Contract

1. `SKILL.md` must include cross-tool behavior for all declared triggers.
2. If `generate openapi` is listed as a trigger, OpenAPI workflow behavior must
   be defined in `SKILL.md` (not only plugin command files).
3. Command-specific docs can specialize behavior but cannot violate critical
   invariants from `SKILL.md`.

## Release Checklist

1. `claude plugin validate .claude-plugin/plugin.json` passes.
2. `claude plugin validate .claude-plugin/marketplace.json` passes without
   warnings.
3. Paths referenced in docs and templates exist (excluding placeholder paths).
4. Command contracts in this file still match `commands/*.md` and `SKILL.md`.
