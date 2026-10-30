#!/usr/bin/env bash
# Export binder pages as small PNGs and push them to this repo so Claude can read them.
# Usage: ./export-plans.sh "/path/to/113 Bellefair — Virtual Binder.pdf" [first-page last-page]
# Needs poppler (macOS: brew install poppler) and git push access.
set -euo pipefail

PDF=${1:?usage: $0 binder.pdf [first last]}
FIRST=${2:-3}   # binder pages 3-5 are Exterior, Front, Back
LAST=${3:-5}
DIR="$(cd "$(dirname "$0")" && pwd)/plans"

mkdir -p "$DIR"
pdftoppm -f "$FIRST" -l "$LAST" -r 110 -png "$PDF" "$DIR/binder-p"
find "$DIR" -name '*.png' -size +4M -print | while read -r f; do
  echo "warning: $f is over 4 MB; lower -r and re-run"
done

cd "$DIR/.."
git add plans
git commit -m "113 Bellefair: binder pages $FIRST-$LAST as PNG"
git push
echo "Pushed. Tell Claude: plans are in 113-bellefair/plans"
