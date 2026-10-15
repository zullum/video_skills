# Scene catalog (2/2): cardWall, exerciseDemo, flyBy, stairs, powerUp, seqRows, document; transitions

## cardWall
**Reference:** a collage of video thumbnails with shouty titles flies in around the figure seen from behind (0:57-1:09).
**Params:** `cards: [{title, fill, asset}]`, `cols=5`, `rows=3`, `area=[60,40,1860,760]`, `fg: {asset, x, y, h}`.
**Actions:** `fill {stagger=.06}` (each card flies in from a seeded offset, ±5° tilt) · `fgIn` · `out`. Add the
generic `push` for the slow push in.
```json
{"id": "s08", "say": "More moves, more programs, more tabs.", "scene": "cardWall", "params": {"cols": 4, "rows": 2,
  "cards": [{"title": "DO THIS", "fill": "accent"}, {"title": "47 WAYS", "fill": "bgLight", "asset": "pushup_pose"}],
  "fg": {"asset": "back", "x": 960, "y": 1080, "h": 520}},
 "beats": [{"at": 0.1, "do": "fill"}, {"at": 0.3, "do": "fgIn"}, {"at": 1.0, "do": "push", "args": {"to": 1.1, "dur": 2}}]}
```

## exerciseDemo (+ muscleInsets)
**Reference:** each exercise on a flat light background (3:42-4:27, 5:24-5:39): the figure loops its rep on a soft
floor shadow, a prop behind it (box, bar), a callout ring draws round the hands or feet, a double arrow shows the
range, a "2×12 / 3/WEEK" tag top left; on the push-up close-up muscle circles pop around it while it keeps repping.
This is the one place with frame-by-frame animation: a sprite (≤24 frames from one Nano Banana sheet).
**Params:** `sprite`, `x=960`, `y=900` (floor), `h=600` (cell height), `rep: [[frame, holdFrames], …]`,
`reps="fill"|n|"beats"`, `start=0`, `prop: {asset, x, y, h}`, `shadow=true`, `anchor`.
**Actions:** `reps {n, rep}` (with `reps: "beats"`) · `callout {x, y, r=90}` (snap) · `arrow {x0, y0, x1, y1}` (tick)
· `tag {lines=["2x12","3/WEEK"], x=230, y=110}` (tick) · `insets {items: [{asset, x, y, r, zoom=2.2, fx=.5, fy=.35}],
stagger=.2}` (pops; a magnified crop of any asset, so a muscle close-up needs no extra image) · `out`.
```json
{"id": "s10", "say": "Push-ups: hands under shoulders, chest to the floor.", "scene": "exerciseDemo", "in": "zoomIn",
 "params": {"sprite": "pushup", "y": 880, "h": 620, "rep": [[0, 2], [6, 2], [12, 2], [18, 2], [23, 6], [18, 2], [12, 2], [6, 2], [0, 8]]},
 "beats": [{"at": "word:hands", "do": "callout", "args": {"x": 700, "y": 820, "r": 90}}, {"at": "word:floor", "do": "tag"}]}
```

## flyBy
**Reference:** a satellite with a "15 MIN" clock badge crosses the day columns (0:06); rockets launch upward with
flickering white exhaust (4:33-4:54); a small rocket streaks along the bottom (6:15).
**Params:** `asset`, `h=260`, `path=[[x,y],…]`, `rot0` (the asset's own heading: −90 = points up; set it to turn the
object along its path), `flame=true`, `badge: {text, r=70}`.
**Actions:** `fly {dur=1.6, path, ease}` (whoosh) · `launch {dur=1.2}` (whoosh; rises from below the frame) · `badge` · `out`.
```json
{"id": "s03", "say": "Fifteen minutes a session.", "scene": "flyBy", "params": {"asset": "satellite", "h": 300, "flame": false,
  "path": [[-200, 700], [2100, 300]], "badge": {"text": "15 MIN"}},
 "beats": [{"at": 0, "do": "fly", "args": {"dur": 2.6}}, {"at": "word:fifteen", "do": "badge"}]}
```

