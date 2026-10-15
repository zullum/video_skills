# 05 Scenes 1 (Tasks 12-15)

Every scene task follows the same cycle: add its gallery shots to `tests/gallery/shots.json` and its probes to
`tests/gallery/probes.json` → `bash scripts/selftest.sh --only <ids>` fails (`unknown scene`) → write the scene →
selftest passes → Read the snapshots yourself (does it look like the reference beat?) → commit. A scene file starts
with its registry header and stays ≤200 lines. Items are visible from the start unless a `pop` beat lists them.

### Task 12: `bubbles` (+ zoomThrough) — the pattern

**Files:** Create `lib/scenes/bubbles.js`; Modify `tests/gallery/{shots,probes}.json`

**Reference beat:** exercises inside textured planet discs pop in one by one (0:00-0:06), float, one glows with
rays while the others grey out (3:38), the camera dives into a bubble and its content becomes the next shot (3:40).

**Interfaces:** Produces `TOON.bubbleKit = {make(parent, items, ctx, tl) -> [bubble], pop, highlight, dim, undim,
swarm, out}` (reused by `days` and `windowRoom`). Item = `{asset|sprite, x, y, r, texture?, rep?}`; a feet-anchored
asset stands at `(r, 1.72r)` of the disc with height `1.45r`, a centre-anchored one sits at `(r, r)`.

- [ ] **Step 1: Gallery shots + probes**

```json
{"id": "bb", "dur": 2.2, "scene": "bubbles", "params": {"items": [{"asset": "blob", "x": 960, "y": 540, "r": 200}]},
 "beats": [{"at": 0.3, "do": "pop", "args": {"items": [0]}}, {"at": 1.2, "do": "highlight", "args": {"i": 0}}]},
{"id": "bb2", "dur": 1.2, "scene": "bubbles", "params": {"items": [{"asset": "ring", "x": 960, "y": 540, "r": 220}]}},
{"id": "bz", "dur": 1.5, "scene": "bubbles", "params": {"items": [{"asset": "blob", "x": 500, "y": 540, "r": 150},
 {"asset": "blob", "x": 1400, "y": 540, "r": 150}]}, "beats": [{"at": 0.8, "do": "zoom", "args": {"i": 0}}]},
{"id": "bs", "dur": 1.5, "scene": "bubbles", "params": {"items": [{"asset": "blob", "x": 960, "y": 540, "r": 120}]},
 "beats": [{"at": 0.2, "do": "swarm", "args": {"n": 24}}]}
```

Probes: `bb` t .1 `px 960,540 bgDeep tol 20` (hidden before pop); t 1.0 `px 960,540 #FF7A59 tol 50` and
`px 960,346 rim tol 50`; t 2.0 `notpx 960,280 bgDeep tol 20` (glow above the bubble). `bb2` t .6
`noarea [0,0,1920,1080] #00B140 tol 60 max .0005` and `notpx 960,540 #00B140 tol 60` (traced ring: no chroma box,
the hole is see-through — Review Focus 4). `bz` t 1.45 `area [0,0,1920,1080] #FF7A59 tol 60 min .35`. `bs` t 1.4
`area [0,0,1920,1080] rim tol 40 min .01`.

- [ ] **Step 2: Run, expect FAIL** — `bash scripts/selftest.sh --only bb,bb2,bz,bs` → `bb: unknown scene 'bubbles'; known: space`.
- [ ] **Step 3: Write `lib/scenes/bubbles.js`**

