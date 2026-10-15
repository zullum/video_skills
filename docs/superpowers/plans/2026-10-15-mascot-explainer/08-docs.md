# 08 Docs (Tasks 26-28)

### Task 26: Reference video breakdown (`references/reference-video*.md`)

The analysed video is the user's local file
`~/Downloads/YTDown.com_YouTube_Media_iZNm0zr_gc8_Start-with-this-calisthenics-workout-Or-don-t_001_1080p.mp4`
(8:25, 1080p30). Text only goes into the repo: no frames, stills or audio.

**Files:** Create `references/reference-video.md` (overview + 0:00-4:15) and `references/reference-video-2.md`
(4:15-8:25), each ≤200 lines.

- [ ] **Step 1: Prepare** in the scratchpad: copy the video into its own folder, a 16 kHz WAV and the whisper SRT
  (`whisper-cli -m …/ggml-large-v3-turbo.bin -l en -osrt`), and the scene-cut list
  (`ffmpeg -i v.mp4 -filter:v "select='gt(scene,0.25)',showinfo" -f null -`).
- [ ] **Step 2: Dispatch six agents in one message** (general-purpose, parallel), one per segment
  `0-85, 85-170, 170-255, 255-340, 340-425, 425-505` s. Each prompt carries: the video path, its segment, the SRT
  lines of the segment, the 17 template names with one line each (from the spec's catalog), and the task:
  "Extract frames at 3 fps for your segment (`ffmpeg -ss A -t D -i v.mp4 -vf fps=3,scale=480:-1,tile=6x4`), Read
  every sheet, and return a markdown table with one row per visual beat: `| start-end | narration (≤12 words) |
  template (or custom: …) | how it is built: layers, assets, motion with timings and eases | transition in | sfx |`.
  Be concrete (sizes, counts, directions, holds). Note anything no template covers. Do not write files in the repo."
- [ ] **Step 3: Merge** into the two files: an overview (palette and line style of the reference, pacing stats —
  beats per minute, median beat length, share of frame-by-frame animation —, template frequency table, the list of
  `custom:` beats with the template that comes closest), then the beat tables.
- [ ] **Step 4: Check coverage** with a short inline script: the table ranges cover 0-505 s with no gap over 1 s,
  and every catalog template appears at least once (list the ones that don't and why).
- [ ] **Step 5: Commit** `mascot-explainer: reference video breakdown`.

### Task 27: References

**Files:** Create `references/scene-catalog.md` (+ `scene-catalog-2.md` if needed), `references/style-bible.md`,
`references/asset-prompts.md`, `references/storyboard.md`, `references/critique.md`.

- [ ] **Step 1: `scene-catalog.md`** — one section per template: the reference beat it reproduces (timestamps), what
  the viewer sees, params (with defaults), actions (with their sound), the assets it needs, timing tips, and one
  ready `shots.json` example that passes `build.py`. Generated from the scene headers and Tasks 11-25; the examples
  are the gallery shots with real asset names. Add the transitions and the generic actions.
- [ ] **Step 2: `style-bible.md`** — `style.json` fields (`size`, `fps`, `palette` roles, `chroma`, `ink`, `mix`,
  `character`, `voice`); how to pick a palette (3 background tones of one hue + panel + one accent, skin far from
  the backgrounds, chroma far from every colour, `|Δ| > 70` per the sheet test); the flat-comic drawing rules every
  prompt repeats (thick black outlines, flat fills, no gradients, muscle lines as ink, faceless head with white eye
  slits, plain chroma background); the demo bible (coral mascot, deep-teal palette).
- [ ] **Step 3: `asset-prompts.md`** — prompts with placeholders `{CHARACTER}` `{PALETTE}` `{CHROMA}`:
  character sheet (turnaround + 3 expressions, 16:9 2K), pose sheet (3×2, 3:2 2K), prop sheet (3×3, 1:1 2K), hand
  holding a phone whose screen is solid `{CHROMA}`, base pose for a sprite, and the rule "pass the character sheet as
  the first reference image"; for sprite grids point to sprite-video's `references/prompts.md`; what to check on
  each result and when a retry is worth it.
- [ ] **Step 4: `storyboard.md`** — the `shots.json` schema and `at` syntax; pacing rules from the reference (a beat
  every 2-5 s, cuts on line ends, the key word lands an action, something moves at least every 2 s, motifs
  return: the same bubbles reappear in later scenes); a narration-pattern → template table (a list of options →
  bubbles/swarm; a schedule → days; a study → shelf + crowd + citation; a claim or term → textSlam; an app → phone;
  a progression → seqRows/stairs; a how-to → exerciseDemo + insets; energy, a turn → powerUp; a pause → freeze);
  how long a line may be (≤ 18 words per shot).
- [ ] **Step 5: `critique.md`** — the Critic's checklist and grade sheet (1-10 per shot): style fidelity (palette,
  ink weight equal across traced assets, no chroma fringe), motion (pops land on words, no dead 2 s, transitions
  read), sprites (sprite-video's critique: shake, sliding feet, missing in-betweens), text (legible, inside the frame),
  audio (voice clear over the music, SFX on the actions); the Critic prompt for a fresh agent; 3 rounds max, every
  shot 8+.
- [ ] **Step 6:** every file ≤200 lines (`wc -l`), every example in the catalog builds (`build.py` on a temp project
  holding the catalog examples). **Commit** `mascot-explainer: references`.

### Task 28: SKILL.md, README, install

**Files:** Create `skills/mascot-explainer/SKILL.md`; Modify `README.md` (table row, setup, cost, layout).

- [ ] **Step 1: `SKILL.md`** (≤200 lines). Frontmatter `name: mascot-explainer`, a description that triggers on:
  narrated mascot/character explainer, animated fitness or education explainer, "like the calisthenics explainer
  video", planet bubbles, sprite-sheet character animation in a full video, a whole video from code with Nano Banana
  assets. Body: what it makes and costs; `SKILL`, `SV`, `VM` paths; 0 check (`check.sh`, `setup_venv.sh`);
  1 brief: script lines, `style.json`, `shots.json`, the asset list and a cost estimate → **Checkpoint** (the user
  approves before any Gemini call); 2 assets (character sheet first, then pose/prop sheets, `asset_sheet.py`, an asset
  board snapshot to check them; sprites with sprite-video + `--clip` + `sprite_import.py`); 3 `timing.py`;
  4 `build.py` + `hf check` + stills of every shot; 5 audio (music: ACE-Step score mode or the user's track
  trimmed to the length; SFX come from the beats; `mix_check.py`); 6 critique loop; 7 render 4K
  (`hf render --resolution landscape-4k --fps 30 --workers 2 -q delivery`) + `av_check.py`; 8 deliver (MP4 path,
  contact sheet, grades, Gemini spend from `gen/budget.json`). A script reference table, the rules (Gemini only in
  the asset stage, never commit reference frames, every key word gets an action), and the fallback: a beat no
  template covers gets a one-off `<project>/assets/js/scenes/<name>.js` written to the catalog's recipes and header
  rule (build.py's registry reads the project copy too).
- [ ] **Step 2: README** — a row in the skills table; a "mascot-explainer" section with setup (`check.sh`,
  `setup_venv.sh`, needs sprite-video and viral-motion installed), cost (demo spend), and the repo layout entry.
  Preview GIF added in Task 33.
- [ ] **Step 3: Verify** `bash install.sh claude --project /tmp/mx-install` copies the skill; in the copy
  `scripts/check.sh` reports only the missing venv (fresh copy) and `setup_venv.sh` fixes it. Remove `/tmp/mx-install`.
- [ ] **Step 4: Commit** `mascot-explainer: SKILL.md and README`.
