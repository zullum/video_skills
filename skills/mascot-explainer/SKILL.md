---
name: mascot-explainer
description: Make a whole narrated mascot explainer video from code, in the style of flat-cartoon fitness/education explainers (one character, a 4-5 shade palette, planet bubbles, zoom-through transitions, bold italic text slams, MON/WED/FRI schedules, study shelves, phones, rockets, frame-by-frame exercise loops) at 4K. Nano Banana (Gemini image) draws only the character, poses and props on a chroma sheet, traced to SVG; body motion comes from one sprite-sheet image of up to 24 frames; everything else is drawn in code by 15 HyperFrames scene templates (plus zoom-through and muscle-inset actions) driven by a shots.json storyboard; Kokoro narration (or the user's recording), a ducked music bed and SFX synthesized from the same beats. Use when the user wants an animated explainer or YouTube-style cartoon video, a "video like that calisthenics explainer", a mascot or character explainer, sprite-sheet character animation inside a full video, or a whole video generated from code with free (Gemini web app, the default) or cheap (Gemini API) assets.
---

# Mascot explainer

A script becomes a 4K narrated cartoon explainer. The style comes from an analysed 8:25 reference
(`references/reference-video.md`, text only): mostly still art moved by motion graphics, with frame-by-frame figure
loops about a third of the time. Code draws everything geometric; Gemini draws only organic things.

| layer | who draws it | cost |
|---|---|---|
| backgrounds, bubbles, window room, day columns, text, tags, arrows, rays, flames, phones, cards, pages | code (15 scene templates in `lib/scenes/`) | $0 |
| the character in poses, hands, props, silhouettes | Nano Banana sheets → `asset_sheet.py` → clipped SVGs | $0 (web) · ~$0.10 / sheet (API) |
| exercise loops | one sprite sheet (≤24 cells) → sprite-video `slice.py --clip` → SVG frames | $0 (web) · ~$0.20-0.25 / move (API) |
| narration, music, SFX | Kokoro / the user's recording, ACE-Step or the user's track, synthesized SFX | $0 |

Images are drawn in the Gemini web app of the user's plan by default ($0); with `PROVIDER=api` a ~50 s video costs
about $0.75-1.50 in API calls. `SKILL` below is this folder; `SV` is the sprite-video skill and
`VM` the viral-motion skill (`scripts/py scripts/deps.py sv|vm` prints them). Python runs only as `SKILL/scripts/py`;
HyperFrames runs only as `$VM/scripts/hf` (it strips the Gemini keys: no frame ever goes to Gemini).

## 0. Setup (once per machine)
`bash SKILL/scripts/check.sh` lists what is missing and how to fix it. `bash SKILL/scripts/setup_venv.sh` makes the
skill's Python 3.12 venv. It needs sprite-video and viral-motion installed next to it (with viral-motion's venv for
Kokoro), ffmpeg, Node 18+, whisper.cpp large-v3-turbo and HyperFrames. The asset stage needs Playwright for Node and
the Gemini Chrome (`bash SKILL/scripts/gemini_chrome.sh`, then the user logs in to Gemini once), or `GEMINI_API_KEY`
for `PROVIDER=api`.
`bash SKILL/scripts/selftest.sh` proves the install for $0 (unit tests + a gallery of every scene checked by
pixel probes; `--render` adds a draft render).

## 1. Brief → checkpoint (before any Gemini call)
1. `bash SKILL/scripts/new_project.sh <dir>`: a landscape HyperFrames project, `style.json`, `shots.json`, `gen/budget.json`.
2. `style.json` (`references/style-bible.md`): palette roles, chroma, character description, voice. Use the user's
   own mascot or the demo bible; never another channel's mascot, brand, app or book name.
3. Write the script, one line per shot (≤18 words), and `shots.json` (`references/storyboard.md`): a scene per line
   (`references/scene-catalog.md`, `scene-catalog-2.md`), the beats on the key words, the transitions.
