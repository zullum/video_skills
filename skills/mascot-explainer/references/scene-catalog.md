# Scene catalog (1/2): space, bubbles, windowRoom, days, textSlam, shelf, crowd, phone

Every shot in `shots.json` names one scene and lists beats. A beat is `{"at", "do", "args"}`; `do` is one of the
scene's actions (below) or a generic one (`push`, `zoomInto`, `flash`, `shake`, `fadeOut`, part 2). Sounds come
from the actions automatically (the name in brackets). Times in "Reference" point into the analysed video
(`reference-video.md`). Coordinates are composition pixels (1920×1080). Every scene also takes `push` (idle camera
push-in, default 1.03, `0` = off), `tone` (`deep` | `mid` | `light`: which background colour) and most take
`flat: true` (no sparkles). An item that a `pop`-like beat lists stays hidden until that beat; everything else is
on screen from the first frame.

## space
**Reference:** under almost every early shot (0:00-0:10, 2:21, 4:33): one deep tone, white 4-point sparkles twinkling.
**Params:** `density` (36). **Actions:** `title {text, size=110, x, y}` (pop).
`TOON.backdrop(parent, tone, ctx, density)` draws this background for every other scene.
```json
{"id": "s04", "say": "That's the whole plan.", "scene": "space", "beats": [{"at": "word:whole", "do": "title", "args": {"text": "THE WHOLE PLAN"}}]}
```

## bubbles (+ zoomThrough)
**Reference:** the three exercises pop in as planets, one per spoken word (0:00-0:06); many small ones swarm (0:48,
2:24, 7:30); one glows with rays while the others grey out (3:36); the camera dives into it and its exercise is
the next shot (3:39).
**Sees:** a pale disc with a crater or stripe texture, a white rim, the figure inside; each floats ±6 px.
**Params:** `items: [{asset | sprite, x, y, r, texture: "craters"|"stripes", rep, h}]` (a feet-anchored pose stands
at the bottom of the disc; a sprite loops `rep`).
**Actions:** `pop {items, stagger=.12}` (pop) · `highlight {i, color="accent", dimOthers=true}` (shimmer) ·
`dim {items}` · `undim` · `zoom {i, scale=7, dur=.6}` (whoosh; give the next shot `"in": "zoomIn"`) ·
`swarm {n=24, rmin=26, rmax=50, stagger=.04}` (pops) · `out {items, stagger}`.
**Assets:** one pose per exercise or a sprite per exercise.
```json
{"id": "s01", "say": "Push-ups. Squats. Two sets each.", "scene": "bubbles", "params": {"items": [
  {"sprite": "pushup", "rep": [[0, 6], [8, 6]], "x": 620, "y": 520, "r": 190}, {"asset": "squat_pose", "x": 1300, "y": 520, "r": 190}]},
 "beats": [{"at": "word:push-ups", "do": "pop", "args": {"items": [0]}}, {"at": "word:squats", "do": "pop", "args": {"items": [1]}},
           {"at": "end-0.6", "do": "zoom", "args": {"i": 0}}]}
```

## windowRoom
**Reference:** the spaceship interior (0:24-0:30, 0:51, 6:06, 7:33): a wide window with a faint grid on the glass,
lit panels on the sill, angled side walls, bubbles floating behind the glass, an astronaut seen from behind in the
lower right corner.
**Params:** `window=[200,70,1720,740]`, `grid=72`, `items` (frame coordinates, inside the window), `fg: {asset, x, y, h, flip}`.
**Actions:** `pop` · `highlight` · `dim` · `swarm` (inside the glass) · `fgIn {from="right"}` · `out`.
**Assets:** the over-the-shoulder astronaut pose.
```json
{"id": "s05", "say": "So why does it feel like too little?", "scene": "windowRoom", "params": {"items": [
  {"asset": "squat_pose", "x": 960, "y": 380, "r": 120}], "fg": {"asset": "astro", "x": 1640, "y": 1080, "h": 520}},
 "beats": [{"at": 0.2, "do": "fgIn"}, {"at": "word:feel", "do": "swarm", "args": {"n": 30}}]}
```

