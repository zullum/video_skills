# 04 Runtime (Tasks 9-11)

Browser code lives in `skills/mascot-explainer/lib/`. It cannot be unit-tested in Python, so its tests are the
gallery probes of Task 11: snapshot a frame, check pixels. Tasks 9-10 are verified through Task 11's first run.

### Task 9: toon-core.js and toon-shapes.js

**Files:** Create `lib/toon-core.js`, `lib/toon-shapes.js`, `lib/fonts/{BarlowCondensed-ExtraBoldItalic.woff2,Barlow-Bold.woff2,OFL.txt}`

**Interfaces (Produces, used by every scene):**
- `TOON.init(style, manifest)`, `TOON.c(role) -> hex` (palette role or the string itself), `TOON.rng(seed) -> () => [0,1)`
  (mulberry32), `TOON.hash(str) -> uint32` (FNV-1a), `TOON.el(tag, attrs, parent)` (SVG namespace for SVG tags;
  attrs `style`/`text` special), `TOON.layer(parent)` (full-frame div), `TOON.svg(parent, w, h)`,
  `TOON.box(parent, x, y, w, h, ax=.5, ay=.5)` (div whose anchor sits at x,y; transform-origin at the anchor),
  `TOON.item(parent, x, y, w, h, ax, ay) -> {el, inner}` (pop/fly on `el`, bob on `inner`, content in `inner`),
  `TOON.img(parent, asset, {x, y, h|w, anchor?, flip?}) -> box`, `TOON.text(parent, str, {x, y, size, font:
  "display"|"label", color, align: "center"|"left", upper=true}) -> div`.
- Motion: `TOON.pop(tl, el, t, {dur=.35, blur=6, back=1.6})` (fromTo scale 0→1, opacity 0→1, blur→0, `back.out`;
  the element is hidden before t), `TOON.out(tl, el, t, {dur=.25, scale=.6})`, `TOON.bob(tl, el, t0, t1, {amp=6,
  period=3.6})` (finite yoyo), `TOON.draw(tl, el, t, dur=.4)` (needs `pathLength="1" stroke-dasharray="1"`).
- `TOON.run(id, shot, dur)`: stage `#<id>-stage` → `cam` layer (transitions, `zoomInto`) → `rig` layer (idle push
  1→`params.push` (default 1.03, `0` = off), `push`, `shake`) → scene content; `st = scene.build(rig, params, ctx)`
  gets `cam rig stage dur ctx` added; then `scene.idle`, the `in` transition, every beat in order, the `out`
  transition, and `tl.set({}, {}, dur)`. Unknown scene/action throws with the shot id.
- Transitions: `in` `pop` (cam 1.06→1, .3 s), `zoomIn` (cam 1.35→1, blur 10→0, .45 s, power3.out), `whip` (cam x
  −25 %W→0, blur 24→0, .3 s), `flash` (white overlay 1→0, .35 s); `out` `whip` (cam x→+25 %W, blur→24 in the last
  .22 s, power2.in), `flash` (white 0→1 in the last .12 s).
- Header `// @actions push,zoomInto,flash,shake,fadeOut`: `push {x,y,to=1.12,dur=1.2}` (rig), `zoomInto {x,y,scale=6,
  dur=.5}` (cam, blur→8, power2.in), `flash {color}`, `shake {amp=8}` (6 × 0.04 s), `fadeOut {dur=.3}`.
- Shapes (`TOON.shape`, ids made unique with `TOON.hash(key)`; colours are palette roles):
  `sparkle(svg, x, y, r, fill)` (4-point star: quadratic sides through the centre),
  `bubble(parent, x, y, r, {texture: "craters"|"stripes", fill="panel", mark="bgLight", rim="rim", key}) -> {el, inner, content, r, x, y}`
  (disc, texture clipped to the disc at 45 % opacity, circular `content` div, white rim `max(3, .035r)` on top),
  `rays(parent, x, y, r, {n=12, color="accent", key}) -> box` (radial-gradient glow + n wedges),
  `arrow(svg, x0, y0, x1, y1, {w=8, head=26, color="ink"})`, `doubleArrow(...)`,
  `tag(parent, x, y, lines, {size=34}) -> box` (white card, 4 px ink border, TLabel lines, −3° tilt),
  `callout(svg, x, y, r, {color="bgDeep", w=7}) -> circle` (pathLength 1, for `draw`),
  `flame(svg, cx, base, w, h, seed, {color, color2})` (closed path: 9 tongues, sin-perturbed, two tones),
  `bolt(svg, x0, y0, x1, y1, seed, {color="accent"})` (6-segment zigzag polygon, 10 px wide),
  `think(parent, x, y, r, symbol) -> box` (white disc, ink border, TDisplay symbol, two small trailing dots),
  `coin(parent, x, y, r) -> box` (accent disc, ink border, "$"), `bookmark(svg, x, y, s)`, `pauseIcon(parent, x, y, r)`,
  `card(parent, x, y, w, h, {fill, title, asset, rot}) -> box` (thumbnail card for walls and phone feeds).

