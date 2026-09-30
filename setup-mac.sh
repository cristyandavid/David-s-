#!/usr/bin/env bash
# One command to get this Mac ready for Blender + Claude + Unity AR.
#   ./setup-mac.sh
# Installs what it can with Homebrew (Python, Blender, Unity Hub), sets up the
# Blender bridge, and checks Xcode / Unity / Claude Code. Safe to re-run.
set -o pipefail  # no -u: macOS bash 3.2 treats an empty array as unset

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODO=()
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
todo() { printf '  \033[33m→\033[0m %s\n' "$1"; TODO+=("$1"); }
have() { command -v "$1" >/dev/null 2>&1; }
cask() {  # cask <name> <app path> <label>
  if [ -d "$2" ]; then ok "$3 installed"
  elif have brew; then echo "  installing $3..."; brew install --cask "$1" >/dev/null && ok "$3 installed" || todo "Install $3 (brew install --cask $1 failed)"
  else todo "Install $3"; fi
}

[ "$(uname)" = Darwin ] || echo "Note: this script is written for macOS; continuing anyway."

echo "1/5 Homebrew + Python"
if have brew; then ok "Homebrew"; else
  todo 'Install Homebrew (see https://brew.sh), then re-run ./setup-mac.sh'
fi
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
  if have brew; then brew install python >/dev/null && ok "Python installed"; else todo "Install Python 3.10+"; fi
else ok "Python $(python3 -c 'import platform; print(platform.python_version())')"; fi

echo "2/5 Apps"
cask blender   /Applications/Blender.app      "Blender"
cask unity-hub "/Applications/Unity Hub.app"  "Unity Hub"
if [ -d /Applications/Xcode.app ]; then ok "Xcode"; else
  todo "Install Xcode from the App Store (needed to put the app on your iPad/iPhone), open it once to accept the licence"
fi

echo "3/5 Claude Code"
if have claude; then ok "Claude Code $(claude --version 2>/dev/null | head -1)"; else
  todo "Install Claude Code (https://code.claude.com/docs), then re-run ./setup-mac.sh to connect Blender"
fi

echo "4/5 Blender bridge"
"$ROOT/blender-bridge/setup.sh" 2>&1 | grep -E '✓|!|^ *(Need|claude mcp)' | sed 's/^/  /'
[ -f "$ROOT/blender-bridge/.venv/bin/python" ] || todo "Blender bridge setup didn't finish; run blender-bridge/setup.sh to see why"

echo "5/5 Unity editor"
EDITORS=$(ls -d /Applications/Unity/Hub/Editor/*/ 2>/dev/null | xargs -n1 basename 2>/dev/null | sort)
if [ -n "$EDITORS" ]; then
  ok "Unity editor(s): $(echo $EDITORS)"
  for v in $EDITORS; do
    [ -d "/Applications/Unity/Hub/Editor/$v/PlaybackEngines/iOSSupport" ] && IOS=1
  done
  [ "${IOS:-}" = 1 ] && ok "iOS Build Support" || todo "Unity Hub → Installs → ⚙ on your editor → Add Modules → iOS Build Support"
else
  todo "Unity Hub → sign in → Installs → Install Editor → Unity 6 LTS, tick iOS Build Support"
fi

echo
if [ ${#TODO[@]} -eq 0 ]; then
  echo "Everything's installed."
else
  echo "Still to do by hand (then re-run ./setup-mac.sh):"
  for t in "${TODO[@]}"; do echo "  - $t"; done
fi
cat <<EOF

Then:
  Blender + Claude  Open Blender → N → Claude tab → Start Claude Bridge
                    Terminal: claude remote-control   →  "ping Blender"
  Unity AR          Unity Hub → Add → Add project from disk →
                    $ROOT/unity/SiteXR-Project
                    First open installs AR packages and builds the scene by itself
                    (watch the Console). Then File → Build And Run.
  Full guide        $ROOT/HOME-SETUP.md
EOF
