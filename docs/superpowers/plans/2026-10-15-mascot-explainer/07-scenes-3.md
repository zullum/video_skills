# 07 Scenes 3 (Tasks 20-25)

Same cycle as before. Each probe below is written as `t kind args`; put them in `tests/gallery/probes.json`.

### Task 20: `crowd`

**Reference beat:** rows of lavender silhouettes in front of the jam tables, "?" thought bubbles over their heads,
then "$" coins over the buyers (1:46-2:00).

**Header:** `// @scene crowd @actions think,coins,clear,out`. **Params:** `{tone="light", asset, n=7, y=1080, h=520}`.
Build: flat background; back row of `n-1` figures (h × .88, opacity .55, half a spacing to the right, 40 px higher)
and a front row of `n` figures at `x_k = W/(2n) + k·W/n`, seeded height ±4 %, every other one flipped; a figure's
head point is `(x_k, top + .07h)` where `top` is its box top (works for any anchor). Actions: `think {symbol="?",
heads=[k…], stagger=.1}` pops `shape.think` (r = max(44, .2h)) centred at `(x_k, top - r - 20)`; `coins {heads,
stagger}` the same with `shape.coin`; `clear` (all symbols out); `out`.

- [ ] **Step 1:** `cr` (dur 1.8, `{"asset":"blob","n":5,"y":700,"h":200}`, think at .3 heads [0,1,2,3,4]): t .1
  `noarea [916,492,88,88] #FFFFFF max .01`; t 1.2 `area [916,492,88,88] #FFFFFF min .3`.
- [ ] **Steps 2-5:** FAIL → `lib/scenes/crowd.js` → PASS + look → commit `mascot-explainer: crowd scene`.

### Task 21: `phone`

**Reference beat:** a hand holds a phone into frame (0:15, 0:48, 7:17): a vertical feed scrolls, bookmark icons
fly out around it (0:57), an app screen glows (3:13), a video plays with a heart (0:50).

**Header:** `// @scene phone @actions scroll,icons,swipe,out`. **Params:** `{tone="mid", hand?: asset, x=960, y=560,
h=900, rot=0, screen: {kind: "feed"|"app"|"video"|"color", color, title, asset, cards}, icons?: {n=8}}`.
Build: with `hand` (a traced asset whose manifest `holes[0]` is the screen), the screen div sits *behind* the image
at the hole rect (fractions × the image box); without it, a code-drawn phone (rounded rect w = .48h, ink 12 px,
black bezel, screen inset 18 px, notch). Screen kinds: `feed` = a column of `shape.card`s 14 px apart; `app` =
accent header bar + TDisplay title + asset + rounded button; `video` = asset + red progress bar + heart; `color` =
a flat fill. Actions: `scroll {dist=600, dur=1.2}` (feed y); `icons {n=8, stagger=.06}` (`shape.bookmark`s fly from
the phone centre to a ring of radius .6h with spin and pop); `swipe {dir="left"}`; `out`.

- [ ] **Step 1:** `ph` (dur 1.6, `{"x":960,"y":540,"h":800,"screen":{"kind":"color","color":"accent"}}`, icons at .3):
  t .5 `px 960,540 accent tol 30`; t 1.4 `area [0,0,1920,1080] #FFFFFF min .004`. `ph2` (dur 1.0, `{"hand":"ring",
  "x":960,"y":540,"h":400,"screen":{"kind":"color","color":"accent"}}`): t .5 `px 960,540 accent tol 40` (content
  shows through the traced hole).
- [ ] **Steps 2-5:** FAIL → `lib/scenes/phone.js` → PASS + look → commit `mascot-explainer: phone scene`.

### Task 22: `cardWall`

**Reference beat:** a collage of video thumbnails with shouty titles flies in around the figure seen from behind
(0:57-1:15), then a slow push in.

**Header:** `// @scene cardWall @actions fill,fgIn,out`. **Params:** `{tone="deep", cards: [{title, fill, asset?}],
cols=5, rows=3, area=[60,40,1860,760], fg?: {asset, x, y, h}}`. Build: background; card slots on the grid with seeded
jitter (±30 px, ±5°); `shape.card`s hidden; `fg` figure in front at the bottom. Actions: `fill {stagger=.06}` (each
card flies in from a seeded offset (±400, ±300) at scale .6 to its slot and angle, .45 s power3.out);
`fgIn` (fg rises 300 px, .5 s power3.out); `out`. Use the generic `push` for the slow push in.

- [ ] **Step 1:** `cw` (dur 2.0, 6 cards `{"title":"DO THIS","fill":"accent"}`, cols 3 rows 2, fill at .2):
  t .1 `noarea [60,40,1800,720] accent max .01`; t 1.6 `area [60,40,1800,720] accent tol 40 min .15`.
