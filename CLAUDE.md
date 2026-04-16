# Claude Engineering Console

> **Core directive:** Optimize for tomorrow being easier than today.

---

## Repository Overview

This repository is a **Claude Code engineering harness** — a documentation and
workflow-definition project that structures how an AI assistant performs daily
engineering work. It contains no application source code, tests, or build
artifacts. All files are Markdown consumed directly by Claude Code.

### Structure

```
David-s-/
├── CLAUDE.md                      # You are here. Core directives for Claude Code.
└── .claude/
    └── commands/
        ├── check.md               # Implementation of /check slash command
        ├── plan.md                # Implementation of /plan slash command
        └── execute.md             # Implementation of /execute slash command
```

### Slash Command Architecture

Each file in `.claude/commands/` defines a custom slash command:

| File | Command | Role |
|------|---------|------|
| `check.md` | `/check [scope]` | Structured risk audit |
| `plan.md` | `/plan [goal]` | Focused improvement planning |
| `execute.md` | `/execute` | Disciplined change delivery |

Commands are invoked in Claude Code as `/check`, `/plan`, `/execute`. The
`$ARGUMENTS` token in each file receives whatever the user appends after the
command name.

---

## The 15-Minute Daily Loop

| Window | Command | Purpose |
|--------|---------|---------|
| 0–2 min | `/check what is most risky or decaying in this repo right now` | Situation awareness |
| 2–5 min | `/plan highest-ROI improvement I can ship today in ≤30 minutes` | Decision |
| 5–10 min | `/execute` | Focused delivery |
| 10–13 min | `/check regressions, edge cases, and long-term risk` | Review |
| 13–15 min | `/plan what can be automated or templated from today's work` | Compression |

**Absolute rules:**
- One plan. One execution. One review. Stop.
- Staff engineers apply pressure in the right place — they don't grind.

---

## Weekly Focus Pattern

| Day | Focus |
|-----|-------|
| Mon | Risk reduction |
| Tue | Speed tooling |
| Wed | Refactor debt |
| Thu | Tests / safety |
| Fri | Automation / templates |

---

## Slash Commands

### `/check [scope]`
Analyze the codebase for fragile areas, tech debt hotspots, and silent failure
risks. Default scope is the whole repo. Specific scopes: a file path, a module,
or a concern like "auth" or "error handling".

**Implementation:** `.claude/commands/check.md`
- Gathers signals via git log, diff, comment searches, and dep audits
- Groups findings into: Fragile areas / Tech debt hotspots / Silent failure risks
- Outputs ranked list with severity, location, risk, and smallest fix
- Ends with a single "Recommended next action"

### `/plan [goal]`
Propose 1–3 concrete, bounded improvements with expected impact and rationale.
Default goal is highest-ROI for the current session. Always include estimated
scope (≤30 min, ≤2 hr, etc.).

**Implementation:** `.claude/commands/plan.md`
- Reads git log and prior `/check` findings before proposing anything
- Maps day-of-week to weekly focus pattern
- Each option: title, scope, impact, why-now, approach, risk
- Ends with a single recommended option and one-sentence rationale
- Hard constraints: ≤3 files per option, no new deps without flagging cost

### `/execute`
Execute the most recently agreed plan item. No scope creep. One clean,
contained change. Commit when done.

**Implementation:** `.claude/commands/execute.md`
- Requires a named plan item; stops and prompts `/plan` if none exists
- Pre-flight: states the item, files to touch, success condition
- Post-change: diff summary, test/lint run if detectable, commit
- Commit format: `<type>(<scope>): <what changed>` + one-sentence why
- Surfaces: assumptions made, debt noticed (not fixed), follow-on actions

---

## Git Conventions

**Branch naming:** `claude/<description>-<random-suffix>` (Claude-generated branches)

**Commit format:**
```
<type>(<scope>): <what changed>

<one sentence: why this change, what risk or friction it removes>
```

Types: `fix`, `refactor`, `test`, `chore`, `perf`, `docs`, `feat`

**Active branches:**
- `claude/add-claude-documentation-ZDq1R` — documentation updates
- `claude/daily-engineering-workflow-yHQLQ` — workflow additions

---

## Behavior Defaults

These rules apply to all Claude Code sessions in this repo:

- Read before editing. Understand before suggesting.
- Smallest change that achieves the goal.
- No speculative refactors, no unsolicited features.
- Security first: flag injection, auth, and data exposure risks immediately.
- When uncertain, ask. One targeted question beats three wrong assumptions.
- No new files unless strictly necessary — prefer editing existing ones.
- Do not modify `.claude/commands/` unless the user explicitly asks to change
  a slash command's behavior.

---

## Modifying This Repository

Since the entire repo is documentation, all changes are low-risk and reversible.
The only meaningful actions are:

1. **Edit `CLAUDE.md`** — update directives, add context, document new patterns
2. **Edit `.claude/commands/*.md`** — refine slash command behavior
3. **Add new `.claude/commands/<name>.md`** — register a new slash command

No build step, no tests, no deploy pipeline. Commit and push is the full
release cycle.