4. List the assets the shots need (one pose per exercise, props, sprites) and the cost.
5. **Checkpoint:** show the user the palette and character, the script, a shot table (shot · scene · key beats),
   the asset list and the cost estimate. Wait for "ok" or edits. This is the only stop before rendering.

## 2. Assets (`references/asset-prompts.md`)
1. Character sheet first (1 call, 2K): `SIZE=2K ASPECT=16:9 SKILL/scripts/py SKILL/scripts/gen_asset.py P gen/character.png "<prompt>"`.
   Read it. Every later call passes `gen/character.png` as the first reference.
2. Pose sheet (3×2) and prop sheet (3×3), then
   `SKILL/scripts/py SKILL/scripts/asset_sheet.py gen/poses.png P --grid 3x2 --names a,b,c,d,e,f [--anchor x=center]`.
   It refuses when the count is wrong and writes `assets/svg/*.svg` + `assets/manifest.json`. A phone screen drawn in
   the chroma colour becomes a hole (`holes`), which the `phone` scene fills.
3. Sprites with sprite-video's method (base pose, `template.py` with red guides, one grid call), then
   `$SV/scripts/slice.py sheet.png frames --cols C --rows R --clip --ink-keep "<dark fill colours, e.g. the shorts>" [--ground]` and
   `SKILL/scripts/py SKILL/scripts/sprite_import.py frames P <name>`. Without `--clip` the frames keep a background box.
4. Check them on an asset board: a temporary `bubbles` shot with every asset, `build.py --only board`, one snapshot.
   No chroma fringe, the same ink weight, the same character everywhere.

`gen_asset.py` never pays twice (an existing file is reused) and refuses a call past `gen/budget.json` "limit".

**Image provider:** by default `gen_asset.py` draws each image in the Gemini web app of the user's logged-in Chrome
on CDP 9003 (`gemini_chrome.sh`; the user logs in once by hand) through `scripts/gemini_web.cjs` + Playwright: $0,
~40 s, ~2K, the JPEG download stored as a PNG. Only when the user asks for it, `PROVIDER=api` pays for Nano Banana API
calls instead (2K/4K, any aspect ratio; quote the cost at the checkpoint). The web app offers only 1:1,
16:9, 9:16, 4:3 and 3:4 and the nearest is asked for (3:2 → 4:3, 2:3 → 3:4, 5:4 → 4:3), so cut grids and build
sprite templates at the ratio actually asked for; there is no 4K, so give a small figure fewer cells (12-16, not 24).
Exit 5 = Gemini is logged out: ask the user to log in there, never type credentials. It automates the consumer app,
which Google's terms may not allow: say so once before the first free run. Each image leaves a chat in the history.

## 3. Narration and timing
`SKILL/scripts/py SKILL/scripts/timing.py P` voices every `say` with Kokoro (cached per line), normalizes it, and
gets word times from whisper → `audio/timing.json`. With the user's own voice: run viral-motion's
`recording/pipeline.sh` (its `references/recording.md`), then `timing.py P --recording P/audio/recording/recording.json`.

## 4. Build and stills
`SKILL/scripts/py SKILL/scripts/build.py P --no-sfx` checks every scene, action, asset and sprite name before it
writes anything (a typo stops it with the shot id and the names it knows), resolves the beats, and writes
`index.html`, `compositions/<id>.html`, the motion events and `audio/sfx_cues.json`. A `word:` beat whose word wasn't
heard stops with the words that were. Then `(cd P && $VM/scripts/hf check .)` must report 0 errors, and
`$VM/scripts/hf snapshot P --at <start+.2, middle, end-.2 of every shot> --no-end`: read every frame yourself.

## 5. Audio
- Music bed: viral-motion's ACE-Step in score mode (an instrumental caption; `$VM/scripts/music/run_music.sh P`,
  then `trim.sh <take> <length> P/assets/audio/music.wav`), or the user's own track trimmed to the length. Without
  either, the video has narration and SFX only; say so.
