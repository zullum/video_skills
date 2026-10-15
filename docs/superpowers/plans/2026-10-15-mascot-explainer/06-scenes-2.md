# 06 Scenes 2 (Tasks 16-19)

Same cycle as `05-scenes-1.md`: gallery shots + probes → selftest `--only` FAIL → write the scene → PASS → Read the
snapshots → commit. Code shapes come from `toon-shapes.js`; items/bubbles from `TOON.bubbleKit`.

### Task 16: `exerciseDemo` (+ muscleInsets)

**Reference beat:** the exercise on a flat lavender background (3:40-4:25, 5:27): the figure loops its rep on a
soft floor shadow, a prop (box, bar) behind it, a callout circle draws round the hands/feet, a double arrow grows to
show the range of motion, a "2×12 / 3/WEEK" tag pops top-left; for the push-up close-up, muscle inset circles pop
around the figure while it keeps repping (5:27).

**Header:** `// @scene exerciseDemo @actions reps,callout,arrow,tag,insets,out`.
**Params:** `{tone="mid", sprite, x=960, y=900 (floor), h=600 (cell height on screen), rep: [[f, hold], …],
reps="fill"|n, start=0, prop?: {asset, x, y, h}, shadow=true}`.
Build: flat full-frame `bg<Tone>` (no sparkles); shadow ellipse (ink, opacity .12, rx = .28 × cell width on screen,
ry 13) at `(x, y)`; prop image behind; `TOON.sprite(…, {x, y, h})`; an SVG overlay and an HTML overlay on top.
Idle: when `rep` is set, `playReps(start → dur)` (`"fill"`) or n cycles.
Actions: `reps {n, rep?}` (explicit cycles from t); `callout {x, y, r}` (`shape.callout` + `draw` .4 s);
`arrow {x0, y0, x1, y1}` (`shape.doubleArrow`, drawn over .5 s); `tag {lines=["2x12","3/WEEK"], x=230, y=110}`
(`shape.tag` pop); `insets {items: [{asset, x, y, r, zoom=2.2, fx=.5, fy=.35}], stagger=.2}` — each a
`shape.bubble` (no texture) whose content shows the asset magnified `zoom`× with its point `(fx, fy)` centred, so a
muscle close-up needs no extra image; `out`.

- [ ] **Step 1: Gallery + probes** (sprite `tick` = red frame 0 / blue frame 1, frames at cell `[20,20,160,160]`):

```json
{"id": "ed", "dur": 2.0, "scene": "exerciseDemo", "params": {"sprite": "tick", "x": 960, "y": 800, "h": 400,
 "rep": [[0, 15], [1, 15]], "reps": "fill"}, "beats": [{"at": 0.2, "do": "callout", "args": {"x": 960, "y": 600, "r": 220}},
 {"at": 0.5, "do": "tag", "args": {"lines": ["2x12", "3/WEEK"], "x": 1400, "y": 300}},
 {"at": 0.9, "do": "insets", "args": {"items": [{"asset": "blob", "x": 1500, "y": 750, "r": 110}]}}]}
```

Probes: t .25 `px 960,600 #E63946 tol 50`; t .75 `px 960,600 #3A86FF tol 50`; t 1.25 `px 960,600 #E63946 tol 50`
(the loop restarts); t 1.0 `notpx 960,380 bgMid tol 20` (callout stroke); t 1.0 `area [1300,230,220,150] #FFFFFF
min .3` (tag); t 1.6 `px 1500,750 #FF7A59 tol 60` (inset, magnified blob).
- [ ] **Steps 2-5:** FAIL → write `lib/scenes/demo.js` → PASS + look → commit `mascot-explainer: exerciseDemo scene`.

### Task 17: `flyBy`

**Reference beat:** a satellite with a "15 MIN" clock badge crosses the MON/WED/FRI frame (0:06); rockets with a
logo launch upward with flickering white exhaust (4:39-4:57); a small rocket streaks along the bottom (5:15).

**Header:** `// @scene flyBy @actions fly,launch,badge,out`. **Params:** `{tone="deep", asset, h=260,
path=[[x,y], …], rot0=0 (the asset's own heading in degrees, e.g. −90 for a rocket pointing up), flame=true,
badge?: {text, r=70}}`. Build: backdrop; `TOON.item` centred on `path[0]`; flame group (three `shape.flame` tongues
in `rim`/`accent`, behind, at the tail) flickering scaleY .8↔1.2 every 2 frames from 0 to dur (finite repeat);
badge = white disc + ink border + TDisplay text, child of the item. Actions: `fly {dur=1.6, ease="power1.inOut"}`
— GSAP `keyframes` over the path offsets, segment time ∝ segment length, `rotation = heading - rot0` per
segment when `rot0` is set, `filter: blur(1.5px)` while moving; `launch {dur=1.2, to?}` (from below the frame up
to its place, power2.out, flame scaleY 0.4→1.4); `badge` (pop); `out`.

