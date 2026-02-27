Execute the most recently agreed plan item from this session. The user's input (if any) is: $ARGUMENTS

## Pre-flight

Before writing a single line of code:
1. State the plan item you are executing (quote it exactly)
2. List the files you will touch
3. State the success condition — how will you know it worked?

If there is no agreed plan item in this session, stop and say:
> No plan selected. Run `/plan` first and choose an option.

## Execution rules

- Read every file before editing it
- Make the smallest change that achieves the goal
- No scope creep: if you discover related issues, note them but do not fix them
- No new dependencies without explicit user approval
- No speculative abstractions — solve the problem in front of you
- Security: if you introduce any user input handling, external calls, or auth logic, flag it explicitly

## After the change

1. Show a diff summary (which files changed, what was added/removed)
2. Run any existing tests or linters if a test/lint command is detectable in the repo (`package.json` scripts, `Makefile`, `pytest`, etc.)
3. State whether the success condition was met
4. Commit with a message in this format:
   ```
   <type>(<scope>): <what changed>

   <one sentence: why this change, what risk or friction it removes>
   ```
   Types: `fix`, `refactor`, `test`, `chore`, `perf`, `docs`

## What to surface after committing

Flag any of the following if discovered during execution:
- Assumptions you made that the user should validate
- Debt you noticed but did not touch (add to backlog, not to this change)
- Follow-on actions that would compound today's improvement
