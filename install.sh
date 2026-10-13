#!/usr/bin/env bash
# Install the skills in this repo for Claude Code, OpenAI Codex and/or Google Antigravity.
#
#   bash install.sh [claude|codex|antigravity|all] [--project DIR] [--link] [--deps]
#
#   default target   all
#   --project DIR    install into a project instead of your home folder
#                    (DIR/.claude/skills, DIR/.agents/skills, DIR/.agent/skills)
#   --link           symlink instead of copy, so `git pull` updates the installed skill
#   --deps           also install the Python packages (pip) and Playwright Chromium (npx)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="all"; PROJECT=""; LINK=0; DEPS=0
while [ $# -gt 0 ]; do
  case "$1" in
    claude|codex|antigravity|all) TARGET="$1" ;;
    --project) PROJECT="$2"; shift ;;
    --link) LINK=1 ;;
    --deps) DEPS=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
  shift
done

dest_for() {   # $1 = tool
  if [ -n "$PROJECT" ]; then
    case "$1" in claude) echo "$PROJECT/.claude/skills" ;; codex) echo "$PROJECT/.agents/skills" ;;
                 antigravity) echo "$PROJECT/.agent/skills" ;; esac
  else
    case "$1" in claude) echo "$HOME/.claude/skills" ;; codex) echo "$HOME/.agents/skills" ;;
                 antigravity) echo "$HOME/.gemini/antigravity/skills" ;; esac
  fi
}

install_for() {  # $1 = tool
  local dest; dest="$(dest_for "$1")"; mkdir -p "$dest"
  for skill in "$HERE"/skills/*/; do
    local name; name="$(basename "$skill")"
    rm -rf "${dest:?}/$name"
    if [ "$LINK" = 1 ]; then ln -s "${skill%/}" "$dest/$name"; else cp -R "${skill%/}" "$dest/$name"; fi
    echo "  $1: $dest/$name"
  done
}

echo "Installing skills:"
case "$TARGET" in
  all) for t in claude codex antigravity; do install_for "$t"; done ;;
  *) install_for "$TARGET" ;;
esac

if [ "$DEPS" = 1 ]; then
  echo "Installing dependencies..."
  python3 -m pip install -r "$HERE/requirements.txt"
  (cd "$HERE" && npm i --no-save playwright && npx playwright install chromium)
fi
echo "Done. Restart the agent (or open a new session) so it picks up the skill."
