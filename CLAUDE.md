# Claude Engineering Console

> **Core directive:** Optimize for tomorrow being easier than today.

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

### `/plan [goal]`
Propose 1–3 concrete, bounded improvements with expected impact and rationale.
Default goal is highest-ROI for the current session. Always include estimated
scope (≤30 min, ≤2 hr, etc.).

### `/execute`
Execute the most recently agreed plan item. No scope creep. One clean,
contained change. Commit when done.

---

## Kimi AI Integration

Kimi (Moonshot AI) is configured as an MCP server, providing access to its models
alongside Claude within this console.

**Setup:** Set `KIMI_API_KEY` in your environment before starting Claude Code.

```bash
export KIMI_API_KEY=your_moonshot_api_key
```

**Available models** (set via `OPENAI_MODEL` in `.claude/settings.json`):
| Model | Context |
|-------|---------|
| `moonshot-v1-8k` | 8k tokens (default) |
| `moonshot-v1-32k` | 32k tokens |
| `moonshot-v1-128k` | 128k tokens |

**API base:** `https://api.moonshot.cn/v1`

Get an API key at [platform.moonshot.cn](https://platform.moonshot.cn).

---

## Behavior Defaults

- Read before editing. Understand before suggesting.
- Smallest change that achieves the goal.
- No speculative refactors, no unsolicited features.
- Security first: flag injection, auth, and data exposure risks immediately.
- When uncertain, ask. One targeted question beats three wrong assumptions.
