---
name: sprite-video
description: Make short 4K cartoon animations (flex, push-up, any simple body motion) from ONE or two Nano Banana (Gemini image) sprite sheets, traced to SVG and filmed with a camera. No video model. Use when the user wants a cheap animated clip of a flat cartoon character, a "Blue Gains" style fitness animation, or a sprite-sheet / SVG animation pipeline.
---

# Sprite-sheet → SVG → 4K video

One generated image holds every frame of the motion as a grid. Code slices it, traces each frame to
SVG (sharp at any size), and films the frames with a camera into an MP4 (1080p or 4K). A 5-second
clip costs about $0.20 in image calls (2 images at 2K), versus $0.40–3.00 for 5 s of Veo.

Everything runs locally: Python 3 + Node + ffmpeg + Chromium (Playwright). Scripts are in
`scripts/`, prompt templates in `references/prompts.md`, the review checklist in
`references/critique.md`, costs in `references/costs.md`.

## Setup (once)

```bash
pip install numpy scipy pillow vtracer potracer
npm i -D playwright && npx playwright install chromium     # or set CHROMIUM=/path/to/chrome
export GEMINI_API_KEY=...                                    # never print it or write it to files
```

## The method (what makes it work)

1. **Pre-draw the character in EVERY cell.** A template with the same base pose pasted into all
   cells locks size and position. With only cell 1 seeded, the model zooms in row by row.
2. **Ask the model to repaint only what moves** ("repaint ONLY the arm on the viewer's right").
3. **Never ask for in-between angles in words.** The model jumps straight to the end pose. Draw red
   guides into each cell instead (a line + circle for a straight limb, shoulder–elbow–wrist dots for
   a bending arm) and tell it to draw along them and then remove all red.
4. **For whole-body motion, rig roughly in code.** E.g. a push-up: rotate the body about the toes,
   erase the arm, keep the hand planted, draw the IK arm guide (`examples/pushup_spec.py`). The model
   cleans it up. An "edit this into the bottom position" prompt often returns the image unchanged.
5. **Generate at 2K; get 4K from the SVG.** `trace2.py` traces the black ink with potrace from a 4×
   supersampled map (smooth, sharp outlines) and the colour fills with vtracer underneath. Use 4K
   source only for 24-cell grids where the character would be under ~400 px tall, or extreme close-ups.
6. **Static things live in the player, not in frames** (the floor line), so they never boil.
7. **Hide sheet changes inside motion.** If frames come from two sheets, switch sheets on a moving
   frame, never on a hold, and drop duplicate frames.

## Workflow

Work in a project folder; keep the base image, templates, sheets and frames there.

### 1. Base pose (1 call, 2K)
Generate the character in the neutral start pose with the framing you want (waist-up mid shot,
character left of centre with room for the arm; or full body side view on a thin floor line).
Prompt: `references/prompts.md` → "Base pose". Pass the user's reference images.
```bash
SIZE=2K ASPECT=5:4 python3 scripts/gen.py base.png "<base prompt>" ref1.png
```
Look at it. Note the pixel positions of pivots (shoulder, toes, wrist) with a coordinate overlay.

### 2. Template (free)
Write a SPEC JSON (format documented at the top of `scripts/template.py`) and build it:
```bash
python3 scripts/template.py spec.json template.png
```
- Limb motion with a still body (flex, curl, wave): 6×4 cells, `"fit": {"height": 0.9}`, empty
  `cells` → base in every cell. If the start of the motion is large (arm hanging → horizontal), make a
  second small sheet (4×2) with angle guides for those in-betweens.
- Whole-body motion around ONE pivot (push-up, plank rock): 3×3 cells, every cell rigged + guided.
  Copy and adapt `examples/pushup_spec.py`.
