#!/usr/bin/env bash
# daily-check.sh — automated signal gathering for the 15-minute engineering loop
#
# Runs the "Gather signals" steps defined in .claude/commands/check.md so the
# output can be piped straight into /check for synthesis.
#
# Usage:
#   ./daily-check.sh            # full run
#   ./daily-check.sh --short    # skip file-size scan (faster on large repos)

set -euo pipefail

SHORT=0
[[ "${1:-}" == "--short" ]] && SHORT=1

hr() { printf '\n%s\n' "$(printf '=%.0s' {1..60})"; }

# ── 1. Recent change velocity ──────────────────────────────────────────────────
hr
echo "## 1. Recent commits (last 20)"
git log --oneline -20

# ── 2. What changed most recently ─────────────────────────────────────────────
COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo 0)
if (( COMMIT_COUNT >= 5 )); then
  hr
  echo "## 2. Files changed in last 5 commits"
  git diff HEAD~5 HEAD --stat
else
  echo "## 2. Skipped — fewer than 5 commits in history"
fi

# ── 3. TODO / FIXME / HACK markers ────────────────────────────────────────────
hr
echo "## 3. TODO / FIXME / HACK / XXX / TEMP / DEPRECATED comments"
# Exclude .git directory and common generated paths
if git grep -n -E 'TODO|FIXME|HACK|XXX|TEMP|DEPRECATED' \
    -- ':!*.lock' ':!vendor/' ':!node_modules/' 2>/dev/null; then
  true  # output already printed
else
  echo "(none found)"
fi

# ── 4. Empty / bare error handlers ────────────────────────────────────────────
hr
echo "## 4. Bare error handlers (empty catch / bare except)"
if git grep -n -E \
    'except:\s*$|catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\(e\)\s*\{\s*\}' \
    -- ':!*.lock' ':!vendor/' ':!node_modules/' 2>/dev/null; then
  true
else
  echo "(none found)"
fi

# ── 5. Hardcoded secrets patterns ─────────────────────────────────────────────
hr
echo "## 5. Potential hardcoded secrets"
if git grep -n -iE \
    '(password|secret|api_key|token)\s*=\s*["'"'"'][^"'"'"']{4,}' \
    -- ':!*.lock' ':!vendor/' ':!node_modules/' 2>/dev/null; then
  echo "WARNING: possible hardcoded secrets above — review immediately"
else
  echo "(none found)"
fi

# ── 6. Large files (>300 lines) ───────────────────────────────────────────────
if (( SHORT == 0 )); then
  hr
  echo "## 6. Files over 300 lines (complexity risk)"
  git ls-files | while IFS= read -r f; do
    [[ -f "$f" ]] || continue
    lines=$(wc -l < "$f")
    (( lines > 300 )) && printf '%6d  %s\n' "$lines" "$f"
  done | sort -rn || echo "(none)"
else
  echo "## 6. Skipped (--short mode)"
fi

# ── 7. Dependency manifest summary ────────────────────────────────────────────
hr
echo "## 7. Dependency manifests present"
MANIFESTS=(package.json requirements.txt go.mod Gemfile Cargo.toml pyproject.toml)
found=0
for m in "${MANIFESTS[@]}"; do
  [[ -f "$m" ]] && { echo "  $m"; found=1; }
done
(( found == 0 )) && echo "  (none detected)"

hr
echo "## Done — paste this output into /check for ranked risk synthesis"