```js
// @scene bubbles @actions pop,highlight,dim,undim,zoom,swarm,out
// Planet bubbles: an exercise (asset, or a looping sprite) inside a textured disc with a white rim.
(function () {
  var T = window.TOON;
  function fill(b, it, tl, ctx) {
    if (it.sprite) {
      b.sp = T.sprite(b.content, it.sprite, { x: it.r, y: it.r * 1.72, h: it.r * 1.45 });
      if (it.rep) T.playReps(tl, b.sp, 0, ctx.dur, it.rep);
    } else if (it.asset) {
      var feet = T.manifest.assets[it.asset].anchor[1] > 0.9;
      T.img(b.content, it.asset, { x: it.r * 0.97, y: it.r * (feet ? 1.72 : 0.97), h: it.r * (it.h || 1.45) });
    }
  }
  var K = T.bubbleKit = {
    make: function (parent, items, ctx, tl) {
      return items.map(function (it, i) {
        var b = T.shape.bubble(parent, it.x, it.y, it.r, { texture: it.texture || (i % 2 ? "stripes" : "craters"),
          seed: T.hash(ctx.id + i), key: ctx.id + "-b" + i });
        fill(b, it, tl, ctx); return b;
      });
    },
    idle: function (tl, bs, dur, rng) {
      bs.forEach(function (b) { T.bob(tl, b.inner, 0, dur, { amp: 6, period: 3.2 + rng() }); });
    },
    pop: function (tl, bs, t, a) {
      var ids = a.items || bs.map(function (_, i) { return i; }), st = a.stagger == null ? 0.12 : a.stagger;
      ids.forEach(function (i, k) { T.pop(tl, bs[i].el, t + k * st); });
    },
    highlight: function (tl, bs, t, a, dur) {
      var b = bs[a.i], rays = T.shape.rays(b.el.parentNode, b.x, b.y, b.r * 2.4, { color: a.color || "accent", key: "hl" + b.x + b.y });
      b.el.parentNode.insertBefore(rays, b.el);
      T.pop(tl, rays, t, { blur: 0 });
      tl.to(rays, { rotation: 25, duration: Math.max(0.1, dur - t), ease: "none" }, t);
      tl.to(b.el, { scale: 1.12, duration: 0.3, ease: "back.out(2)" }, t);
      if (a.dimOthers !== false) K.dim(tl, bs.filter(function (_, i) { return i !== a.i; }), t, {});
    },
    dim: function (tl, bs, t) {
      bs.forEach(function (b) { tl.to(b.inner, { opacity: 0.55, filter: "grayscale(1) brightness(1.1)", duration: 0.3 }, t); });
    },
    undim: function (tl, bs, t) {
      bs.forEach(function (b) { tl.to(b.inner, { opacity: 1, filter: "grayscale(0) brightness(1)", duration: 0.3 }, t); });
    },
    swarm: function (tl, parent, t, a, ctx, items) {
      var rnd = T.rng(T.hash(ctx.id + "swarm")), n = a.n || 24, made = [];
      for (var k = 0; k < n; k++) {
        var r = (a.rmin || 26) + rnd() * ((a.rmax || 50) - (a.rmin || 26));
        var it = { x: r + 40 + rnd() * (T.W - 2 * r - 80), y: r + 40 + rnd() * (T.H - 2 * r - 80), r: r };
        if (items.length) { var src = items[k % items.length]; it.asset = src.asset; it.sprite = src.sprite; }
        var b = K.make(parent, [it], { id: ctx.id + "s" + k, dur: ctx.dur }, tl)[0];
        T.pop(tl, b.el, t + k * (a.stagger || 0.04), { dur: 0.25 }); made.push(b);
      }
      return made;
    }
  };
  T.scene.bubbles = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.density);
      var layer = T.layer(rig);
      return { layer: layer, items: p.items || [], bs: K.make(layer, p.items || [], ctx, ctx.tl) };
    },
    idle: function (tl, st, dur) { K.idle(tl, st.bs, dur, st.ctx.rng); },
    actions: {
      pop: function (tl, st, t, a) { K.pop(tl, st.bs, t, a); },
      highlight: function (tl, st, t, a) { K.highlight(tl, st.bs, t, a, st.dur); },
      dim: function (tl, st, t, a) { K.dim(tl, (a.items || []).map(function (i) { return st.bs[i]; }), t); },
      undim: function (tl, st, t) { K.undim(tl, st.bs, t); },
      zoom: function (tl, st, t, a) {
        var b = st.bs[a.i || 0];
        T.actions.zoomInto(tl, st, t, { x: b.x, y: b.y, scale: a.scale || 7, dur: a.dur || 0.6 });
      },
      swarm: function (tl, st, t, a) { st.bs = st.bs.concat(K.swarm(tl, st.layer, t, a, st.ctx, st.items)); },
      out: function (tl, st, t, a) {
        (a.items || st.bs.map(function (_, i) { return i; })).forEach(function (i, k) {
          T.out(tl, st.bs[i].el, t + k * (a.stagger || 0.06)); });
      }
    }
  };
})();
```

- [ ] **Step 4: Run, expect PASS** (all `bb*`, `bz`, `bs` probes). Read the `bb` 2.0 s and `bz` 1.45 s snapshots.
- [ ] **Step 5: Commit** `mascot-explainer: bubbles scene`.

### Task 13: `textSlam`

**Reference beat:** "THE FIX NOBODY'S SELLING YOU" and "SATISFICING" (2:22, 2:30): bold italic uppercase white words
punch in on the spoken word; "THE WEEKLY STRUC…" types on (5:45).