- Whole-body motion with several joints (squat, lunge, sit-up, deadlift): cut the base into
  `pieces` (foot, shin, thigh, torso + head, arms) and place them by forward kinematics, one cell per
  frame. Copy and adapt `examples/squat_spec.py` (4×2 cells, tall cells, `ASPECT=3:2`). The model
  only has to repair the joints; it got all 8 squat frames right on the first call.
- Pick the grid so a cell has the figure's shape: a standing full body wants tall cells (4×2 at 3:2),
  a lying push-up wide cells (3×3 at 16:9). A wrong cell shape makes the figure tiny.
Open the template and check guides sit where the limb should be.

### 3. Sprite sheet (1 call per sheet, 2K)
```bash
SIZE=2K ASPECT=16:9 python3 scripts/gen.py sheet.png "<grid prompt>" template.png base.png
```
Prompts: `references/prompts.md` → "All-cells grid" / "Guided in-betweens". Check the result: same
size in all rows? any red left? arm in every cell? Regenerate only if a rule was broken.
If an extra sheet's colours drifted from the main one, fix before slicing:
`python3 scripts/colorfix.py extra.png main.png extra_cf.png COLS ROWS MAINCOLS MAINROWS`.

### 4. Slice + trace (free)
```bash
python3 scripts/slice.py sheet.png frames --cols 6 --rows 4 --keep-small --anchor 0.18,0.42   # still head
python3 scripts/slice.py sheet.png frames --cols 3 --rows 3 --floor                           # floor scene
python3 scripts/slice.py sheet.png frames --cols 4 --rows 2 --ground                          # feet planted (squat)
python3 scripts/merge.py all --ref=main main_extra:0-6 main:8-23                              # join sheets
```
`--anchor` = column band (fractions of cell width) containing the head; aligns frames that drift.
`--ground` = lock the planted foot (heel + sole) to frame 0 and add a floor line if the model dropped
it. Use it for every standing move: without it the squat feet slid 30 px (5 % of the cell) per cycle.

### 5. Film (free)
Copy `scripts/player.html` next to the frames folder, then:
```bash
node scripts/shoot.cjs "player.html?dir=all&seq=$(python3 -c 'import urllib.parse,json;print(urllib.parse.quote(json.dumps(SEQ)))')&z1=1.12&ax=500&ay=600&pop=22" clip_4k.mp4 --scale 2
```
- `seq=[[frame, holdFrames], ...]` at 30 fps. Ease in/out: longer holds at the start and end of a
  move (3), 2 in the middle; hold the first pose ~20 and the peak ~45.
- Cycles: `rep=[[0,10],[1,3],...,[8,5],[7,2],...,[0,4]]&reps=3&tail=20` (push-up: slow down, fast up).
- Camera: slow push-in `z0=1&z1=1.1` anchored on the action (`ax`,`ay` in cell px), optional pan
  `cx`→`cx2`, `pop=<frame>` punch at a peak. The view never shows a frame's cut edge.
- Full body on a floor: anchor the zoom on the floor (`ay`=floor y, `ax`=`cx`=figure centre) and keep
  `z` near 1 (e.g. `z0=0.96&z1=1.04`); a push-in on the hips cuts the head and the floor off. Squat
  timing that read well: `rep=[[0,10],[1,4],[2,3],[3,3],[4,3],[5,3],[6,4],[7,12],[6,3],[5,2],[4,2],[3,2],[2,2],[1,3]]`.
- `--scale 2` = 3840×2160. Use `--still 1.0 --scale 2` for a single 4K PNG to inspect.

### 6. Critique (3 rounds, free)
Tile every frame (`ffmpeg -i clip.mp4 -vf "select='not(mod(n\,3))',scale=480:-1,tile=6x5" -frames:v 1 t.png`)
and review as a film critic with `references/critique.md`. Fix with sequence/camera/slicing changes
first; regenerate an image only for drawing errors. Report what was fixed and what remains.

## Delivering
Give the user the final MP4 (attach the file), a before/after comparison when something changed, the
critique list, and the image cost (count calls × price in `references/costs.md`).
