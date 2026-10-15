# mascot-explainer: design

Date: 2026-10-15 · Branch: `add-mascot-explainer` · Status: sections 1-2 approved in chat, 3-6 for review

## Goal

A skill that makes a whole narrated mascot explainer video from code, in the style of the analysed
reference (an 8:25 calisthenics explainer: flat vector cartoon, thick black ink, one mascot, a 4-5 shade
palette, "planet bubbles", zoom-through transitions, text slams, short frame-by-frame exercise loops).
Generic: any topic, any character and palette given in a style bible. Proven by a ~50 s demo with our own
mascot. Character motion comes from ONE Nano Banana image holding up to 24 frames, traced to SVG and
rendered at 4K.

**Decided with the user:** generic skill + 45-60 s demo (not a full 8 min remake); a configurable
character, the demo uses our own mascot (coral-orange figure, navy shorts, white wristbands, deep-teal
"space" palette), never the reference channel's mascot or brand; full audio (narration, music, SFX);
HyperFrames assembles; approach A (asset pipeline + scene template library).

## Reference video findings (what the skill must reproduce)

- 1920×1080, 30 fps, ~1,260 narrated words, music bed, SFX on pops and swooshes.
- Mostly **still illustrations moved by motion graphics**: pop-ins, floats, camera push-ins, zoom-through
  matches, whip blurs. Per-second motion energy is near zero on many holds and spikes on transitions.
- **Frame-by-frame animation only where the body moves**: push-up reps (3-4 key frames with holds),
  incline push-up, rows, squats, gestures. Inset circles pop around the figure while it loops.
- Shots last 2-5 s, cut on narration line boundaries; inner beats land on key words.
- A full shot-by-shot breakdown goes into `references/reference-video.md` (text only: no frames from
  the reference video are committed to this public repo).

## 1. Architecture (approved)

Five stages: script → storyboard (`shots.json`) → assets (Nano Banana → SVG) → narration + timing →
build (HyperFrames composition from the scene library) → mix, QA, 4K render.

```
skills/mascot-explainer/
  SKILL.md                workflow (≤200 lines)
  references/  scene-catalog.md  reference-video.md  style-bible.md  asset-prompts.md
               storyboard.md  critique.md
  scripts/     check.sh  setup_venv.sh  asset_sheet.py  timing.py  build.py  selftest.sh
  lib/         toon-core.js  toon-sprite.js  scenes/*.js      (copied into each project)
  examples/demo/  script.md  style.json  shots.json
```

- **Reuse, no copies.** `sprite-video`: gen.py, template.py, slice.py, trace2.py, muscles.py.
  `viral-motion`: scripts/hf, Kokoro TTS (`hf tts` in its venv), sfx_lib/build_sfx, duck_lane,
  mix_check, the Critic. A dependency resolves to the sibling folder (`SKILL/../<name>`) first, then
  `~/.claude/skills/<name>`; `check.sh` names anything missing.
- **Gemini only in the asset stage**, through sprite-video's gen.py. HyperFrames always runs through
  viral-motion's `hf`, which strips the keys (no frame is ever sent to Gemini).
- Own venv for tracing (numpy scipy pillow vtracer potracer): Homebrew Python 3.14 lacks them.
- Every file ≤200 lines (user rule), generated project files excepted.

## 2. Asset pipeline (approved)

Code draws everything geometric ($0): backgrounds, sparkles, planet bubbles, window room + grid, day
columns, text, tags, arrows, callout circles, stairs, rays, lightning, flashes, phone frame, thumbnail
cards, book pages. Nano Banana draws only organic things (character poses, hands, props, silhouettes).

1. `style.json`: palette with roles (`bgDeep bgMid bgLight panel ink skin shorts sleeve accent text`),
   chroma key colour (not in the palette, green by default), font, ink weight, character description.
2. Character sheet, 1 call at 2K: turnaround (front, ¾, side) + 3 expressions on the chroma colour.
   It is the reference image of every later call.
3. Pose sheet(s), 1 call per 6 poses (3×2). Prop sheet, 1 call (3×3).
4. Sprite sheets by the sprite-video method (base pre-drawn in every cell + red guides): 6×4 = 24
   frames for limb motion, 3×3 / 4×2 for whole-body motion.
5. `asset_sheet.py`: slice a sheet, key out the chroma colour, trace each asset with trace2, write
   `assets/svg/<name>.svg` + `assets/manifest.json` (size, anchor: feet or centre).
6. Cache: generated images are kept and reused; each call prints its price. Demo budget ≤ $1.50.

## 3. Scene catalog (lib/scenes, one file each)

Each template is `TOON.scene.<name>(host, params, tl)`: it builds SVG/DOM in `host` and adds tweens to
the scene's paused GSAP timeline. Seek-safe: a seeded random, no wall clock, no CSS animations.

