# mascot-explainer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A skill (`skills/mascot-explainer/`) that turns a narration script into a 4K narrated mascot explainer
video in the reference style, proven by a ~50 s demo with our own coral mascot.

**Architecture:** Code draws everything geometric (HyperFrames HTML + inline SVG + GSAP); Nano Banana draws only
the character, hands and props, traced to SVG; body motion comes from sprite sheets (≤24 frames per image) traced
to SVG frames. A `shots.json` storyboard is the single source of timing: Python resolves every beat time (from
Kokoro + whisper word times), writes the HyperFrames project, and derives the SFX cues from the same beats. Scene
templates are JS modules of *actions* (`pop`, `highlight`, `zoom`, …) that only execute resolved beats.

**Tech Stack:** HyperFrames 0.8.141 (`viral-motion/scripts/hf`), GSAP 3.14.2 (CDN), Python 3.12 venv via `uv`
(numpy scipy pillow vtracer potracer pytest), sprite-video scripts (gen/template/slice/trace2), viral-motion
scripts (Kokoro `hf tts`, whisper `run_whisper.sh`, `build_sfx.py`, `duck_lane.py`, `mix_check.py`,
`av_check.py`, ACE-Step `run_music.sh`), ffmpeg, Barlow / Barlow Condensed fonts (OFL).

**Spec:** `docs/superpowers/specs/2026-10-15-mascot-explainer-design.md`

## Plan files (execute in order)

| file | tasks |
|---|---|
| `01-foundation.md` | 1 skill skeleton, venv, dependency lookup, check · 2 sprite-video `--clip` |
| `02-assets.md` | 3 budgeted Gemini wrapper · 4 asset_sheet.py · 5 sprite_import.py |
| `03-timing-build.md` | 6 beats + whisper parsing · 7 timing.py · 8 build.py (html + audio) |
| `04-runtime.md` | 9 toon-core.js + toon-shapes.js · 10 toon-sprite.js · 11 probe harness, selftest, `space` scene |
| `05-scenes-1.md` | 12 bubbles (+ zoomThrough) · 13 textSlam · 14 days · 15 windowRoom |
| `06-scenes-2.md` | 16 exerciseDemo (+ muscleInsets) · 17 flyBy · 18 powerUp · 19 shelf |
| `07-scenes-3.md` | 20 crowd · 21 phone · 22 cardWall · 23 stairs · 24 seqRows · 25 document |
| `08-docs.md` | 26 reference-video breakdown · 27 references · 28 SKILL.md, README, install |
| `09-demo.md` | 29 style + character + asset sheets · 30 sprites · 31 script → build · 32 audio, critique, 4K · 33 wrap-up |

## Global Constraints

- Every file in `skills/mascot-explainer/` ≤ 200 lines (user rule); generated project files are exempt.
- Python runs only through `skills/mascot-explainer/scripts/py` (its `.venv`, Python 3.12 via `uv`).
- HyperFrames runs only through `<viral-motion>/scripts/hf` (strips GEMINI/GOOGLE keys, `--describe false`).
- Gemini is called only by `scripts/gen_asset.py` (asset stage), never by HyperFrames, TTS, music or critique.
- Image model `gemini-3.1-flash-image`; prices 1K $0.067, 2K $0.101, 4K $0.151 per image. Demo budget ≤ $1.50.
- Never print or write `GEMINI_API_KEY`.
- No frame, still or audio of the reference video is committed; references describe it in text only.
- The demo uses our own mascot (coral-orange skin, navy shorts, white wristbands) and a deep-teal palette; never
  the reference channel's mascot, brand, app or book names.
- Landscape 1920×1080 composition, 30 fps; final render `--resolution landscape-4k` (3840×2160).
- Mix gate: −14 LUFS ±1, true peak ≤ −1 dBTP (`mix_check.py`).
- Commits: `git -c user.name=Sanel -c user.email=zullumsan@gmail.com commit …` ending with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `add-mascot-explainer`. No push without asking.
- `*.mp4` stays uncommitted (repo `.gitignore`); `.venv/` and `__pycache__/` ignored by the skill's `.gitignore`.

