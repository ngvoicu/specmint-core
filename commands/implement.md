---
description: Implement the active spec — work through tasks, mark them complete, update progress
disable-model-invocation: true
---

# Implement Spec

Implement tasks from the active spec. The argument can specify scope.

User's request: $ARGUMENTS

## Scope Detection

Parse the user's request to determine what to implement:

- **No argument / "the spec" / "implement"** → Start from the `← current`
  task and work forward through all remaining tasks
- **"phase N" / "phase <name>"** → Implement all unchecked tasks in that
  specific phase only
- **"all phases" / "everything"** → Implement all remaining unchecked tasks
  across all phases, in order
- **"task CODE-NN"** → Implement just that specific task

## Implementation Workflow

1. Read `.specs/registry.md` to find the spec with `active` status
2. If none is active, show the user their specs so they can choose one
3. Load `.specs/<id>/SPEC.md`
4. Parse all phases and tasks — identify which tasks are in scope
5. Present a brief plan: "I'll implement N tasks across M phases. Starting
   with [TASK-CODE] — <task description>."

For each task in scope, in order:

### Execute

1. Mark the task with `← current` in the SPEC.md
2. **Implement the task** — write the actual application code:
   - Follow the patterns and conventions identified in the research notes
   - Use the libraries and approaches specified in the spec
   - Write clean, maintainable, professional code
   - If the task has specific file paths or function names, use them
3. **Write tests** if the task has a corresponding test task or if the spec's
   testing strategy calls for it
4. **Run tests** to verify correctness after implementation

### Update Progress (sacred — never skip)

Progress tracking is the most important bookkeeping in specsmith. If you
skip this, resume breaks, the registry lies, and the spec becomes useless.
After completing each task, immediately update the spec files:

1. Check off the task: `- [ ]` → `- [x]`
2. Remove `← current` from the completed task
3. Move `← current` to the next unchecked task (or the next in-scope task)
4. If all tasks in the current phase are done:
   - Phase status: `[in-progress]` → `[completed]`
   - Next phase (if any): `[pending]` → `[in-progress]`
   - Review Acceptance Criteria — check off any that are now satisfied
5. Update the `updated` date in YAML frontmatter
6. Recompute progress count (X/Y) from checkboxes
7. Update progress and `updated` date in `.specs/registry.md`
8. **Verify**: Re-read both `SPEC.md` and `registry.md` to confirm edits
   landed. If registry progress doesn't match SPEC.md checkbox count, fix
   it before moving on.
9. Update Resume Context with current state

If you realize you forgot to update after a previous task, stop and fix
it now before continuing with the next task.

### Handle Issues

- If a task is more complex than expected, split it into subtasks and update
  the SPEC.md before continuing
- If implementation diverges from the spec (better approach found, errors in
  spec, etc.), log it in the **Deviations** section
- Log any new technical decisions in the **Decision Log**
- If blocked on a task:
  - Keep the task unchecked and add a blocker note in Resume Context
  - Set the phase marker to `[blocked]` only when the whole phase is blocked
  - Move to the next unblocked task if possible

## Completion

When all in-scope tasks are done:

- If all tasks in the spec are complete:
  - Verify all Acceptance Criteria are checked. If any remain unchecked,
    report which ones and ask the user before marking complete.
  - Set all phases to `[completed]`
  - Set spec status to `completed` in frontmatter
  - Update `.specs/registry.md` with `completed` status
  - Present a summary: tasks completed, files created/modified, tests passing
  - Suggest next spec to activate if any are paused
- If only a phase was completed:
  - Report phase completion and remaining work
  - Set the next phase to `[in-progress]` if applicable

## Quality Standards

During implementation:
- Write clean, simple, maintainable code — no over-engineering
- Follow existing codebase patterns and conventions
- Use the libraries specified in the spec's Library Choices section
- Write comprehensive tests as specified in the Testing Strategy
- Handle edge cases identified in the spec
- Validate at system boundaries, trust internal code