- [ ] **Step 1: Gallery + probes:** `fb` (dur 2.0, `{"asset":"blob","h":160,"path":[[200,540],[1700,540]]}`, fly at
  .2 `{"dur":1.4}`): t .1 `px 200,540 #FF7A59 tol 50`; t 1.8 `px 1700,540 #FF7A59 tol 50` and `px 200,540 bgDeep tol 30`.
- [ ] **Steps 2-5:** FAIL → write `lib/scenes/fly.js` → PASS + look → commit `mascot-explainer: flyBy scene`.

### Task 18: `powerUp`

**Reference beat:** a dark flame aura flares up behind the figure as it hits the floor (3:00, 3:57); a pause badge
freezes a grey frame ("Quick pause", 3:12); yellow lightning bursts around the phone ("Go bananas", 3:15).

**Header:** `// @scene powerUp @actions ignite,burst,freeze,rays,off`. **Params:** `{tone="mid", target: {asset|sprite,
x, y, h, rep?}, color="bgDeep", color2="bgLight"}`. Build: flat background; aura SVG behind the target with three
`shape.flame` variants (seeds 1-3, base at the target's bottom, width 1.3h, height 1.5h) all hidden; the target;
an overlay for bolts, rays and the pause icon.
Actions: `ignite` — aura scales up from its base (.3 s back.out) then the visible variant cycles every .1 s to the
end of the shot (`tl.set` opacity steps); `burst {n=8}` — `shape.bolt`s radiating from the target centre (length
300-520 px, seeded), visible on/off 3 × in .3 s, an accent glow flash and `shake`; `freeze` — cam filter
`grayscale(1) brightness(.85)` set at t and `shape.pauseIcon` (r 150) pops at the centre; `rays` — rotating
`shape.rays` behind the target; `off` — aura out.

- [ ] **Step 1: Gallery + probes:** `pu` (dur 2.0, target `{"asset":"blob","x":960,"y":540,"h":300}`, ignite at .3):
  t .2 `noarea [860,300,200,80] bgDeep tol 30 max .02`; t 1.2 `area [860,300,200,80] bgDeep tol 30 min .3`. `pz` (dur 1.5, same target, freeze at .3): t 1.0 `area [880,460,160,160] #FFFFFF min .1`.
- [ ] **Steps 2-5:** FAIL → write `lib/scenes/power.js` → PASS + look → commit `mascot-explainer: powerUp scene`.

### Task 19: `shelf`

**Reference beat:** the jam study (1:42-2:05): jars on a shelf, 6 then 24 in a pyramid, a split screen comparing
the two tables, crowds of shoppers above them (that part is `crowd`), and a small citation label bottom-right.

**Header:** `// @scene shelf @actions fill,clear,split,cite,out`. **Params:** `{tone="light", item, itemH=110,
shelfY=780, counts=[6,24], citation?}`. Build: flat background; shelf board (`panel`) between two ink lines (6 px)
at `shelfY` and `shelfY + 70`; for each set a pyramid laid out from the shelf up (≤8 per row, each row up by
.82 itemH and shifted half an item; set 0 centred, or the left half after `split`); citation card at bottom-right
(white, ink 3 px, TLabel 22 px ink text) hidden.
Actions: `fill {set=0, stagger=.04}` (pops `counts[set]` items; the event count follows `count`); `clear {set}`;
`split` (a vertical ink divider draws down the middle, set 0 moves left, set 1 fills the right half); `cite`
(card pops); `out`.

- [ ] **Step 1: Gallery + probes:** `sh` (dur 2.5, `{"item":"blob","itemH":90,"counts":[6,24],"citation":"Author et
  al., Journal, 2000"}`, fill at .2 `{"set":0,"count":6}`, cite at 1.0): t .1 `noarea [400,560,1100,240] #FF7A59
  max .001`; t 1.0 `area [400,560,1100,240] #FF7A59 min .03`; t 2.0 `area [1450,1000,460,60] #FFFFFF min .3`.
- [ ] **Steps 2-5:** FAIL → write `lib/scenes/shelf.js` → PASS + look → commit `mascot-explainer: shelf scene`.
- [ ] **Step 6:** full `bash scripts/selftest.sh` green.
