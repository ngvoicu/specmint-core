---
description: Show detailed progress of the active spec
disable-model-invocation: true
---

# Spec Status

Show detailed progress of the active spec.

1. If `.specs/registry.md` does not exist, report "No specs yet" and suggest
   running `/specmint-core:forge`.
2. Read `.specs/registry.md` and find the spec with `active` status.
3. If no active spec exists:
   - If specs exist, list them and ask which one to activate.
   - If no specs exist, suggest running `/specmint-core:forge`.
4. Load `.specs/<id>/SPEC.md` for the active spec and parse all phases
   and tasks.
5. Show a detailed breakdown with explicit markers (`✓` done, `→` in-progress,
   `○` pending), plus exact progress (`X/Y` tasks), current phase, and current
   task.

```
User Auth System [active, high priority]
Created: 2026-02-10 | Updated: 2026-02-11

Phase 1: Foundation [completed] ✓
  ✓ Set up auth middleware
  ✓ Create user model
  ✓ Implement JWT token generation
  ✓ Add refresh token logic

Phase 2: OAuth Integration [in-progress] →
  ✓ Google OAuth provider
  → GitHub OAuth provider ← current
  ○ Token exchange flow

Phase 3: Testing [pending] ○
  ○ Unit tests for auth middleware
  ○ Integration tests
  ○ Security audit

Progress: 5/10 tasks (50%)
Current: GitHub OAuth provider
```

6. Also show the Resume Context section.
7. If there are research notes (research-*.md, interview-*.md) in
   `.specs/<id>/`, mention them with file count.
