Generate a focused improvement plan. The user's goal (if any) is: $ARGUMENTS

If no goal is specified, default to: "highest-ROI improvement I can ship today in ≤30 minutes"

## Step 1: Read the current state

Before proposing anything:
- Review recent git log to understand what's been touched
- Review any findings from a prior `/check` in this session
- Identify the day of the week and map it to the weekly focus pattern:
  - Mon → Risk reduction
  - Tue → Speed tooling
  - Wed → Refactor debt
  - Thu → Tests / safety
  - Fri → Automation / templates
  - Other → Default to highest-ROI

## Step 2: Generate options

Propose exactly 1–3 options. Each option must:
- Be completable in the stated time window
- Have a clear, measurable outcome
- Not require changes outside the stated scope

For each option use this format:

```
## Option [N]: <title>

**Scope:** ≤30 min | ≤2 hr | etc.
**Impact:** <what improves and by how much — be specific>
**Why now:** <why this matters today, not next week>
**Approach:**
  1. <step>
  2. <step>
  3. <step>
**Risk:** <what could go wrong, and how to contain it>
```

## Step 3: Recommend one

End with:

```
**Recommended:** Option [N] — <one sentence rationale>
```

Base the recommendation on: highest risk reduction OR highest leverage for future work, whichever aligns with the weekly focus.

## Constraints

- No option may touch more than 3 files unless the goal explicitly requires it
- No option may introduce new dependencies without flagging it as a cost
- No option may be "refactor everything" — scope must be concrete and bounded
- If the user's goal is unclear, ask one clarifying question before proposing options
