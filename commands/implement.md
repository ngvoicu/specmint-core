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
6. **TUI Progress**: Create a TaskCreate entry for each in-scope task so
   they appear as live checkboxes in the Claude Code TUI:
   - subject: `[TASK-CODE] <task description>`
   - activeForm: `Implementing [TASK-CODE]`
   The SPEC.md checkboxes remain the source of truth — TUI entries are a
   convenience view for real-time progress.

For each task in scope, in order:

### Execute

1. Set the task's TUI entry to `in_progress` via TaskUpdate
2. Mark the task with `← current` in the SPEC.md
2. **Implement the task** — write the actual application code:
   - Follow the patterns and conventions identified in the research notes
   - Use the libraries and approaches specified in the spec
   - Write clean, maintainable, professional code
   - If the task has specific file paths or function names, use them
3. **Write tests** if the task has a corresponding test task or if the spec's
   testing strategy calls for it
4. **Run tests** to verify correctness after implementation

### Update Progress (sacred — never skip)

Progress tracking is the most important bookkeeping in specmint-core. If you
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
10. Set the task's TUI entry to `completed` via TaskUpdate

If you realize you forgot to update after a previous task, stop and fix
it now before continuing with the next task.

### Phase Review (after completing a phase)

When all tasks in a phase are completed, review before moving to the next:

1. Dispatch the `superpowers:code-reviewer` agent (if available) with:
   - The phase requirements from the SPEC.md
   - The list of files created/modified during this phase
   - The acceptance criteria relevant to this phase
2. If no reviewer agent is available, do an inline review:
   - Re-read the phase's tasks and acceptance criteria
   - Verify each task's implementation matches what was specified
   - Check for missing edge cases, incomplete implementations, or spec drift
3. If the review finds issues, fix them before marking the phase complete
4. Log any review findings in the Decision Log

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

## Parallel Task Execution (optional)

When multiple tasks within a phase are independent (no shared files, no
sequential dependencies), you may dispatch them in parallel using the
Agent tool:

1. Identify which tasks have no file-level or logical dependencies on
   each other
2. Dispatch an Agent for each independent task with:
   - The full task specification from the SPEC.md
   - The research notes and library choices for context
   - Clear instructions on which files to create/modify
3. After all agents complete, integrate results and run tests
4. Update all checkboxes, registry, and TUI entries in a single batch

Default to sequential execution. Only parallelize when tasks are clearly
independent and the speedup is worth the coordination overhead. When in
doubt, execute sequentially.

## Verification Gate (mandatory before claiming completion)

Before reporting any phase or spec as complete, provide evidence:

1. Run the project's test suite (or the relevant subset) via Bash
2. Show the actual command and output in your response
3. If tests fail, fix the issues before claiming completion
4. Never use language like "should pass", "probably works", or "seems correct"

This applies at every completion boundary: task, phase, and spec. Evidence
first, then assertions. No exceptions.

## Completion

When all in-scope tasks are done:

- If all tasks in the spec are complete:
  - **Run the full test suite** and show the output (verification gate)
  - Verify all Acceptance Criteria are checked. If any remain unchecked,
    report which ones and ask the user before marking complete.
  - Set all phases to `[completed]`
  - Set spec status to `completed` in frontmatter
  - Update `.specs/registry.md` with `completed` status
  - Present a summary: tasks completed, files created/modified, test output
  - Suggest next spec to activate if any are paused
- If only a phase was completed:
  - **Run tests** for the phase's scope and show the output (verification gate)
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
