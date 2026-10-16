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
# The asset stage calls GPT Image 2.5 on fal.ai (FAL_AI_API_KEY); PROVIDER=gemini-web needs Playwright and the Chrome
# of gemini_chrome.sh on CDP 9003, PROVIDER=api a Gemini key. Without any it can't run; code-only scenes still work.
if [ -n "${FAL_AI_API_KEY:-}${FAL_KEY:-}" ]; then echo "  ok    fal.ai key (images, the default)"
else echo "  note  no FAL_AI_API_KEY in the environment: export FAL_AI_API_KEY=... in ~/.zshrc (the image provider)"; fi
node -e 'const p=require("path"),os=require("os");for(const t of ["playwright",p.join(process.execPath,"../../lib/node_modules/playwright"),p.join(os.homedir(),".claude/skills/playwright-skill/node_modules/playwright")]){try{require(t);process.exit(0)}catch{}}process.exit(1)' 2>/dev/null \
  && echo "  ok    Playwright for Node (PROVIDER=gemini-web)" || echo "  note  no Playwright for Node: npm i -g playwright (only for PROVIDER=gemini-web)"
curl -s --max-time 2 http://127.0.0.1:9003/json/version >/dev/null \
  && echo "  ok    Gemini Chrome on CDP 9003 (PROVIDER=gemini-web)" || echo "  note  no Chrome on 9003 (only for PROVIDER=gemini-web): bash $SKILL/scripts/gemini_chrome.sh, log in once"
if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then echo "  ok    Gemini API key (PROVIDER=api)"
else echo "  note  no GEMINI_API_KEY: only needed for PROVIDER=api"; fi
[ $ok = 1 ] && echo "all good" || { echo "fix the MISS lines"; exit 1; }
