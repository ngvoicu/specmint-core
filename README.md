# specmint-core

**Your AI coding plan should not die when your session does.**

[![Benchmark +39%](https://img.shields.io/badge/benchmark-%2B39%25-brightgreen)](https://github.com/ngvoicu/specmint-core#evaluation-results)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-orange)](https://marketplace.claudecode.io)

specmint-core gives AI coding sessions persistent memory. Plan something in one session, close the terminal, switch tools, come back three weeks later — your spec is still there, exactly where you left it.

**Benchmark result (Anthropic Skill Creator):** 100% assertion pass rate with specmint-core vs. 61% without — a **+39% delta**.

---

## Install

### Claude Code (native plugin — full feature set)

```bash
/plugin marketplace add ngvoicu/specmint-core
```

### All other tools (universal skill)

```bash
npx skills add ngvoicu/specmint-core -g -a <tool>
```

#### Supported tools

| Tool | Install command |
|------|----------------|
| Claude Code | `/plugin marketplace add ngvoicu/specmint-core` |
| Cursor | `npx skills add ngvoicu/specmint-core -g -a cursor` |
| Windsurf | `npx skills add ngvoicu/specmint-core -g -a windsurf` |
| Cline | `npx skills add ngvoicu/specmint-core -g -a cline` |
| Codex | `npx skills add ngvoicu/specmint-core -g -a codex` |
| Gemini CLI | `npx skills add ngvoicu/specmint-core -g -a gemini` |

All tools share the same `.specs/` directory. Switch tools mid-feature — your context comes with you.

---

## The problem

Traditional AI coding "plan mode" lives only in conversation context. Once you close your terminal or start a new session, the plan vanishes. There's no mechanism to:

- Resume partially-completed implementation plans
- Alternate between multiple feature specifications
- Maintain a clear record of completed versus pending tasks
- Preserve the research and architectural decisions underlying the plan

specmint-core solves all four through persistent file-based specs.

---

## How it works

### `/forge "description"`

Initiates a research-first workflow before writing a single line of spec:

1. **Deep Research** — Reads 10–20+ actual files from your codebase, searches the web for best practices, reviews library docs, compares alternatives. Saved to `.specs/<id>/research-01.md`.
2. **Targeted Interviews** — Asks codebase-specific questions: *"I see Express middleware pattern X in `src/middleware/`. Should auth follow the same pattern?"* Generic questions don't happen.
3. **Deeper Investigation** — Explores specific directions from your answers, checks feasibility, identifies edge cases.
4. **Additional Interview Rounds** — Continues until every task is concrete and unambiguous.
5. **Specification Writing** — Synthesizes everything into a structured SPEC.md: architecture diagrams, library comparisons, phased tasks, testing strategy, decision log, resume context.
6. **Implementation** — Work through tasks via `/implement`, checking off progress and logging decisions.

### `/pause` and `/resume`

```bash
/pause   # saves exact stopping point: file paths, function names, next task
/resume  # picks up from there — works weeks later, works from a different tool
```

### Other commands

| Command | Function |
|---------|----------|
| `/specmint-core:forge "description"` | Initiate research-interview-spec workflow |
| `/specmint-core:implement` | Continue current task or implement specific phase |
| `/specmint-core:resume` | Load paused spec from resume context |
| `/specmint-core:pause` | Save detailed context and pause |
| `/specmint-core:switch <spec-id>` | Activate different spec |
| `/specmint-core:list` | Display all specs grouped by status |
| `/specmint-core:status` | Show detailed progress |
| `/specmint-core:openapi` | Generate OpenAPI documentation |

---

## Spec format

Specs live in `.specs/` as plain markdown with YAML frontmatter — git-trackable, readable in any editor, accessible from any tool.

```
.specs/
├── registry.md
└── user-auth-system/
    ├── SPEC.md
    ├── research-01.md
    ├── interview-01.md
    ├── research-02.md
    └── interview-02.md
```

**Frontmatter fields:** `id`, `title`, `status` (`active` / `paused` / `completed` / `archived`), `created`, `updated`, `priority`, `tags`

**Content conventions:**
- Phase markers: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`
- Task codes: `[PREFIX-NN]` format
- Current task indicator: `← current`
- Architecture: ASCII art or Mermaid diagrams
- Decision documentation: table with date, decision, reasoning
- Implementation divergences: tracked in separate table

---

## Multi-tool compatibility

All tools accessing the same `.specs/` directory stay synchronized through shared conventions:
- Task codes (`[AUTH-03]`) are identical across tools
- Current task marker (`← current`) is visible everywhere
- Resume context includes file paths and function names
- Phase status indicators are uniform

**Note:** Avoid simultaneous execution on the same spec across tools. Parallel work on different specs is fine.

---

## Evaluation results

Benchmark testing via Anthropic Skill Creator:

| Condition | Pass rate | Assertions |
|-----------|-----------|-----------|
| With specmint-core | **100%** | 18/18 |
| Without | 61% | 11/18 |
| **Delta** | **+39%** | — |

Measured across: research fidelity, interview quality, spec accuracy, and implementation tracking.

---

## Related tools

The Mint plugin ecosystem:
- **specmint-tdd** — test-driven development enforcement variant
- **schemint-pg** — PostgreSQL schema design and optimization

---

## License

MIT
