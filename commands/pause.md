---
description: Pause the active spec — save detailed resume context for next session
disable-model-invocation: true
---

# Pause Spec

Read the specmint-core skill and follow the "Pausing a Spec" workflow.

1. Read `.specs/registry.md` to find the spec with `active` status
2. If no active spec exists, report that there is nothing to pause and stop
3. Load the SPEC.md
4. Capture everything about the current state:
   - Which task was in progress
   - What files were modified (specific paths, function names, line ranges)
   - Key decisions made this session
   - Blockers or open questions
   - The exact next step someone should take
5. Write all of this to the Resume Context section in SPEC.md
6. Update checkboxes to reflect actual progress
7. Move `← current` to the correct task
8. Add session decisions to Decision Log
9. Set status to `paused`, update the `updated` date
10. Update `.specs/registry.md`
11. Confirm to the user that context was saved

Be extremely specific in the Resume Context. Write it as if briefing a
colleague who has never seen this code and will pick up tomorrow.
