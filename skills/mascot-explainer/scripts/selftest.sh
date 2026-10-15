#!/usr/bin/env bash
# $0 self test, no Gemini: the unit tests, then a gallery video of every scene built from hand-made and synthetic
# assets, checked frame by frame with pixel probes (tests/gallery/probes.json).
#   selftest.sh [--only id,id] [--render]        SELFTEST_DIR=<empty dir> to choose where the project goes
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"; PY="$SKILL/scripts/py"; ONLY=""; RENDER=0
while [ $# -gt 0 ]; do
  case "$1" in --only) ONLY="$2"; shift ;; --render) RENDER=1 ;; *) echo "unknown argument: $1" >&2; exit 2 ;; esac
  shift
done
VM="$("$PY" "$SKILL/scripts/deps.py" vm)"; HF="$VM/scripts/hf"
"$PY" -m pytest "$SKILL/tests" -q
P="${SELFTEST_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/mx-selftest.XXXXXX")}"; mkdir -p "$P"
(cd "$P" && HYPERFRAMES_SKIP_SKILLS=1 "$HF" init proj --non-interactive --example=blank --resolution=landscape >/dev/null)
G="$P/proj"; cp -R "$SKILL/tests/gallery/." "$G/"
"$PY" "$SKILL/tests/make_fixtures.py" "$G" >/dev/null
"$PY" "$SKILL/scripts/build.py" "$G" --no-sfx ${ONLY:+--only "$ONLY"}
(cd "$G" && "$HF" check . >"$G/check.txt" 2>&1) || { tail -40 "$G/check.txt"; echo "hf check failed ($G)"; exit 1; }
T="$("$PY" "$SKILL/scripts/probe.py" times "$G" "$G/probes.json" ${ONLY:+--only "$ONLY"})"
(cd "$G" && "$HF" snapshot . --at "$T" --no-end -o snapshots >"$G/snap.txt" 2>&1) || { tail -20 "$G/snap.txt"; exit 1; }
"$PY" "$SKILL/scripts/probe.py" check "$G" "$G/probes.json" "$G/snapshots" ${ONLY:+--only "$ONLY"}
if [ "$RENDER" = 1 ]; then
  (cd "$G" && "$HF" render -q draft -o renders/gallery.mp4 --workers 2 >"$G/render.txt" 2>&1) || { tail -20 "$G/render.txt"; exit 1; }
  want="$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['duration'])" "$G/audio/sfx_cues.json")"
  got="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$G/renders/gallery.mp4")"
  "$PY" -c "import sys; w,g=map(float,sys.argv[1:]); sys.exit(0 if abs(w-g)<=0.1 else f'render is {g:.2f} s, expected {w:.2f} s')" "$want" "$got"
  echo "render ok: $got s"
fi
echo "selftest passed: $G"
