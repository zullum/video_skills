#!/usr/bin/env bash
# Split takes into vocals + instrumental (demucs htdemucs) and transcribe the vocal stem with the user's whisper.cpp.
#
#   stems.sh <project-dir> <take> [take ...]      e.g. stems.sh videos/my-video seed11 seed23
#
# Writes <project>/audio/stems/htdemucs/<take>/{vocals.wav,no_vocals.wav,vocals16k.wav,whisper.json,transcript.json}
# Transcribe the VOCAL STEM, never the full mix: the music drowns the words and misranks takes.
# The language is forced from song.json "language" (auto-detect heard "Music Outro" in a sung Take).
set -u
SKILL_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
P="$(cd "${1:?usage: stems.sh <project-dir> <take> [take ...]}" && pwd)"
shift
[ $# -gt 0 ] || { echo "name at least one take (e.g. seed11)" >&2; exit 2; }
ACE="${MOTION_STUDIO_ACESTEP:-}"
[ -z "$ACE" ] && [ -f "$SKILL_DIR/.acestep" ] && ACE="$(cat "$SKILL_DIR/.acestep")"
[ -n "$ACE" ] && [ -f "$ACE/pyproject.toml" ] || { echo "ACE-Step not found: bash \"$SKILL_DIR/scripts/check.sh\"" >&2; exit 2; }
WHISPER="$HOME/myprojects/whisper.cpp"
[ -x "$WHISPER/build/bin/whisper-cli" ] || { echo "whisper-cli not found: bash \"$SKILL_DIR/scripts/check.sh\"" >&2; exit 2; }
lang="$("$SKILL_DIR/scripts/py" -c 'import json, sys; print(json.load(open(sys.argv[1])).get("language", "en"))' "$P/audio/song.json" 2>/dev/null || echo en)"

for take in "$@"; do
  take="${take%.wav}"
  src="$P/audio/takes/$take.wav"
  out="$P/audio/stems/htdemucs/$take"
  [ -f "$src" ] || { echo "missing $src" >&2; continue; }
  if [ ! -f "$out/vocals.wav" ]; then
    echo "[$(date +%T)] demucs $take"
    (cd "$ACE" && uv run python -m demucs --two-stems vocals -n htdemucs -d cpu -o "$P/audio/stems" "$src") > "$P/audio/stems.log" 2>&1 \
      || { echo "demucs failed for $take (see $P/audio/stems.log)" >&2; continue; }
  fi
  ffmpeg -loglevel error -y -i "$out/vocals.wav" -ac 1 -ar 16000 "$out/vocals16k.wav"
  if [ ! -f "$out/transcript.json" ]; then
    echo "[$(date +%T)] transcribe $take (vocal stem, -l $lang)"
    # DTW needs -nfa (flash attention silently turns it off). No lyric --prompt: on singing it echoes unsung lines.
    { "$WHISPER/build/bin/whisper-cli" -m "$WHISPER/models/ggml-large-v3-turbo.bin" -l "$lang" -nfa --dtw large.v3.turbo \
        -sns -ojf -of "$out/whisper" "$out/vocals16k.wav" \
      && "$SKILL_DIR/scripts/py" "$SKILL_DIR/scripts/music/whisper_to_transcript.py" "$out/whisper.json" "$out/transcript.json" --lag 0.3; } \
      > "$out/transcribe.log" 2>&1 || echo "transcription failed for $take (see $out/transcribe.log)" >&2
  fi
  echo "  $take -> $out"
done
