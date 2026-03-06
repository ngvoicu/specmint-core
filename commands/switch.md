---
description: Switch to a different spec — pause current, activate and resume target
disable-model-invocation: true
---

# Switch Spec

Switch to a different spec. The argument should be a spec ID.

Target: $ARGUMENTS

1. Validate the target first:
   - If no argument, show available specs and ask for target ID
   - If `.specs/<target-id>/SPEC.md` does not exist, report and stop
2. If target is already active, report "already active" and stop.
3. **Pause current spec** (if any) — run full pause workflow (save resume
   context, update checkboxes, set status to paused)
4. **Load target spec** — read `.specs/<target-id>/SPEC.md`
5. **Activate it** — set its status to `active` in both frontmatter and
   `.specs/registry.md`
6. **Resume it** — run the full resume workflow (parse progress, find
   current task, read resume context, present summary)
7. **Update registry** — ensure both specs' statuses are current in
   `.specs/registry.md`

This should feel like one seamless operation — context switch in a
single command.
