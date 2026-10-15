#!/usr/bin/env bash
# Checks what mascot-explainer needs and prints the fix for each missing piece. Installs nothing.
SKILL="$(cd "$(dirname "$0")/.." && pwd)"; ok=1
row() { if [ "$2" = 0 ]; then echo "  ok    $1"; else echo "  MISS  $1  ->  $3"; ok=0; fi; }
"$SKILL/.venv/bin/python" -c "import numpy,scipy,PIL,vtracer,potrace" 2>/dev/null; row "venv (py3.12 + tracers)" $? "bash $SKILL/scripts/setup_venv.sh"
SV=$("$SKILL/scripts/py" "$SKILL/scripts/deps.py" sv 2>/dev/null); row "sprite-video" $? "bash install.sh claude (video_skills repo)"
VM=$("$SKILL/scripts/py" "$SKILL/scripts/deps.py" vm 2>/dev/null); row "viral-motion + venv" $? "install viral-motion, run its scripts/check.sh"
[ -n "$VM" ] && "$VM/.venv/bin/python" -c "import kokoro_onnx" 2>/dev/null; row "Kokoro voice" $? "bash $VM/scripts/check.sh"
command -v ffmpeg >/dev/null; row "ffmpeg" $? "brew install ffmpeg"
node -e 'process.exit(Number(process.versions.node.split(".")[0]) < 18 ? 1 : 0)' 2>/dev/null; row "node 18+" $? "brew install node"
test -f "$HOME/myprojects/whisper.cpp/models/ggml-large-v3-turbo.bin"; row "whisper large-v3-turbo" $? "see viral-motion README"
[ -n "$VM" ] && "$VM/scripts/hf" --version >/dev/null 2>&1; row "HyperFrames CLI" $? "npm i -g hyperframes"
if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then echo "  ok    Gemini key (asset stage)"
else echo "  note  no GEMINI_API_KEY: the asset stage can't run; code-only scenes still work"; fi
[ $ok = 1 ] && echo "all good" || { echo "fix the MISS lines"; exit 1; }
