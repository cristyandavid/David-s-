#!/usr/bin/env bash
# Export binder pages as small PNGs into a folder on your Desktop, then open that
# folder and the GitHub upload page so you can drag the files in. No git needed.
# Usage: ./export-plans-local.sh "/path/to/113 Bellefair — Virtual Binder.pdf" [first last]
set -euo pipefail

PDF=${1:?usage: $0 binder.pdf [first last]}
FIRST=${2:-3}   # binder pages 3-5 are Exterior, Front, Back
LAST=${3:-5}
OUT="$HOME/Desktop/113-bellefair-plans"
UPLOAD="https://github.com/cristyandavid/David-s-/upload/claude/daily-engineering-workflow-yHQLQ/113-bellefair/plans"

command -v pdftoppm >/dev/null || { echo "Install poppler first: brew install poppler"; exit 1; }
[ -f "$PDF" ] || { echo "PDF not found: $PDF"; exit 1; }

mkdir -p "$OUT"
pdftoppm -f "$FIRST" -l "$LAST" -r 110 -png "$PDF" "$OUT/binder-p"

echo "Exported to $OUT:"
ls -lh "$OUT"
find "$OUT" -name '*.png' -size +4M -print | while read -r f; do
  echo "warning: $f is over 4 MB; re-run with a lower resolution"
done

open "$OUT" "$UPLOAD" 2>/dev/null || echo "Open $OUT and $UPLOAD, then drag the PNGs in."
echo "Drag the PNGs onto the GitHub page, commit, then tell Claude."