## Interfaces every task shares

- **Skill paths:** `SKILL=skills/mascot-explainer`. `deps.py` resolves `SV` (sprite-video: has `scripts/trace2.py`)
  and `VM` (viral-motion: has `.venv/bin/python`) as the sibling folder first, then `~/.claude/skills/<name>`.
- **Project layout** (one video): `style.json`, `shots.json`, `index.html`, `compositions/<id>.html`,
  `compositions/<id>.motion.json`, `assets/js/` (lib copy), `assets/fonts/`, `assets/svg/`, `assets/sprites/<n>/`,
  `assets/manifest.json`, `assets/audio/{narration/<id>.wav,music.wav,sfx.wav}`, `audio/timing.json`,
  `audio/sfx_cues.json`, `gen/` (raw Gemini PNGs + `budget.json`), `renders/`, `snapshots/`.
- **manifest.json:** `{"assets": {name: {"file", "w", "h", "anchor": [ax, ay], "holes": [[x,y,w,h], …]}},
  "sprites": {name: {"dir", "cell": [w,h], "floor": [y0,y1]|null, "frames": [{"file","x","y","w","h"}]}}}`
  (`holes` in fractions of w/h; sprite coordinates in cell pixels).
- **shots.json:** `{"style": "style.json", "voice": "af_heart", "speed": 1.0, "shots": [{"id", "say"?, "dur"?,
  "hold"?, "scene", "params", "beats": [{"at", "do", "args"}], "in"?}]}`; `at` = seconds | `"word:<w>"` |
  `"word:<w>#2"` | `"word:<w>+0.2"` | `"end-0.6"`; `in` ∈ `cut` (default), `pop`, `zoomIn`, `whip`, `flash`.
- **timing.json:** `{"duration", "shots": [{"id", "start", "dur", "lead", "speech", "voice"|null,
  "words": [{"w", "t"}]}]}`; word `t` is local to the shot start (lead included).
- **Resolved shot** (what JS receives): `{"scene", "params", "beats": [{"t", "do", "args"}], "in", "out"}`.
- **JS runtime:** `TOON.init(style, manifest)`, `TOON.run(id, shot, dur) → gsap timeline`,
  scene module `TOON.scene.<name> = {build(cam, params, ctx) → st, idle?(tl, st, dur), actions: {verb(tl, st, t, args)}}`;
  `ctx = {id, dur, tl, rng}`; stage element id `<id>-stage`.
- **Motion events** (`compositions/<id>.motion.json`): `{"events": [{"t", "kind", "note"}]}`, kinds from
  `build_sfx.py` KIND: `pop whoosh shimmer impact stamp tick snap chime blip`.

## Review Focus

1. A `word:` beat whose word is not in that shot's narration (typo, contraction, number spoken as words) → build
   stops with the shot id, the word and the words actually heard. Pinned in Task 6.
2. A sheet whose asset count differs from `--names` (two props touching, a stray mark) → asset_sheet stops and
   says how many it found, writing nothing. Pinned in Task 4.
3. Re-running the asset stage must never spend money twice: an existing output is reused and the budget ledger
   refuses a call that would pass the limit. Pinned in Task 3.
4. A traced asset placed on a background colour different from the sheet's must show no chroma/background box
   or fringe around it (holes between limbs included). Pinned in Tasks 2 and 12 (gallery probe).
5. A scene or action name in `shots.json` that does not exist → build fails before rendering with the shot id and
   the known names (Python validates against a registry generated from `lib/scenes`). Pinned in Task 8.

## Execution notes

- Scene tasks (11-25) give the full spec, fixtures, probes and the code of the non-obvious parts; Task 12
  (bubbles) is written out in full as the pattern the other scenes follow.
- Run the fast loop per scene with `bash scripts/selftest.sh --only <shot-ids>`; the full selftest at the end of
  every plan file.
