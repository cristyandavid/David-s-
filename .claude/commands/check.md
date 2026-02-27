Perform a structured risk audit of this repository. The user's input (if any) is: $ARGUMENTS

Follow this sequence exactly:

## 1. Gather signals

Run these in order and collect the output:
- `git log --oneline -20` — recent change velocity and authors
- `git diff HEAD~5 HEAD --stat` — what changed most recently (skip if fewer than 5 commits)
- Search for `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP`, `DEPRECATED` comments across all source files
- Look for bare `except:` / `catch (e) {}` / empty error handlers
- Check for hardcoded secrets patterns: `password =`, `secret =`, `api_key =`, `token =` assigned to string literals
- Identify files or functions larger than ~300 lines (complexity risk)
- Check `package.json`, `requirements.txt`, `go.mod`, or equivalent for obviously outdated or known-vulnerable deps

## 2. Synthesize findings

Group findings into exactly three buckets:

### Fragile areas
Code that will likely break under pressure, edge cases, or load. List file:line where possible.

### Tech debt hotspots
Areas where accumulated shortcuts will slow down future work. Estimate the drag.

### Silent failure risks
Places where errors are swallowed, assumptions go unvalidated, or failures produce no signal. These are the most dangerous.

## 3. Output format

Return a ranked list (most urgent first) using this template for each item:

```
[SEVERITY: high|medium|low] <one-line description>
  Location: <file:line or module>
  Risk: <what breaks and when>
  Fix: <smallest intervention that meaningfully reduces risk>
```

End with a single "Recommended next action" — the one thing to address first.

Do not suggest improvements outside the risk/debt/silent-failure scope.
Do not propose features.
