#!/usr/bin/env bash
# Start a viral-motion project: a HyperFrames project + the audio files for its level.
#
#   new_project.sh <project-dir> <level> [format]   level: 1 (showreel, no music) | 2 (lyric music video) | 3 (story film)
#                                                   format: portrait (default, 1080x1920) | landscape | square
#
# Level 2 gets audio/song.json (a song with vocals); level 3 gets audio/song.json in score mode (instrumental
# with a story arc); both get audio/sfx_cues.json. Fill them in, then follow SKILL.md.
set -eu
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
dir="${1:?usage: new_project.sh <project-dir> <1|2|3>}"
level="${2:?level 1, 2 or 3}"
case "$level" in 1|2|3) ;; *) echo "level must be 1, 2 or 3" >&2; exit 2 ;; esac
format="${3:-portrait}"
case "$format" in portrait|landscape|square) ;; *) echo "format must be portrait, landscape or square" >&2; exit 2 ;; esac
if [ -e "$dir/index.html" ]; then
  echo "$dir already has a project (index.html); not touching it" >&2
  exit 2
fi
parent="$(dirname "$dir")"
mkdir -p "$parent"
(cd "$parent" && HYPERFRAMES_SKIP_SKILLS=1 "$SKILL_DIR/scripts/hf" init "$(basename "$dir")" --non-interactive --example=blank --skill=general-video --resolution="$format" >/dev/null)
P="$(cd "$dir" && pwd)"
mkdir -p "$P/audio" "$P/renders"
if [ "$level" = 2 ]; then
  cp "$SKILL_DIR/templates/song.json" "$P/audio/song.json"
elif [ "$level" = 3 ]; then
  cp "$SKILL_DIR/templates/score.json" "$P/audio/song.json"
fi
[ "$level" = 1 ] || cp "$SKILL_DIR/templates/sfx_cues.json" "$P/audio/sfx_cues.json"
echo "project: $P (level $level, $format)"
case "$level" in
  1) echo "next: BRIEF.md, frame.md, STORYBOARD.md (Beat sheet) -> Checkpoint 1, then build (references/level-1-showreel.md)" ;;
  2) echo "next: Beat sheet + the song in audio/song.json -> Checkpoint 1, then: bash \"$SKILL_DIR/scripts/music/run_music.sh\" \"$P\"  (references/level-2-lyric-video.md)" ;;
  3) echo "next: Beat sheet + score caption in audio/song.json -> Checkpoint 1, then: bash \"$SKILL_DIR/scripts/music/run_music.sh\" \"$P\"  (references/level-3-story-film.md)" ;;
esac
