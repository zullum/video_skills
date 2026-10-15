# 09 Demo (Tasks 29-33)

The demo project lives outside the repo at `~/myprojects/mascot-explainer-demo/` (created with
`hf init … --example=blank --resolution=landscape`); its inputs are committed to `skills/mascot-explainer/examples/demo/`
(`script.md`, `style.json`, `shots.json`, sprite specs). Gemini budget: `gen/budget.json` limit 1.50.

### Task 29: Style, checkpoint, character, asset sheets

- [ ] **Step 1: `style.json`** — size [1920,1080], fps 30, palette `bgDeep #0E2F38, bgMid #1D5C66, bgLight #7FB8B5,
  panel #CFE8E4, ink #141418, skin #FF8A5B, shorts #23305A, sleeve #FFFFFF, accent #FFD166, text #FFFFFF,
  rim #FFFFFF`, chroma `#00B140`, mix `{music: .5, sfx: .6}`, voice `af_heart`, character "a bald, muscular,
  friendly cartoon man with coral-orange skin, white eye slits and no other facial features except a small mouth,
  navy athletic shorts, white wristbands, barefoot, thick black comic outlines, flat colours".
- [ ] **Step 2: Draft `script.md` + `shots.json`** (≈120 words, 17 shots, ~50 s; one line per shot):
  s01 bubbles "Push-ups. Squats. Two sets each." (pop on each word) · s02 days "Monday, Wednesday, Friday."
  · s03 flyBy "Fifteen minutes a session." (satellite, "15 MIN" badge) · s04 textSlam "That's the whole plan." ·
  s05 windowRoom "So why does it feel like too little?" (astronaut fg, swarm) · s06 crowd "Most people never even
  start." (think "?") · s07 phone "Every app sells you more." (feed + icons) · s08 cardWall "More moves, more
  programs, more tabs." · s09 textSlam "Your first win isn't volume. It's showing up." · s10 exerciseDemo push-up
  (24 frames, zoomIn) "Push-ups: hands under shoulders, chest to the floor." (callout) · s11 exerciseDemo "Chest,
  shoulders and triceps in one move." (insets) · s12 exerciseDemo squat "Squats: feet planted, hips back, full
  depth." (arrow, tag 2x12) · s13 seqRows "When the top of the range feels easy, add one rep." · s14 stairs "Same
  moves, just harder, month after month." · s15 powerUp "Stop researching." (freeze) · s16 powerUp "Start today."
  (ignite) · s17 bubbles "Two sets is enough." (highlight, zoom out to black). Transitions: zoomIn into s10,
  whip at s07/s13, flash at s16. Assets named in the list below.
- [ ] **Step 3: Checkpoint** — show the user the palette, the script, the shot table (shot, template, key beats),
  the asset list (character sheet; pose sheet: `hips` waist-up hands on hips, `point` finger up, `back` full body
  from behind, `sitphone` sitting with a phone, `astro` astronaut over-shoulder, `stand` full body front;
  prop sheet: `box`, `rocket`, `satellite`, `jar`, `person` silhouette, `handphone` (chroma screen), `dumbbell`,
  `rings`, `parallettes`) and the cost estimate (3 asset calls + 4 sprite calls ≈ $0.75, cap $1.50). Wait for "ok".
- [ ] **Step 4: Character sheet** — `SIZE=2K ASPECT=16:9 scripts/py scripts/gen_asset.py P gen/character.png
  "<asset-prompts.md character sheet>"`; Read it; regenerate only if a style rule is broken.
- [ ] **Step 5: Pose and prop sheets** — `gen/poses.png` (3:2, ref `gen/character.png`), `gen/props.png` (1:1,
  ref `gen/character.png`); `asset_sheet.py gen/poses.png P --grid 3x2 --names hips,point,back,sitphone,astro,stand`
  and `asset_sheet.py gen/props.png P --grid 3x3 --names box,rocket,satellite,jar,person,handphone,dumbbell,rings,parallettes
  --anchor rocket=center,satellite=center,jar=feet`; check `handphone` has a hole.
- [ ] **Step 6: Asset board** — a temp shot `board` (bubbles, all 15 assets as items on a 5×3 grid, r 150) built with
  `build.py --only board` and one snapshot; Read it: no chroma fringe, same ink weight, same character. Commit the
  inputs (`examples/demo/*.json`, `script.md`).

### Task 30: Sprites (24-frame push-up, 8-frame squat)

- [ ] **Step 1: Push-up base** — front view, top of the push-up, full body, on chroma (`gen/pushup_base.png`, 2K 16:9,
  ref character sheet). Mark the shoulders, elbows, wrists and the torso box with a coordinate overlay.