| template | reproduces | key params |
|---|---|---|
| `space` | deep backdrop, twinkling 4-point sparkles, slow drift (base layer) | tone, density |
| `bubbles` | exercise/topic "planets": crater or stripe texture, white rim; pop-in, bob, highlight rays, dim others, crowd of many | items[{asset or sprite, x,y,r,texture}], layout, highlight |
| `zoomThrough` | camera dives into a bubble, its content becomes the next shot (transition) | target, dur |
| `windowRoom` | spaceship window with grid glass, floor panels; content floats behind glass; over-shoulder figure in front | content, fg, camera |
| `days` | MON/WED/FRI columns: lines wipe in, labels slide, content cloned per column | labels, content |
| `textSlam` | bold italic uppercase headline, word punch or typewriter | text, mode, pos |
| `shelf` | study visual: objects build into a small vs big grid, split compare, citation tag | item, counts, citation |
| `crowd` | row of tinted silhouettes, "?" / "$" thought bubbles pop above heads | n, phases |
| `phone` | hand holding a phone, live screen (feed, app mock), icons flying around | screen, hand, icons |
| `cardWall` | collage of thumbnail cards flying in, figure seen from behind | cards, fg |
| `exerciseDemo` | sprite loop on the floor with a shadow, callout circle draws on, ROM arrow grows, "2×12 / 3/WEEK" tag | sprite, reps, callout, arrow, tag |
| `muscleInsets` | close-up circles pop around the looping figure | insets, sprite |
| `flyBy` | rocket / satellite along a path, exhaust flicker, motion blur, badge | asset, path, label |
| `stairs` | progression steps build, items on steps, figure on top | steps, items |
| `powerUp` | flame aura, lightning burst, radial rays, speed lines, pause icon | kind, target |
| `seqRows` | rows of bubble → arrow → bubble with set tags | rows |
| `document` | code-built book cover and page spreads sliding in | pages |

Transitions: `cut`, `zoomThrough`, `whip` (directional blur), `flash` (white cross flare), `pop`.
Motion rules (`toon-core.js`): pop-in scale 0→1.08→1 in 0.35 s with blur 6→0 px and 0.12 s stagger;
idle bob ±6 px over 3-4 s; slow camera push 2-4 % per shot; nothing stays fully still longer than 2 s.
`toon-sprite.js` plays an SVG frame sequence with sprite-video's `seq`/`rep` format by toggling
visibility on the timeline (deterministic on seek).

`references/scene-catalog.md` documents each template: what it looks like in the reference, how it is
built, timing, params, and which assets it needs. Unknown one-off scenes are hand-written in the same
style following the catalog's recipes (the approach B fallback).

## 4. Storyboard and build

- `shots.json`: `{style, fps: 30, size: [1920,1080], shots: [{id, say, scene, params, beats:
  [{at: "word:<w>" | seconds, do, args}], in: "cut|zoomThrough|whip|flash|pop"}]}`.
- `timing.py`: one Kokoro clip per `say` line (or the user's recording through viral-motion's
  recording pipeline) → `audio/voice.wav` + whisper word times → `timing.json` (shot start/end, words).
  Shot times always come from the narration; nothing is guessed.
- `build.py`: `shots.json` + `timing.json` + `manifest.json` → `index.html` (tracks, audio) and
  `compositions/<id>.html` (~20 lines each, calling one template), copies `lib/` into `assets/js/`, and
  writes `<id>.motion.json` (pops, whooshes, slams) for the SFX build.

## 5. Audio

Narration: English Kokoro by default, or the user's recording (any language). Music: an instrumental
bed from viral-motion's ACE-Step or the user's track, ducked -10 dB under the voice (duck_lane).
SFX synthesized from the motion events with sfx_lib: `ui_pop` (bubble), `whoosh` (zoom, whip, fly-by),
`shimmer` (highlight), `impact_low` (text slam), `tick` (tags), `riser` (before a reveal).
Gate: mix_check -14 LUFS ±1, true peak ≤ -1 dBTP.

## 6. QA, tests, demo

- `selftest.sh` ($0, no Gemini): a 6 s project of code-only scenes (space, bubbles with placeholder
  shapes, textSlam, days) → `hf check` 0 errors → render → length and audio check.
- Per video: `hf check` 0 errors; snapshots at every shot start/middle/end and beat; critique rounds by a
  fresh Critic agent with `references/critique.md` (palette fidelity, ink weight across assets, sprite
  shake and jumps, pop timing, text legibility, dead zones, A/V sync), max 3 rounds, every shot 8/10+.
- Demo: an original ~50 s English script on a topic of this genre (working title "Two sets are enough to
  start"), our coral mascot, covering ≥10 templates including bubbles, zoomThrough, windowRoom, days,
  textSlam, exerciseDemo with a 24-frame push-up sprite, muscleInsets, flyBy, powerUp, shelf or crowd.

**Success criteria**
1. `selftest.sh` passes on a clean checkout with the dependencies installed.
2. The demo renders at 3840×2160, 30 fps, ~50 s, with narration + music + SFX, mix within the gate.
3. Every demo shot grades 8/10+ in the final critique; Gemini spend ≤ $1.50.
4. `reference-video.md` covers every shot of the 8:25 reference with its template and technique.
5. All skill files ≤200 lines; README gets a row, setup notes and a preview GIF in `assets/`; the demo
   MP4 is delivered locally, not committed (`*.mp4` is gitignored).

## Out of scope

A full remake of the reference video; any copy of its mascot, brand, app or book; video generation
models; portrait format (landscape only for now, the templates take the size from `shots.json`).
