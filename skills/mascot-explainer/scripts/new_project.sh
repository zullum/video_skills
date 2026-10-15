#!/usr/bin/env bash
# Start a mascot-explainer project: a landscape HyperFrames project plus style.json, an empty shots.json and the
# Gemini budget ledger.   new_project.sh <project-dir> [style.json]   (default style: examples/demo/style.json)
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
dir="${1:?usage: new_project.sh <project-dir> [style.json]}"
[ -e "$dir/index.html" ] && { echo "$dir already has a project (index.html); not touching it" >&2; exit 2; }
VM="$("$SKILL/scripts/py" "$SKILL/scripts/deps.py" vm)"
mkdir -p "$(dirname "$dir")"
(cd "$(dirname "$dir")" && HYPERFRAMES_SKIP_SKILLS=1 "$VM/scripts/hf" init "$(basename "$dir")" --non-interactive --example=blank --resolution=landscape >/dev/null)
P="$(cd "$dir" && pwd)"
mkdir -p "$P/gen" "$P/audio" "$P/renders"
cp "${2:-$SKILL/examples/demo/style.json}" "$P/style.json"
[ -f "$P/shots.json" ] || printf '{"style": "style.json", "voice": "af_heart", "speed": 1.0, "shots": []}\n' > "$P/shots.json"
[ -f "$P/gen/budget.json" ] || printf '{"limit": 1.5, "spent": 0.0, "calls": []}\n' > "$P/gen/budget.json"
echo "project: $P"
echo "next: style.json (palette, character), shots.json (script + scenes), then the checkpoint in SKILL.md"