- `build.py P` (without `--no-sfx`) synthesizes the SFX stem from the beats (pop, whoosh, shimmer, impact, tick…)
  and ducks the music −10 dB under every spoken line.
- Gate: `$VM/scripts/py $VM/scripts/qa/mix_check.py P/index.html --out P/renders/mix_sim.wav` passes (−14 LUFS ±1,
  true peak ≤ −1 dBTP). Tune `style.json` `mix` and rebuild.

## 6. Critique loop (`references/critique.md`)
`SKILL/scripts/py SKILL/scripts/critic_frames.py P --out critique/round-1` snapshots every shot (start, middle, end,
each beat) into labelled sheets → a fresh Critic agent grades every shot 1-10 → fix the three worst problems (timing
and params first, scene code next, a new image last) → repeat until every shot is 8+, 3 rounds at most.

## 7. Render and verify
Build once more without `--no-sfx` first (a `--no-sfx` build leaves the SFX stem out).
`(cd P && $VM/scripts/hf render -o renders/<name>-4k.mp4 --resolution landscape-4k --fps 30 --workers 2 -q delivery)`;
then `$VM/scripts/py $VM/scripts/qa/mix_check.py P/index.html --out P/renders/mix.wav` and
`SKILL/scripts/py SKILL/scripts/finish_audio.py renders/<name>-4k.mp4 renders/mix.wav renders/<name>-final.mp4`: it puts the
clean mix into the render (HyperFrames' normal render can add AAC glitches and then lower the whole track by ~4 dB;
the render log says "Audio lowered by") and checks the -14 LUFS / -1 dBTP gate on the result.
`ffprobe` shows 3840×2160; `$VM/scripts/py $VM/scripts/qa/av_check.py renders/<name>-final.mp4 --duration <total>
--expect <slam times>` (take the times from `compositions/<id>.motion.json` + the shot slots in `audio/sfx_cues.json`;
under a voice the nearest onset can be the spoken word, so when it flags, measure the onsets in `assets/audio/sfx.wav`);
a contact sheet (`bash $VM/scripts/qa/contact_sheet.sh <mp4> <jpg> <times…>`) for a last look.

## 8. Deliver
The MP4 path (open it), the contact sheet, length and resolution, the Critic's final grades, the Gemini spend from
`gen/budget.json`, and what another round would improve.

## Rules
- Gemini only in the asset stage, through `gen_asset.py`; the checkpoint comes first.
- Every key word in the narration lands an action; nothing on screen is still for 2 s.
- No frame, still or audio of a reference video goes into any repo; describe it in text.
- A beat no template covers: a one-off scene in `P/assets/js/scenes/` (`scene-catalog-2.md`, last section).

## Scripts
| script | does |
|---|---|
| `check.sh`, `setup_venv.sh`, `py`, `deps.py` | setup, the venv, finding sprite-video and viral-motion |
| `new_project.sh <dir> [style]` | a new project |
| `gen_asset.py P OUT "prompt" [refs]` | one cached image: the Gemini web app by default, `PROVIDER=api` for the paid API (`SIZE`, `ASPECT`) |
| `gemini_web.cjs OUT "prompt" [refs]`, `gemini_chrome.sh` | one image from the Gemini web app; the Chrome it uses (CDP 9003) |
| `asset_sheet.py SHEET P --names … [--grid CxR] [--anchor …]` | a sheet of poses/props → clipped SVGs + manifest |
| `sprite_import.py FRAMES P NAME` | a sliced sprite → the project |
| `timing.py P [--recording …] [--no-voice]` | narration + word times → `audio/timing.json` |
| `build.py P [--only ids] [--no-sfx]` | the HyperFrames project, SFX stem, music duck |
| `critic_frames.py P [--out critique/round-N]` | the Critic's labelled frame sheets |
| `finish_audio.py RENDER MIX OUT` | the clean simulated mix into the rendered MP4 + the loudness gate |
| `probe.py`, `selftest.sh [--only ids] [--render]` | pixel probes; the $0 self test |