- [ ] **Step 1: Fonts.** `curl -fsSLo lib/fonts/BarlowCondensed-ExtraBoldItalic.woff2 https://cdn.jsdelivr.net/fontsource/fonts/barlow-condensed@latest/latin-800-italic.woff2`,
  same for `barlow@latest/latin-700-normal.woff2` → `Barlow-Bold.woff2`, and
  `https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/OFL.txt` → `OFL.txt`. Check each file
  is non-empty (`file` says Web Open Font Format 2).
- [ ] **Step 2: Write `lib/toon-core.js`** per the interface. The run loop:

```js
T.run = function (id, shot, dur) {
  var stage = document.getElementById(id + "-stage"), tl = gsap.timeline({ paused: true });
  var S = T.scene[shot.scene]; if (!S) throw new Error(id + ": unknown scene " + shot.scene);
  var p = shot.params || {}, cam = T.layer(stage), rig = T.layer(cam);
  var ctx = { id: id, dur: dur, tl: tl, rng: T.rng(T.hash(id)) };
  var st = S.build(rig, p, ctx) || {}; st.cam = cam; st.rig = rig; st.stage = stage; st.dur = dur; st.ctx = ctx;
  if (p.push !== 0) tl.fromTo(rig, { scale: 1 }, { scale: p.push || 1.03, duration: dur, ease: "none" }, 0);
  if (S.idle) S.idle(tl, st, dur);
  if (ENTER[shot["in"]]) ENTER[shot["in"]](tl, cam, stage);
  (shot.beats || []).forEach(function (b) {
    var fn = (S.actions || {})[b.do] || T.actions[b.do];
    if (!fn) throw new Error(id + ": " + shot.scene + " has no action " + b.do);
    fn(tl, st, b.t, b.args || {});
  });
  if (EXIT[shot.out]) EXIT[shot.out](tl, cam, stage, dur);
  tl.set({}, {}, dur);
  return tl;
};
```

- [ ] **Step 3: Write `lib/toon-shapes.js`** per the interface (≤200 lines; split `toon-shapes2.js` for
  `think coin bookmark pauseIcon card` if needed — build.py loads every `lib/*.js`, core first).
- [ ] **Step 4: Commit** `mascot-explainer: TOON runtime core and shapes` (verified in Task 11).

### Task 10: toon-sprite.js

**Files:** Create `lib/toon-sprite.js`