- [ ] **Step 2: 24-cell template** — `examples/demo/pushup_front_spec.py` (adapted from sprite-video's
  `fly_spec.py` two-arm guides + `pushup_spec.py` rig): 6×4 cells, both hands kept planted (`keep`), arms erased in
  cells 1-23, the torso + head piece lowered by `d_k = D·(1 − cos(πk/23))/2` (D = the drop to the bottom pose), and
  shoulder-elbow-wrist guide dots per cell with the elbows flaring out as the body drops. Build it with
  `<sv>/scripts/template.py` and look at it.
- [ ] **Step 3: Sheet** — `SIZE=4K ASPECT=16:9 gen_asset.py P gen/pushup_sheet.png "<All-cells grid prompt>"
  gen/pushup_tpl.png gen/pushup_base.png` (4K: 24 small cells). Check: same size in every row, no red left, arms in
  every cell.
- [ ] **Step 4: Slice + import** — `<sv>/scripts/slice.py gen/pushup_sheet.png gen/pushup_frames --cols 6 --rows 4
  --clip`, then `sprite_import.py gen/pushup_frames P pushup`; `rep` = frames 0→23 down (1 frame each, 4 at the
  bottom) and 23→0 up (1 each, 6 at the top).
- [ ] **Step 5: Squat** — same flow with `examples/demo/squat_spec.py` (adapted from sprite-video's
  `squat_spec.py`, 4×2, `ASPECT=3:2`), `slice.py … --cols 4 --rows 2 --ground --clip`, `sprite_import.py … squat`.
- [ ] **Step 6: Sprite check** — a temp `exerciseDemo` shot per sprite, 12 snapshots across one rep, tiled; review
  with sprite-video's `references/critique.md` (shake, floating torso, jumps). Fix with `rep` holds or slicing first,
  regenerate only for drawing errors. Commit the specs.

### Task 31: Script → timing → build → stills

- [ ] **Step 1:** `timing.py P` → `audio/timing.json` (~50 s). Fix any `word:` beat error by editing the beat.
- [ ] **Step 2:** `build.py P --no-sfx`, `hf check P` (0 errors), `hf snapshot P --at <start+.2, middle, end-.2 of
  every shot>`; Read the contact sheet. Fix layout (text in frame, figures not cut, bubbles not overlapping).
- [ ] **Step 3: Commit** the final `examples/demo/shots.json`.

### Task 32: Audio, critique, 4K

- [ ] **Step 1: Music** — `audio/song.json` from viral-motion's `templates/score.json` with mode `score`,
  instrumental, caption "upbeat lo-fi hip hop instrumental bed for an animated explainer: soft punchy drums, warm
  Rhodes chords, round bass, steady 92 bpm groove, constant energy, short soft ending", duration = total + 6,
  target_duration = total, seeds [11, 23]; `<vm>/scripts/music/run_music.sh P`; pick the take whose level stays
  even (Read `<vm>` `references/music.md` for ranking); `<vm>/scripts/music/trim.sh <take> <total> P/assets/audio/music.wav`.
  If music generation can't run (disk < 10 GB or no ACE-Step), ask the user for a track or continue without music
  and say so.
- [ ] **Step 2:** `build.py P` (SFX built, music ducked) → `mix_check.py index.html --out renders/mix_sim.wav`; adjust
  `style.mix` until PASS.
- [ ] **Step 3: Critique loop** — snapshots of every shot (start, middle, end, each beat) → a fresh Critic agent with
  `references/critique.md` grades every shot; fix the 3 worst problems; repeat until every shot is 8+ (max 3 rounds).
- [ ] **Step 4: Render** — `hf render P -o renders/demo-4k.mp4 --resolution landscape-4k --fps 30 --workers 2
  -q delivery`; `ffprobe` shows 3840×2160, 30 fps; `<vm>` `av_check.py renders/demo-4k.mp4 --duration <total>
  --expect <s04 and s09 slam times>`; contact sheet with `<vm>/scripts/qa/contact_sheet.sh`; a final Critic pass on it.

### Task 33: Wrap-up

- [ ] **Step 1:** preview GIF (6 s, 480 px, 12 fps, palettegen) → `assets/mascot-explainer.gif` (< 3 MB) in the README.
- [ ] **Step 2:** `wc -l` every file under `skills/mascot-explainer/` (all ≤200); `bash scripts/selftest.sh` green;
  `git log` authors all `zullumsan@gmail.com`.
- [ ] **Step 3:** whole-branch review by a fresh reviewer agent (spec + plan + diff); fix what it confirms.
- [ ] **Step 4:** commit; report to the user: MP4 path, contact sheet, grades, Gemini spend, open issues. Ask before
  pushing or opening a PR.
