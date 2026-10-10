#!/bin/bash
# One whisper-cli run with the recommended flags; extra args are appended (later flags win).
# Usage: run_whisper.sh <turbo|v3> <in16k.wav> <out_prefix> [extra whisper-cli args...]
#        run_whisper.sh detect <in16k.wav>   (language ID only: prints "<code> <p>", e.g. "hr 0.99")
# Writes <out_prefix>.json (-ojf: ml1 word segments + per-token p and DTW t_dtw),
#        <out_prefix>.stderr.txt (incl. /usr/bin/time -l), and prints the wall time in seconds.
set -e
W="$HOME/myprojects/whisper.cpp"   # the user's own build and models (check.sh verifies them)
M=$W/models
if [ "$1" = detect ]; then
  "$W/build/bin/whisper-cli" -m "$M/ggml-large-v3-turbo.bin" -f "$2" -dl 2>&1 \
    | sed -n 's/.*auto-detected language: \([a-z]*\) (p = \([0-9.]*\)).*/\1 \2/p'
  exit 0
fi
case "$1" in
  turbo) MODEL=$M/ggml-large-v3-turbo.bin; DTW=large.v3.turbo ;;
  v3)    MODEL=$M/ggml-large-v3.bin;       DTW=large.v3 ;;
  *) echo "model must be turbo|v3" >&2; exit 2 ;;
esac
WAV=$2; OUT=$3; shift 3
# -nfa: DTW is silently disabled when flash attention is on (whisper.cpp src/whisper.cpp:3708).
/usr/bin/time -p -o "$OUT.time.txt" "$W/build/bin/whisper-cli" -m "$MODEL" -f "$WAV" \
  -l hr -ml 1 -sow -ojf -nfa --dtw "$DTW" -sns -np -of "$OUT" "$@" \
  > "$OUT.stdout.txt" 2> "$OUT.stderr.txt"
echo "$(awk '/^real/{print $2}' "$OUT.time.txt")"
