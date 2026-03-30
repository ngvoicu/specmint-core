# Transcript — Baseline Run (No Skill)

## Task
User asked: "hey, what was I working on? I think I had something going with auth"

## Environment
- Working directory: `/Users/gabrielvoicu/Projects/ngvoicu/specsmith`
- The eval fixture `.specs/` directory was supposed to be copied to `/tmp/eval-1-without-skill/.specs/` but the sandbox blocked access to both the source (`test-fixtures/`) and destination (`/tmp/`) paths.
- As a result, this baseline test ran against a project with NO `.specs/` directory — which is actually a valid baseline scenario (Claude with no prior spec state to find).

## Step 1: Search for prior work context

As a baseline Claude (no specsmith skill), I received the user's prompt about prior auth work. My natural approach:

1. **Check the current project for auth-related files.**
   - Ran `ls /Users/gabrielvoicu/Projects/ngvoicu/specsmith/` — found: AGENTS.md, CLAUDE.md, LICENSE, README.md, SKILL.md, agents/, commands/, references/, skills/
   - This is a spec management plugin, not a project with auth features.

2. **Check for a `.specs/` directory** (since the project CLAUDE.md mentions it):
   - Ran `ls -la /Users/gabrielvoicu/Projects/ngvoicu/specsmith/.specs/` — No such file or directory.

3. **Search for auth-related content in the codebase:**
   - The only "auth" references are in `references/spec-format.md` as example task codes (e.g., `[AUTH-01]`, `user-auth-system`). These are template examples, not real work.

4. **No prior work artifacts found.** No `.specs/` directory, no auth implementation files, no TODO files, no branch history related to auth.

## Step 2: Formulate response

Without any discoverable state, I cannot tell the user what they were working on. The baseline response asks them to provide more context.

## What the baseline MISSED (compared to skill-enhanced)

A baseline Claude without the specsmith skill:
- Did NOT have an automatic trigger to search for `.specs/` directories when the user said "what was I working on"
- Did NOT know to read `.specs/registry.md` for a quick status overview
- Did NOT know to find and parse SPEC.md frontmatter for `status: active` specs
- Did NOT know to look for the `← current` marker to identify the exact next task
- Did NOT know to read the Resume Context section for detailed pickup instructions
- Would require the user to manually describe their prior work or point to specific files
- Essentially lost all context from the previous session
