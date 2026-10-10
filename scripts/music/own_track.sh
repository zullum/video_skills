#!/usr/bin/env bash
# Use the user's own music file (WAV/MP3/...) as the Track: no Takes, no ranking, no Checkpoint 2.
#
#   own_track.sh <project-dir> <music-file> <video-seconds>
#
# Writes <project>/audio/takes/own.wav, then stems.sh / timing.py --take own --end <video-seconds> / trim.sh as usual.
# Exit 3 = a hard fail only the user can fix: the file is shorter than the video. Say so and wait for a new file.
# A longer file is a soft flag (report it at delivery): trim.sh cuts it to the video length with a fade.
set -u
P="$(cd "${1:?usage: own_track.sh <project-dir> <music-file> <video-seconds>}" && pwd)"
src="${2:?music file}"
want="${3:?video seconds}"
[ -f "$src" ] || { echo "missing $src" >&2; exit 2; }
mkdir -p "$P/audio/takes"
ffmpeg -loglevel error -y -i "$src" -vn -ar 48000 -ac 2 -c:a pcm_s16le "$P/audio/takes/own.wav" \
  || { echo "ffmpeg could not read $src" >&2; exit 2; }
have="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$P/audio/takes/own.wav")"
if awk -v h="$have" -v w="$want" 'BEGIN { exit !(h < w) }'; then
  rm -f "$P/audio/takes/own.wav"
  echo "STOP: the Track is ${have} s long but the video needs ${want} s. Ask the user for a longer file." >&2
  exit 3
fi
echo "$P/audio/takes/own.wav: ${have} s (video ${want} s)"
if awk -v h="$have" -v w="$want" 'BEGIN { exit !(h > w + 1) }'; then
  echo "soft flag: the Track is longer than the video; trim it: trim.sh audio/takes/own.wav $want assets/audio/song.wav 2"
fi
