#!/bin/bash
# Recording -> recording.json, end to end, with wall-clock per step.
# Usage: pipeline.sh <recording.m4a|mp3|wav|aiff> <approved_script.txt> <outdir> [hr|en] [turbo|v3]
#   script: one script line per text line (as approved at Checkpoint 1).
#   hr = any Bosnian/Croatian/Serbian Latin speech (bs/sr behave worse).
# Exit 3 = hard fail: the Recording is in another language than the script, or under 70% of the script
#          is heard clearly (different text, music, garbage).
set -e
D=$(cd "$(dirname "$0")" && pwd)
PY="$D/../py"
IN=$1; SCRIPT=$2; OUT=$3; LANG_=${4:-hr}; MOD=${5:-turbo}
mkdir -p "$OUT"
ts() { python3 -c 'import time; print(time.time())'; }
lap() { python3 -c "print(f'{$(ts) - $1:6.2f}s  $2')"; }

t=$(ts); "$PY" "$D/prep_recording.py" "$IN" "$OUT" > "$OUT/prep.log"; lap $t "intake + cleanup (prep_recording.py)"
t=$(ts); read -r DET DET_P <<< "$("$D/run_whisper.sh" detect "$OUT/whisper16k.wav")"; lap $t "language check (heard ${DET:-?} ${DET_P:-})"
PROMPT="$(tr '\n' ' ' < "$SCRIPT")"
t=$(ts); "$D/run_whisper.sh" "$MOD" "$OUT/whisper16k.wav" "$OUT/whisper" -l "$LANG_" --prompt "$PROMPT" \
  --carry-initial-prompt > /dev/null; lap $t "whisper-cli $MOD (-ml 1 -sow -ojf -nfa --dtw, script prompt)"
rc=0
t=$(ts); "$PY" "$D/align_script.py" --script "$SCRIPT" --whisper "$OUT/whisper.json" --prep "$OUT/prep.json" \
  --out "$OUT/recording.json" --lang "$LANG_" --detected "${DET:-}" --detected-p "${DET_P:-0}" \
  > "$OUT/align.log" || rc=$?; lap $t "align + snap + shots (align_script.py)"
cat "$OUT/align.log"
exit $rc
