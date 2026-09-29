#!/usr/bin/env bash
# One-time setup on the computer that runs Blender (macOS or Linux).
#   1. Python venv with the `mcp` package   -> blender-bridge/.venv
#   2. Blender add-on installed + enabled   (needs Blender closed)
#   3. MCP server registered with Claude Code as "blender"
# Safe to re-run. Override Blender's path with: BLENDER=/path/to/blender ./setup.sh
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

echo "1/3 Python + mcp"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    PY="$(command -v "$c")"; break
  fi
done
if [ -z "$PY" ]; then
  echo "  Need Python 3.10+. On a Mac: brew install python   (then re-run this script)"; exit 1
fi
[ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q mcp
(cd "$DIR" && "$VENV/bin/python" -c 'import mcp_server')
ok "mcp installed in $VENV"

echo "2/3 Blender add-on"
BLENDER="${BLENDER:-}"
if [ -z "$BLENDER" ]; then
  for c in /Applications/Blender.app/Contents/MacOS/Blender "$HOME/Applications/Blender.app/Contents/MacOS/Blender" "$(command -v blender || true)"; do
    [ -n "$c" ] && [ -x "$c" ] && { BLENDER="$c"; break; }
  done
fi
if [ -n "$BLENDER" ]; then
  "$BLENDER" --background --python-expr "
import bpy, addon_utils
bpy.ops.preferences.addon_install(filepath=r'$DIR/addon/claude_bridge.py', overwrite=True)
bpy.ops.preferences.addon_enable(module='claude_bridge')
bpy.ops.wm.save_userpref()
assert addon_utils.check('claude_bridge')[1], 'add-on did not enable'
" >/dev/null 2>&1 && ok "add-on installed + enabled ($BLENDER)" \
    || warn "auto-install failed — install addon/claude_bridge.py by hand (see README)"
else
  warn "Blender not found — install addon/claude_bridge.py by hand, or re-run with BLENDER=/path/to/blender"
fi

echo "3/3 Claude Code"
if command -v claude >/dev/null; then
  claude mcp remove blender --scope user >/dev/null 2>&1 || true
  claude mcp add --scope user blender -- "$VENV/bin/python" "$DIR/mcp_server.py" >/dev/null
  ok "registered MCP server 'blender' (all projects)"
else
  warn "claude CLI not found. Install Claude Code, then run:"
  echo "      claude mcp add --scope user blender -- \"$VENV/bin/python\" \"$DIR/mcp_server.py\""
fi

cat <<EOF

Done. Each time you want Claude in Blender:
  1. Open Blender → press N in the 3D viewport → Claude tab → Start Claude Bridge
  2. In Terminal:  claude remote-control      (or just: claude)
  3. Say: "ping Blender", then try: "run $DIR/examples/stud_wall.py in Blender"
EOF