- [ ] **Steps 2-5:** FAIL → `lib/scenes/wall.js` → PASS + look → commit `mascot-explainer: cardWall scene`.

### Task 23: `stairs`

**Reference beat:** a staircase of progressions: the figure stands on the top step, equipment (rings, parallettes)
sits on lower steps, a small figure with the "2×12" ball at the bottom (5:05-5:20).

**Header:** `// @scene stairs @actions build,place,out`. **Params:** `{tone="light", steps=4, dir="down", x0=120,
x1=1800, ytop=520, ybot=900, items: [{asset, step, dx=0, h}]}`. Build: flat background; step k is a `panel` rect
`(x1-x0)/steps` wide whose height falls from `ybot-ytop` to `(ybot-ytop)/steps` (`dir="up"` mirrors), top edge ink
5 px, `transform-origin: bottom`, scaleY 0; items stand on their step's top (feet anchor). Actions:
`build {stagger=.15}` (each step grows .35 s back.out); `place {items, stagger=.12}` (pop); `out`.

- [ ] **Step 1:** `st` (dur 1.8, steps 4, build at .2): t .1 `noarea [120,860,1680,30] panel max .05`; t 1.4
  `px 330,895 panel tol 30` and `px 1590,895 panel tol 30`.
- [ ] **Steps 2-5:** FAIL → `lib/scenes/stairs.js` → PASS + look → commit `mascot-explainer: stairs scene`.

### Task 24: `seqRows`

**Reference beat:** rows of "this exercise → harder variation" with a set badge (6:24-6:40, 3×12 → …).

**Header:** `// @scene seqRows @actions show,tag,out`. **Params:** `{tone="mid", rows: [{from: {asset|sprite},
to: {…}, tag}], r=70, x0=640, x1=1280}`. Layout: row i at `y_i = 540 + (i - (n-1)/2)·(2r + 50)`; a bubble at x0, a
`shape.arrow` from `x0 + r + 20` to `x1 - r - 20` (pathLength 1), a bubble at x1, a badge (white disc .32r, ink,
TDisplay text) at `(x0 + .75r, y_i - .75r)`. Actions: `show {rows, stagger=.2}` (per row: pop the first bubble,
draw the arrow over .3 s, pop the second at +.3 s); `tag {rows}` (badges pop); `out`.

- [ ] **Step 1:** `sr` (dur 1.8, two rows of blob → blob, show at .2 rows [0,1]): t .1 `noarea [570,350,780,380]
  #FF7A59 max .001`; t 1.5 `px 640,480 #FF7A59 tol 60` and `px 1280,600 #FF7A59 tol 60`.
- [ ] **Steps 2-5:** FAIL → `lib/scenes/rows.js` → PASS + look → commit `mascot-explainer: seqRows scene`.

### Task 25: `document`

**Reference beat:** a playbook cover slides in, then page spreads with headings, text and figures (0:26-0:33,
6:57-7:10). Our version is a code-built generic guide, never a copy of the reference's book.

**Header:** `// @scene document @actions in,flip,out`. **Params:** `{tone="deep", pages: [{kind: "cover", title,
subtitle, asset}, {kind: "spread", heading, lines=12, figures: [asset…]}]}`. Build: pages are white boxes with a soft
CSS shadow, centred at (960, 540): a cover is 560 × 760 (TDisplay ink title up to 3 lines at 92 px, TLabel subtitle,
asset figure); a spread is 1100 × 760 split in two halves (TDisplay 40 px heading, seeded grey text-line rects in
`bgLight` at .5 opacity, figure images). Actions: `in {i=0}` (pop with rotation 6°→−2°, .5 s back.out);
`flip {to}` (current page to x −900 / −12° in .45 s power2.in, next from x +900 / 8° to its place in .5 s power3.out);
`out`.

- [ ] **Step 1:** `dc` (dur 2.4, a cover "THE GUIDE" + a spread with the blob as figure; in at .1, flip at 1.0
  `{"to":1}`): t .7 `area [700,200,520,680] #FFFFFF min .5`; t 2.0 `area [460,180,1000,700] #FFFFFF min .5`.
- [ ] **Steps 2-5:** FAIL → `lib/scenes/doc.js` → PASS + look → commit `mascot-explainer: document scene`.
- [ ] **Step 6:** full `bash scripts/selftest.sh --render` green: every probe passes, `hf check` 0 errors, the draft
  render's length matches. Read the gallery contact sheet (`snapshots/contact-sheet.jpg`).