**Interfaces (Produces):** `TOON.sprite(parent, name, {x, y, h, anchor?}) -> {el, imgs, cur, k}` (cell scaled to
height `h`; default anchor `[0.5, floor[0]/cell_h]` or `[0.5, 1]`; every frame an `<img>` at its cell x,y,w,h × k,
frame 0 visible); `TOON.show(tl, sp, i, t)` (two `tl.set` opacity calls; frames must be scheduled in time order);
`TOON.playSeq(tl, sp, t0, seq, fps=30) -> t_end` (`seq = [[frame, holdFrames], …]`, sprite-video's format);
`TOON.playReps(tl, sp, t0, t1, rep, fps=30) -> t_end` (whole cycles that fit before t1, then rests on `rep[0][0]`).

- [ ] **Step 1: Write it** (~40 lines):

```js
T.show = function (tl, sp, i, t) {
  if (i === sp.cur) return;
  tl.set(sp.imgs[sp.cur], { opacity: 0 }, t); tl.set(sp.imgs[i], { opacity: 1 }, t); sp.cur = i;
};
T.playSeq = function (tl, sp, t0, seq, fps) {
  var t = t0; fps = fps || 30;
  seq.forEach(function (p) { T.show(tl, sp, p[0], t); t += p[1] / fps; });
  return t;
};
T.playReps = function (tl, sp, t0, t1, rep, fps) {
  fps = fps || 30; var len = rep.reduce(function (s, p) { return s + p[1]; }, 0) / fps, t = t0;
  while (t + len <= t1 + 1e-6) t = T.playSeq(tl, sp, t, rep, fps);
  T.show(tl, sp, rep[0][0], t); return t;
};
```

- [ ] **Step 2: Commit** `mascot-explainer: sprite player` (verified in Task 11 and 16).

### Task 11: Probe harness, selftest, `space` scene

**Files:** Create `scripts/probe.py`, `scripts/selftest.sh`, `tests/make_fixtures.py`, `tests/test_probe.py`,
`tests/gallery/{style.json,shots.json,probes.json,assets/manifest.json,assets/svg/blob.svg,assets/sprites/tick/{f00.svg,f01.svg}}`,
`lib/scenes/space.js`

**Interfaces:**
- `probe.py times PROJECT PROBES [--only ids]` prints the sorted unique global times (`slots[shot] + t`, slots from
  `audio/sfx_cues.json`) joined by commas; `probe.py check PROJECT PROBES SNAPDIR [--only ids]` maps the i-th time to
  `frame-<i:02d>-at-*.png` and prints `PASS`/`FAIL <shot> t=<t> <note>` per probe; exit 1 on any FAIL. Probe kinds:
  `px {x,y,color,tol=40}`, `notpx {x,y,color,tol=40}`, `area {rect:[x,y,w,h],color,tol=40,min=.05}`,
  `noarea {rect,color,tol=40,max=.002}`; colour distance = max channel difference; `color` may be a palette role.
- `selftest.sh [--only ids] [--render]`: pytest → `hf init` a fresh `${SELFTEST_DIR:-/tmp/mx-selftest}` → copy
  `tests/gallery/` in → `make_fixtures.py` (synthetic chroma sheet with a ring → `asset_sheet.py --names ring
  --anchor center`) → `build.py --no-sfx` → `hf check .` (non-zero exit = fail) → `hf snapshot . --at <times>
  --no-end` → `probe.py check` → with `--render`: `hf render -q draft` + ffprobe duration within 0.1 s of the total.
- `space.js` (`// @scene space @actions title`): `TOON.backdrop(parent, tone="deep", ctx, density=36) -> {bg, stars}`
  (full-frame `bgDeep|bgMid|bgLight` rect + sparkles r 5-14 px at seeded positions), `TOON.twinkle(tl, stars, dur, rng)`
  (opacity .35↔1, period 1.2-2.6 s, finite repeats); scene `space` = backdrop + idle twinkle + action
  `title {text, size=110, y=540}` (TDisplay text popping in).
- Gallery assets: `blob.svg` 200×200 orange `#FF7A59` disc with 8 px ink outline (anchor centre);
  sprite `tick` 2 frames, cell `[200,200]`: `f00.svg` red `#E63946` square, `f01.svg` blue `#3A86FF` square, each
  with `<clipPath id="fig">` so sprite_import's rule holds.

- [ ] **Step 1: Failing test** `tests/test_probe.py`: a 40×20 PNG half `#0B2E35`, half `#FFFFFF` in
  `snap/frame-00-at-0.5s.png`; slots `{"sp": 0}`; probes `px (5,5) bgDeep`, `area [20,0,20,20] text min .9`,
  `noarea [0,0,40,20] #00B140` → `check` exits 0; change the first to `#FF0000` → exit 1 and `FAIL sp t=0.5`.
- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement `probe.py`.** **Step 4: Run, expect PASS.**
- [ ] **Step 5: Gallery shot + probes for `space`** (`tests/gallery/shots.json`):

```json
{"style": "style.json", "shots": [
  {"id": "sp", "dur": 1.5, "scene": "space", "params": {"tone": "deep"},
   "beats": [{"at": 0.3, "do": "title", "args": {"text": "MASCOT"}}]}]}
```

`probes.json`: `{"shot":"sp","t":0.1,"kind":"area","rect":[0,0,1920,1080],"color":"bgDeep","min":0.85}`,
`{"shot":"sp","t":0.1,"kind":"noarea","rect":[760,470,400,140],"color":"text","max":0.002,"note":"title hidden before its beat"}`,
`{"shot":"sp","t":1.2,"kind":"area","rect":[760,470,400,140],"color":"text","min":0.05,"note":"title visible"}`.
- [ ] **Step 6: Implement `space.js`, `selftest.sh`, `make_fixtures.py`.** Run `bash scripts/selftest.sh`.
  Expected: pytest green, `hf check` 0 errors, 3 × `PASS`, `selftest passed`. Read the 1.2 s snapshot yourself.
- [ ] **Step 7: Commit** `mascot-explainer: probe harness, selftest, space scene`.