**Header:** `// @scene textSlam @actions slam,type,sub,out`. **Params:** `{tone="deep", flat=false, text, size=150,
x=960, y=540, color="text", sub?: {text, size=64}}`. Build: backdrop (sparkles unless `flat`), a centred line of
word spans (TDisplay 800 italic, `display:inline-block`, margin .12em), optional sub line below at `y + size*.9`.
Actions: `slam {stagger=.12}` each word fromTo `{scale 1.6, opacity 0, y -30}` → `{1, 1, 0}` in .18 s power4.out,
then `shake {amp 6}` at the last word; `type {cps=16}` char spans set to opacity 0 at 0 and to 1 at `t + i/cps`;
`sub` pops the sub line; `out` scales the words to .8 and fades in .25 s.

- [ ] **Step 1: Gallery + probes:** `ts` (dur 1.6, text "BIG IDEA", slam at .4): t .2 `noarea [560,440,800,200]
  text max .002`; t 1.2 `area` same rect `text min .06`. `tt` (dur 1.6, "THE WEEKLY PLAN", type at .2 cps 20): t .1
  `noarea [360,440,1200,200] text max .002`; t 1.4 `area` same rect `text min .04`.
- [ ] **Steps 2-5:** run (FAIL) → write `lib/scenes/text.js` → run (PASS) + look → commit `mascot-explainer: textSlam`.

### Task 14: `days`

**Reference beat:** MON | WED | FRI columns (0:04, 5:45, 7:39): white separators draw down, labels top-centre, the
same three bubbles appear in every column, later "2×12 / 3/WEEK" tags beside them.

**Header:** `// @scene days @actions split,fill,tag,out`. **Params:** `{tone="deep", labels=["MON","WED","FRI"],
items: [{asset|sprite, dx, dy, r}] (relative to each column centre (cx, 540)), labelY=70, labelSize=72}`.
Build: backdrop; separators at `x = k*W/N` (white, 6 px, full height, `transform-origin: top`, scaleY 0); labels
(TDisplay, hidden); per column `bubbleKit.make` with `x = cx + dx`. Actions: `split {stagger=.2}` per column k at
`t + k*stagger`: its left separator scaleY 0→1 (.35 s power2.out) and its label from `y -40, opacity 0`;
`fill {cols, stagger=.15}` pops each column's bubbles; `tag {lines=["2x12","3/WEEK"], cols, stagger=.12}` pops a
`shape.tag` at `(x + .9r, y - .6r)` per bubble; `out`.

- [ ] **Step 1: Gallery + probes:** `dy` (dur 2.0, items `[{"asset":"blob","dx":0,"dy":80,"r":110}]`, split at .2,
  fill at .9 `{"cols":[0,1,2]}`): t .1 `noarea [637,300,6,400] text max .01`; t 1.0 `area [637,300,6,400] text
  min .8` and `area [220,30,200,80] text min .05`; t 1.6 `px 320,620 #FF7A59 tol 60`.
- [ ] **Steps 2-5:** FAIL → write `lib/scenes/days.js` → PASS + look → commit `mascot-explainer: days scene`.

### Task 15: `windowRoom`

**Reference beat:** spaceship interior (0:21, 0:45, 5:58): a wide window with a faint grid on the glass, a white
panel strip on the sill, angled side walls; exercise bubbles float behind the glass; an astronaut seen from behind
in the lower right corner.

**Header:** `// @scene windowRoom @actions pop,highlight,dim,swarm,fgIn,out`. **Params:** `{window=[200,70,1720,740],
grid=72, items (frame coords), fg?: {asset, x, y, h, flip}}`. Build on one full-frame SVG: room fill `bgMid`;
side walls = polygons from the frame corners to the window corners inflated by 28 px (`bgDeep`, opacity .5, ink
4 px edges); window frame `panel` with ink 6 px; glass `bgDeep`; grid lines every `grid` px (`rim`, opacity .10,
2 px); 8 sparkles on the glass; sill strip `panel` 40 px under the window, then floor `bgLight` with 4 light
trapezoid panels (`rim`, .9). Bubbles live in a div at the glass rect with `overflow:hidden` (frame coords minus
the glass origin), `fg` image on top. Actions: bubbleKit verbs (swarm limited to the glass), `fgIn {from="right"}`
(x ±420 → 0, .5 s power3.out), `out`.

- [ ] **Step 1: Gallery + probes:** `wr` (dur 2.0, items `[{"asset":"blob","x":960,"y":400,"r":120}]`, pop at .3):
  t .1 `px 960,100 bgDeep tol 25` (glass) and `notpx 960,1060 bgDeep tol 20` (floor); t 1.2 `px 960,400 #FF7A59 tol 60`.
- [ ] **Steps 2-5:** FAIL → write `lib/scenes/room.js` → PASS + look → commit `mascot-explainer: windowRoom scene`.
- [ ] **Step 6:** full `bash scripts/selftest.sh` green.
