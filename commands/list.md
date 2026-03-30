---
description: List all specs with status, progress, and priority
disable-model-invocation: true
---

# List Specs

Show all specs grouped by status.

1. If `.specs/registry.md` does not exist, report "No specs yet" and suggest
   running `/specmint-core:forge`.
2. Read `.specs/registry.md`.
3. For each spec row, read `.specs/<id>/SPEC.md` to compute accurate
   task counts (`[x]` and total), current phase, and current task marker.
4. Present grouped by status in this order: `active`, `paused`, `completed`,
   `archived`. If a registry row points to a missing SPEC.md, show it under
   the right status with `(SPEC.md missing)` and continue.

```
Active:
  → auth-system: User Auth System (5/12 tasks, Phase 2) [high]

Paused:
  ⏸ api-refactor: API Refactoring (2/8 tasks, Phase 1) [medium]
  ⏸ dark-mode: Dark Mode Support (0/6 tasks, not started) [low]

Completed:
  ✓ ci-pipeline: CI Pipeline Setup (8/8 tasks) [high]
```

If there are no rows after the table header, suggest running
`/specmint-core:forge` to create one.
