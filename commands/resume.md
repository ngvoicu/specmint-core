---
description: Resume the active spec — read progress, load context, pick up where you left off
disable-model-invocation: true
---

# Resume Spec

Read the specmint-core skill and follow the "Resuming a Spec" workflow.

1. Read `.specs/registry.md` to find the spec with `active` status
2. If none is active, show the user their specs so they can choose one
3. Load `.specs/<id>/SPEC.md`
4. Parse progress — count completed vs total tasks per phase
5. Find the current phase and current task (`← current` marker)
6. Read the Resume Context section
7. Check if there are research notes (research-*.md, interview-*.md) in
   `.specs/<id>/` that provide additional context
8. Present a compact summary and begin working on the current task

If there are no specs at all, suggest running `/specmint-core:forge` to
create one.