## stairs
**Reference:** a staircase of progressions (5:15-5:21): the figure on the top step, equipment on the lower steps.
**Params:** `steps=4`, `dir="down"|"up"`, `x0=120`, `x1=1800`, `ytop=520`, `ybot=900`, `items: [{asset, step, dx, h, flip}]`.
**Actions:** `build {stagger=.15}` (tick per step) · `place {items, stagger=.12}` (pops) · `out`.
```json
{"id": "s14", "say": "Same moves, just harder, month after month.", "scene": "stairs", "params": {"dir": "up",
  "items": [{"asset": "stand", "step": 3, "h": 300}, {"asset": "box", "step": 0, "h": 120}]},
 "beats": [{"at": 0.1, "do": "build"}, {"at": "word:harder", "do": "place"}]}
```

## powerUp
**Reference:** a dark flame aura flares behind the figure as it drops to the floor (3:03-3:09, 4:00); the frame
freezes grey under a pause badge ("Quick pause", 3:12); lightning bursts round the phone ("Go bananas", 3:15).
**Params:** `target: {asset | sprite, x, y, h, rep}`, `color="bgDeep"`, `color2="bgLight"`.
**Actions:** `ignite` (shimmer; the aura cycles 3 variants every 0.1 s) · `burst {n=8}` (impact; bolts + glow +
shake) · `freeze {x, y, r=150}` (stamp; grey + pause badge, keep it off the face) · `rays` · `off`.
```json
{"id": "s16", "say": "Start today.", "scene": "powerUp", "in": "flash", "params": {"target": {"asset": "hips", "x": 960, "y": 1000, "h": 720}},
 "beats": [{"at": "word:start", "do": "ignite"}]}
```

## seqRows
**Reference:** "this exercise → harder variation" rows with a set badge (6:27-6:48).
**Params:** `rows: [{from: {asset|sprite}, to: {…}, tag}]`, `r=70`, `x0=640`, `x1=1280`.
**Actions:** `show {rows, stagger=.2}` (pops) · `tag {rows}` · `out`.
```json
{"id": "s13", "say": "When the top of the range feels easy, add one rep.", "scene": "seqRows", "params": {"rows": [
  {"from": {"asset": "pushup_pose"}, "to": {"asset": "pushup_pose"}, "tag": "2x12"}]},
 "beats": [{"at": "word:easy", "do": "show"}, {"at": "word:rep", "do": "tag"}]}
```

## document
**Reference:** a guide's cover slides in, then spreads with headings, text and figures (0:36-0:42, 6:57-7:12). Always
our own generic guide, never a copy of a real book.
**Params:** `pages: [{kind: "cover", title, subtitle, asset}, {kind: "spread", heading, lines=12, figures: [asset…]}]`.
**Actions:** `in {i=0}` · `flip {to}` (whoosh) · `out`.

## Transitions and generic actions
`"in"` on a shot: `cut` (default), `pop` (pop), `zoomIn` (pairs with the previous shot's `zoom`; when that shot has
none, build.py adds a `zoomInto` to the frame centre), `whip` (whoosh at the cut; build.py makes the previous shot
whip out), `flash` (impact; the previous shot flashes out).
Generic actions on any scene: `push {x, y, to=1.12, dur=1.2}` · `zoomInto {x, y, scale=6, dur=.5}` ·
`flash {color}` · `shake {amp=8}` · `fadeOut {dur=.3}`.

## A beat no template covers
Write a one-off scene in the project: `assets/js/scenes/<name>.js`, first line `// @scene <name> @actions a,b`,
`TOON.scene.<name> = {build, idle?, actions}` like the ones in `lib/scenes/`. build.py's registry reads the project's
scenes too and never overwrites them. Rules that cost a debug round once:
- tween HTML boxes (`TOON.box`, `TOON.item`, layers), not SVG groups: GSAP `scale` with `svgOrigin` on a full-frame
  SVG `<g>` rendered nothing;
- an element is hidden before its pop because `fromTo` renders its start state at once; anything never popped is
  visible from frame 0;
- never set a CSS `transform` on an element GSAP also scales or moves (put the rotation on a child);
- no `Math.random`, `Date` or CSS animations: `TOON.rng(TOON.hash(id))` and the timeline only;
- mark decorative layering with `data-layout-allow-overlap` / `data-layout-allow-overflow`, and keep `hf check` at 0 errors.
