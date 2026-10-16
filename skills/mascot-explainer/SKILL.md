---
name: mascot-explainer
description: Make a whole narrated mascot explainer video from code, in the style of flat-cartoon fitness/education explainers (one character, a 4-5 shade palette, planet bubbles, zoom-through transitions, bold italic text slams, MON/WED/FRI schedules, study shelves, phones, rockets, frame-by-frame exercise loops) at 4K. An image model (GPT Image 2.5 on fal.ai by default) draws only the character, poses and props on a chroma sheet, traced to SVG; body motion comes from one sprite-sheet image of up to 24 frames; everything else is drawn in code by 15 HyperFrames scene templates (plus zoom-through and muscle-inset actions) driven by a shots.json storyboard; Kokoro narration (or the user's recording), a ducked music bed and SFX synthesized from the same beats. Use when the user wants an animated explainer or YouTube-style cartoon video, a "video like that calisthenics explainer", a mascot or character explainer, sprite-sheet character animation inside a full video, or a whole video generated from code for cents (GPT Image 2.5 on fal.ai: low-quality Full HD stills, medium 4K sprite sheets).
---

# Mascot explainer

A script becomes a 4K narrated cartoon explainer. The style comes from an analysed 8:25 reference
(`references/reference-video.md`, text only): mostly still art moved by motion graphics, with frame-by-frame figure
loops about a third of the time. Code draws everything geometric; the image model draws only organic things.

| layer | who draws it | cost |
|---|---|---|
| backgrounds, bubbles, window room, day columns, text, tags, arrows, rays, flames, phones, cards, pages | code (15 scene templates in `lib/scenes/`) | $0 |
| the character in poses, hands, props, silhouettes | GPT Image 2.5 sheets (low, Full HD) → `asset_sheet.py` → clipped SVGs | ~$0.015 / sheet |
| exercise loops | base pose (low, Full HD) + one sprite sheet (medium, 4K, ≤24 cells, `KIND=sprite`) → sprite-video `slice.py --clip` → SVG frames | ~$0.06 / move |
| narration, music, SFX | Kokoro / the user's recording, ACE-Step or the user's track, synthesized SFX | $0 |

Every image is an OpenAI GPT Image 2.5 call on fal.ai: a 50 s two-exercise video costs ~$0.15, a 5-minute video with
five exercises ~$0.50 (Nano Banana: ~5x more). `SKILL` below is this folder; `SV` is the sprite-video skill and
`VM` the viral-motion skill (`scripts/py scripts/deps.py sv|vm` prints them). Python runs only as `SKILL/scripts/py`;
HyperFrames runs only as `$VM/scripts/hf` (it strips the Gemini keys: no frame ever goes to Gemini).

## 0. Setup (once per machine)
`bash SKILL/scripts/check.sh` lists what is missing and how to fix it. `bash SKILL/scripts/setup_venv.sh` makes the
skill's Python 3.12 venv. It needs sprite-video and viral-motion installed next to it (with viral-motion's venv for
Kokoro), ffmpeg, Node 18+, whisper.cpp large-v3-turbo and HyperFrames. The asset stage needs `FAL_AI_API_KEY`
exported (fal.ai); the free Gemini web provider needs Playwright for Node and its Chrome (`gemini_chrome.sh`, one
login), the Nano Banana provider `GEMINI_API_KEY`.
`bash SKILL/scripts/selftest.sh` proves the install for $0 (unit tests + a gallery of every scene checked by
pixel probes; `--render` adds a draft render).

## 1. Brief → checkpoint (before any image call)
1. `bash SKILL/scripts/new_project.sh <dir>`: a landscape HyperFrames project, `style.json`, `shots.json`, `gen/budget.json`.
2. `style.json` (`references/style-bible.md`): palette roles, chroma, character description, voice. Use the user's
   own mascot or the demo bible; never another channel's mascot, brand, app or book name.
3. Write the script, one line per shot (≤18 words), and `shots.json` (`references/storyboard.md`): a scene per line
   (`references/scene-catalog.md`, `scene-catalog-2.md`), the beats on the key words, the transitions.
4. Write the asset plan `P/assets.json` (`references/asset-plan.md`): every object a line names or implies, as code
   SVGs ($0), items (one sheet of up to 24 per call), poses, props and sprites, and the cost of each kind. Plan items
   generously: a camera popping in on "film yourself" or weights dropping onto a step make a shot richer for cents.
5. **Checkpoint:** show the user the palette and character, the script, a shot table (shot · scene · key beats),
   the asset plan and the cost estimate. Wait for "ok" or edits. This is the only stop before rendering.

## 2. Assets (`references/asset-prompts.md`)
1. Character sheet first (1 call): `ASPECT=16:9 SKILL/scripts/py SKILL/scripts/gen_asset.py P gen/character.png "<prompt>"`.
   Read it. Every later call passes `gen/character.png` as the first reference.
2. Pose sheet (3×2) and prop sheet (3×3), then
   `SKILL/scripts/py SKILL/scripts/asset_sheet.py gen/poses.png P --grid 3x2 --names a,b,c,d,e,f [--anchor x=center]`.
   It refuses when the count is wrong and writes `assets/svg/*.svg` + `assets/manifest.json`. A phone screen drawn in
   the chroma colour becomes a hole (`holes`), which the `phone` scene fills.
