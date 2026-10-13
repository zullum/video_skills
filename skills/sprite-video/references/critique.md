# Film-critic checklist

Review EVERY frame (tile the video, 1 tile per 2–3 frames), not a few keyframes. Run three rounds:
look, list problems, fix, render again. Prefer cheap fixes (sequence, camera, slicing) over new images.

| Check | What it looks like | Usual fix |
|---|---|---|
| Size jump between rows | character grows/shrinks at a row change | template with the base in every cell; `slice.py --anchor` |
| Shake / jitter | head or feet move a few px between frames | `--anchor` on a still head; cell-locked slicing; no per-frame rescaling |
| Floating torso | body cut above the screen bottom ("no legs") | camera never shows the cell's cut edge (player clamps automatically); zoom anchored above it |
| Visible crop boxes | lighter/darker rectangles around the figure | recolour near-background fills (`merge.py`/`trace2.py` do it); same background everywhere |
| Missing in-betweens | limb snaps to a new angle | guided in-between sheet (red line + circle) |
| Sheet switch boil | body details change when frames come from another sheet | switch sheets during motion, drop duplicate held frames |
| Detached limb | arm separate from the shoulder, gap at the joint | regenerate with "repair the shoulder"; never composite parts from different sheets |
| Wrong mechanics | e.g. push-up elbow only goes back | change the IK guide (elbow flare = shorter upper arm), regenerate that sheet |
| Contact points slide | hands/toes move on the floor | keep the hand box (`keep`), floor drawn by the player; standing moves: `slice.py --ground` |
| Cream stripe inside dark clothes | pale band between the outline and dark gray shorts | fixed in `trace2.py` (dark fills are not ink); re-slice old frames |
| Head or floor cut by the zoom | full-body shot, push-in on the hips | anchor on the floor (`ay`), `z` 0.96–1.04 |
| Motion lines jump | lines appear on different sides frame to frame | use the frames whose lines agree, hold the last one |
| Eye glow / shine lost | white turned cream | keep white in the palette (it is fixed in `slice.py`); don't recolour near-white fills |
| Blur / soft lines | raster upscaling | trace at native size with `trace2.py`, film with `--scale 2` |
| Timing | robotic, even spacing | ease: 3-frame holds at starts/ends of moves, 2 in the middle, long hold on the peak |
| Framing | character jammed in a corner, head cut by zoom | `cx`/`ax`/`ay`, smaller `z1`, check the last frame of the zoom |
