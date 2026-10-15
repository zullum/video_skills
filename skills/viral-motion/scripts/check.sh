#!/usr/bin/env bash
# viral-motion check: verifies the local toolchain on this Mac. Installs nothing; prints the fix for anything missing.
#
#   check.sh
#
# Everything is free and local. No Gemini, ever: the API keys must be blank.
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WHISPER="$HOME/myprojects/whisper.cpp"
KOKORO="$HOME/.cache/hyperframes/tts"
problems=0
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; problems=$((problems + 1)); }
note() { printf '    fix: %s\n' "$1"; }

echo "viral-motion check  ($SKILL_DIR)"

# ---------------------------------------------------------------- render
if command -v node >/dev/null 2>&1 && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ]; then
  ok "Node.js $(node -v)"
else
  bad "Node.js 22+ not found"; note "brew install node"
fi
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')"
else
  bad "ffmpeg not found"; note "brew install ffmpeg"
fi
if v="$("$SKILL_DIR/scripts/hf" --version 2>/dev/null | tail -1)" && [ -n "$v" ]; then
  ok "HyperFrames CLI $v (through scripts/hf)"
  chrome="$("$SKILL_DIR/scripts/hf" browser path 2>/dev/null | tail -1)"
  if [ -x "$chrome" ]; then ok "headless Chrome for rendering"; else bad "headless Chrome not found"; note "$SKILL_DIR/scripts/hf browser ensure"; fi
else
  bad "HyperFrames CLI not found"; note "npm install -g hyperframes"
fi

# ---------------------------------------------------------------- music
ACE="$(cat "$SKILL_DIR/.acestep" 2>/dev/null)"
if [ -n "$ACE" ] && [ -f "$ACE/pyproject.toml" ]; then
  ok "ACE-Step checkout: $ACE"
  has() { [ -n "$(find "$ACE/checkpoints/$1" -maxdepth 1 \( -name '*.safetensors' -o -name '*.bin' \) 2>/dev/null | head -1)" ]; }
  for m in acestep-v15-turbo vae Qwen3-Embedding-0.6B acestep-5Hz-lm-0.6B; do
    if has "$m"; then ok "checkpoint $m"; else bad "checkpoint $m missing"; note "cd \"$ACE\" && uv run acestep-download --model $m"; fi
  done
  if grep -q ACESTEP_MPS_DTYPE "$ACE/acestep/core/generation/handler/init_service_orchestrator.py" 2>/dev/null; then
    ok "bf16 memory patch"
  else
    bad "bf16 memory patch not applied"; note "cd \"$ACE\" && git apply \"$SKILL_DIR/scripts/music/acestep-mps-bf16.patch\""
  fi
  if "$ACE/.venv/bin/python" -c "import demucs" >/dev/null 2>&1; then
    ok "demucs (vocal / instrumental stems)"
  else
    bad "demucs not in ACE-Step's venv"; note "cd \"$ACE\" && uv pip install demucs"
  fi
else
  bad "ACE-Step not found (SKILL/.acestep)"; note "echo ~/myprojects/musicmodel/ACE-Step-1.5 > \"$SKILL_DIR/.acestep\""
fi

# ---------------------------------------------------------------- word timing
if [ -x "$WHISPER/build/bin/whisper-cli" ]; then
  ok "whisper-cli ($WHISPER/build/bin)"
else
  bad "whisper-cli not found in $WHISPER/build/bin"; note "cd \"$WHISPER\" && cmake -B build && cmake --build build -j --config Release"
fi
for m in large-v3-turbo large-v3; do
  if [ -f "$WHISPER/models/ggml-$m.bin" ]; then ok "whisper model $m"; else bad "whisper model $m missing"; note "cd \"$WHISPER\" && ./models/download-ggml-model.sh $m"; fi
done

# ---------------------------------------------------------------- voice + Python
VPY="$SKILL_DIR/.venv/bin/python"
if "$VPY" -c 'import sys, numpy, soundfile, kokoro_onnx; assert sys.version_info[:2] == (3, 12)' >/dev/null 2>&1; then
  ok "skill venv: Python 3.12 with numpy, soundfile, kokoro-onnx"
else
  bad "skill venv missing or incomplete ($SKILL_DIR/.venv)"
  note "uv venv --python 3.12 \"$SKILL_DIR/.venv\" && uv pip install --python \"$VPY\" numpy soundfile kokoro-onnx"
fi
if [ -f "$KOKORO/models/kokoro-v1.0.onnx" ] && [ -f "$KOKORO/voices/voices-v1.0.bin" ]; then
  ok "Kokoro model and voices"
else
  bad "Kokoro model or voices missing ($KOKORO)"; note "HYPERFRAMES_PYTHON=\"$VPY\" \"$SKILL_DIR/scripts/hf\" tts \"test\" -o /tmp/kokoro-test.wav"
fi

# ---------------------------------------------------------------- no Gemini
if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${GOOGLE_API_KEY:-}" ]; then
  ok "Gemini keys are blank"
else
  bad "GEMINI_API_KEY or GOOGLE_API_KEY is set"; note "run sessions from ~/myprojects/musicmodel (its .claude/settings.json blanks them)"
fi

echo
if [ "$problems" -eq 0 ]; then
  echo "All set."
else
  echo "$problems thing(s) to fix above, then run this again."
  exit 1
fi