## days
**Reference:** MON | WED | FRI (0:04-0:08, 5:48-5:57, 7:36): white separators draw down, the labels drop in, the same
bubbles appear in each column, then "2×12 / 3/WEEK" tags pop beside them.
**Params:** `labels=["MON","WED","FRI"]`, `items: [{asset|sprite, dx, dy, r}]` (relative to each column centre), `labelY=70`, `labelSize=72`.
**Actions:** `split {stagger=.2}` (whoosh) · `fill {cols, stagger=.15}` (pop per column) · `tag {lines, cols, size=30}` (tick) · `out`.
```json
{"id": "s02", "say": "Monday, Wednesday, Friday.", "scene": "days", "params": {"items": [{"asset": "pushup_pose", "dy": 60, "r": 110}]},
 "beats": [{"at": 0.1, "do": "split"}, {"at": "word:friday", "do": "fill", "args": {"cols": [0, 1, 2]}}]}
```

## textSlam
**Reference:** "THE FIX NOBODY'S SELLING YOU" (2:21), "SATISFICING" / "MAXIMISING" over the figure (2:33-2:45),
"THE WEEKLY STRUC…" typing on (5:45).
**Params:** `text`, `size=150`, `x`, `y`, `color="text"`, `sub: {text, size=64}`.
**Actions:** `slam {stagger=.12}` (impact; words punch in from 1.6× with a small shake) · `type {cps=16}` (blip) · `sub` · `out`.
```json
{"id": "s09", "say": "Your first win isn't volume. It's showing up.", "scene": "textSlam",
 "params": {"text": "SHOWING UP"}, "beats": [{"at": "word:showing", "do": "slam"}]}
```

## shelf
**Reference:** the jam study (1:42-2:05): 6 jars, then a 24-jar pyramid, a split screen comparing both tables, a
small citation label bottom right.
**Params:** `item`, `itemH=110`, `shelfY=780`, `counts=[6,24]`, `citation`.
**Actions:** `fill {set=0, count, stagger=.04}` (pops) · `clear {set}` · `split` (whoosh: divider draws, set 0
moves left, set 1 lives on the right) · `cite` (tick) · `out`.
```json
{"id": "s06", "say": "Six options or twenty-four?", "scene": "shelf", "params": {"item": "jar", "citation": "Iyengar & Lepper, 2000"},
 "beats": [{"at": 0.1, "do": "fill", "args": {"set": 0}}, {"at": "word:twenty-four", "do": "split"},
           {"at": "word:twenty-four+0.3", "do": "fill", "args": {"set": 1, "stagger": 0.02}}, {"at": "end-0.8", "do": "cite"}]}
```

## crowd
**Reference:** rows of silhouettes in front of the tables, "?" bubbles over their heads, then "$" coins (1:46-2:03).
**Params:** `asset` (a silhouette), `n=7`, `y=1080`, `h=520`. A back row of `n-1` lighter figures sits behind.
**Actions:** `think {symbol="?", heads, stagger=.1}` (pop) · `coins {heads}` (chime; replaces the "?" on that head) · `clear` · `out`.
```json
{"id": "s06b", "say": "Most people never even start.", "scene": "crowd", "params": {"asset": "person", "n": 6},
 "beats": [{"at": "word:people", "do": "think", "args": {"heads": [0, 1, 2, 3, 4, 5]}}]}
```

## phone
**Reference:** a hand holds a phone into frame (0:15, 1:21-1:30, 7:15): a feed scrolls, bookmarks fly out around it,
an app screen, a video with a heart.
**Params:** `hand` (a traced hand-with-phone asset; its manifest `holes[0]` is the screen) or none (code-drawn phone),
`x`, `y`, `h=900`, `rot`, `screen: {kind: "feed"|"app"|"video"|"color", color, title, asset, cards: [{title, fill, asset}]}`.
**Actions:** `scroll {dist=600, dur=1.2}` · `icons {n=8, stagger=.06}` (pops) · `swipe {dir}` · `out`.
```json
{"id": "s07", "say": "Every app sells you more.", "scene": "phone", "params": {"hand": "handphone", "h": 980, "y": 600,
  "screen": {"kind": "feed", "cards": [{"title": "47 WAYS", "fill": "accent"}, {"title": "NO GYM", "fill": "bgLight"}]}},
 "beats": [{"at": 0.2, "do": "scroll", "args": {"dist": 500}}, {"at": "word:more", "do": "icons"}]}
```