3. Small things: write the `code` SVGs and add each with `svg_asset.py P NAME FILE.svg [--anchor feet]`; draw
   the `items` with `SKILL/scripts/py SKILL/scripts/item_sheet.py P` (one call per 24, cut by shape, read the sheet).
   Any shot can use them through the generic `item` beat (`scene-catalog-2.md`): pop, fly, drop or spin in on a word,
   float or turn, leave.
4. Sprites with sprite-video's method (base pose, `template.py` with red guides, one grid call with `KIND=sprite`:
   medium quality at 3840×2160, so build the template at that size, e.g. 6×4 cells of 640×540), then
   `$SV/scripts/slice.py sheet.png frames --cols C --rows R --clip --ink-keep "<dark fill colours, e.g. the shorts>" [--ground]` and
   `SKILL/scripts/py SKILL/scripts/sprite_import.py frames P <name>`. Without `--clip` the frames keep a background box.
5. Check them on an asset board: a temporary `bubbles` shot with every asset, `build.py --only board`, one snapshot.
   No chroma fringe, the same ink weight, the same character everywhere.

`gen_asset.py` never pays twice (an existing file is reused) and refuses a call past `gen/budget.json` "limit".

**Image providers** (the user's choice): every image is OpenAI GPT Image 2.5 Flare on fal.ai through
`scripts/fal_gen.py` (`FAL_AI_API_KEY`), ~30-40 s a call. A still (character sheet, poses, props, sprite base poses)
is low quality at Full HD (1920×1072 at 16:9; ~$0.0045, ~$0.015 with the character reference); an animation sprite
sheet is `KIND=sprite`, medium quality at 3840×2160 (~$0.026 + ~$0.01 a reference). Any aspect ratio up to 3:1 works;
sides are multiples of 16. Quote the total at the checkpoint. Tested on Dr. Gains: the same character from the
reference, a 24-frame push-up that follows its template within 1 % of the cell height, clean SVG traces; it draws
the olive shorts a little greener. `PROVIDER=api` uses Nano Banana instead (2K/4K, ~5x the price);
`PROVIDER=gemini-web` draws in the Gemini web app of the user's logged-in Chrome on CDP 9003 for $0 (the rest of this
paragraph). That app offers only 1:1, 16:9, 9:16, 4:3 and 3:4 and the nearest is asked for (3:2 → 4:3, 2:3 → 3:4,
5:4 → 4:3), so cut grids and build templates at the ratio actually asked for; ~2K, now and then ~1K (warned about:
delete it and run again); calls on one Chrome run one at a time (a lock), about 40 s each.
A free sprite sheet (`PROVIDER=gemini-web KIND=sprite`) has no 4K, so a small figure gets fewer cells (12-16, not 24),
and the app reads cell 1 as the start of the move: a sheet that starts halfway gets its first row redrawn from the
start. For more frames give every sheet the start: frames 1-12 (start → halfway) on one 4×3 sheet plus every other
frame of the whole move (2, 4 … 24) on another, keeping its second half (14-24): 18 frames, all 2K. Measure each
cell's figure top before slicing (it must move steadily) and `--drop` a cell that jumps.
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
The MP4 path (open it), the contact sheet, length and resolution, the Critic's final grades, the image spend from
`gen/budget.json`, and what another round would improve.

## Rules
- Image models only in the asset stage, through `gen_asset.py`; the checkpoint comes first.
- Every key word in the narration lands an action; nothing on screen is still for 2 s.
- No frame, still or audio of a reference video goes into any repo; describe it in text.
- A beat no template covers: a one-off scene in `P/assets/js/scenes/` (`scene-catalog-2.md`, last section).

## Scripts
| script | does |
|---|---|
| `check.sh`, `setup_venv.sh`, `py`, `deps.py` | setup, the venv, finding sprite-video and viral-motion |
| `new_project.sh <dir> [style]` | a new project |
| `gen_asset.py P OUT "prompt" [refs]` | one cached, budgeted image: GPT Image 2.5 on fal (stills low/Full HD, `KIND=sprite` medium/4K; `PROVIDER`, `SIZE`, `QUALITY`, `ASPECT`) |
| `fal_gen.py OUT "prompt" [refs]` | one GPT Image 2.5 call on fal.ai (gen_asset's default) |
| `item_sheet.py P [--dry]` | the asset plan's items: up to 24 per call → one SVG each |
| `svg_asset.py P NAME FILE.svg [--anchor …]` | a hand-written SVG → an asset in the manifest |
| `gemini_web.cjs OUT "prompt" [refs]`, `gemini_chrome.sh` | one image from the Gemini web app; the Chrome it uses (CDP 9003) |
| `asset_sheet.py SHEET P --names … [--grid CxR] [--anchor …]` | a sheet of poses/props → clipped SVGs + manifest |
| `sprite_import.py FRAMES P NAME` | a sliced sprite → the project |
| `timing.py P [--recording …] [--no-voice]` | narration + word times → `audio/timing.json` |
| `build.py P [--only ids] [--no-sfx]` | the HyperFrames project, SFX stem, music duck |
| `critic_frames.py P [--out critique/round-N]` | the Critic's labelled frame sheets |
| `finish_audio.py RENDER MIX OUT` | the clean simulated mix into the rendered MP4 + the loudness gate |
| `probe.py`, `selftest.sh [--only ids] [--render]` | pixel probes; the $0 self test |
