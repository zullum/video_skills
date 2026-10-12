# Watercolor: painted washes on one sheet of paper

A Visual style for any level: picture-book watercolor (the look of "The Lantern"). Dense, saturated washes with
torn, darker edges and lifted pigment, a fine ink line that "boils", warm glows, everything sitting in the same
paper. A seeded Canvas2D engine with no dependencies paints it, deterministic and seek-safe, and fast: the 6 s
example renders in ~7 s (180 frames, `--workers 2`).

## When

- The user names it (watercolor, painted), or the request clearly fits: painted, storybook, fairy tale. Never
  pick it unasked for anything else.
- Write "Visual style: Watercolor" and its palette (hex + role) into `frame.md`. Banned looks still apply: a later
  Watercolor video changes the palette, the subject and the fonts.

## The files

`SKILL/assets/watercolor/`:
- `scene.js` → `window.SCENE`: the helpers (`mulberry32` seeded random, `prog(t, t0, dur)` → 0..1, `easeOut`,
  `backOut`, `W`, `H`) plus an example scene (`shapes`, `lantern`, `lanternPose`, `drawGlow`): a night city paints
  in, windows light up, a paper lantern rises, 6 s portrait. For a new video, replace the example with its own
  shapes and keep the helpers: `wash.js` and `paper.js` use them. Other formats: set `W`/`H`, redraw the scene.
- `wash.js` → `window.WC`: washes and ink.
- `paper.js` → `window.PAPER.paint(canvas, seed)`: the paper, painted once.

Copy them into the project right after `new_project.sh`:

```bash
mkdir -p <project>/assets && cp SKILL/assets/watercolor/{scene,wash,paper}.js <project>/assets/
```

## index.html: the paper over transparent Shots

index.html owns the paper; every Shot stays transparent (no ground), at every level. Load the scripts in `<head>`
after GSAP in this order (`wash.js` reads `SCENE` as it loads). The paper canvas is the root's **last** child,
multiplied over every Shot, on the paper base `#ece3d2`. Keep the scaffold's `*` and `html, body` size rules;
drop its `#root` and `#title` rules and its `<h1>`; add these after them:

```html
<script src="assets/scene.js"></script>
<script src="assets/paper.js"></script>
<script src="assets/wash.js"></script>
<style>
  html, body, #root { background: #ece3d2; }
  #root { position: relative; width: 100%; height: 100%; overflow: hidden; }
  #paper { position: absolute; inset: 0; width: 100%; height: 100%; display: block;
           mix-blend-mode: multiply; pointer-events: none; }
</style>
<!-- body: -->
<div id="root" data-composition-id="main" data-start="0" data-duration="6" data-width="1080" data-height="1920">
  <div id="s1" class="clip" data-composition-id="s1" data-composition-src="compositions/s1.html"
       data-start="0" data-duration="6" data-track-index="0" data-width="1080" data-height="1920"></div>
  <canvas id="paper" width="1080" height="1920" data-layout-allow-overflow></canvas>
</div>
<script>
  window.PAPER.paint(document.getElementById("paper"), 4242);   // any fixed seed
  window.__timelines["main"] = gsap.timeline({ paused: true });
</script>
```

## A Shot

Two full-size canvases: the paint, and the glow above it with `mix-blend-mode: screen`. Build every wash once,
outside `draw`; `draw(t)` clears and repaints everything from `t` alone, driven by a clock tween (seek-safe both ways):

```html
<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; }
    #s1-paint, #s1-glow { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
    #s1-glow { mix-blend-mode: screen; }
  </style>
  <div id="root" data-composition-id="s1" data-width="1080" data-height="1920">
    <canvas id="s1-paint" width="1080" height="1920" data-layout-allow-overflow></canvas>
    <canvas id="s1-glow" width="1080" height="1920" data-layout-allow-overflow></canvas>
  </div>
  <script>
    // SCENE, WC from assets/scene.js, assets/wash.js (loaded by index.html)
    (function () {
      var S = window.SCENE, WC = window.WC, DUR = 6;
      var ctx = document.getElementById("s1-paint").getContext("2d");
      var gctx = document.getElementById("s1-glow").getContext("2d");
      var washes = S.shapes.map(function (sh) { return WC.makeWash(sh.poly, sh.color, sh.seed, sh.bleed, sh.solid); });
      function draw(t) {
        ctx.clearRect(0, 0, S.W, S.H);
        S.shapes.forEach(function (sh, i) {                        // back to front
          WC.drawWash(ctx, washes[i], S.prog(t, sh.t0, sh.dur), sh.sweep);
          if (sh.ink) WC.ink(ctx, sh.poly, true, t, sh.ink.seed, S.easeOut(S.prog(t, sh.ink.t0, sh.ink.dur)), 2.6);
        });
        S.drawGlow(gctx, t);
      }
      var tl = gsap.timeline({ paused: true }), clock = { _t: 0 };
      Object.defineProperty(clock, "t", { get: function () { return this._t; },
        set: function (v) { this._t = v; draw(v); } });
      tl.to(clock, { t: DUR, duration: DUR, ease: "none" }, 0);
      draw(0);
      window.__timelines["s1"] = tl;
    })();
  </script>
</template></body></html>
```

## The engine

- `WC.makeWash(poly, color, seed, bleed, solid)`: `poly` is `[[x, y], ...]` in canvas pixels; `color` must be
  `#rrggbb` (the darker edge is derived from it). `bleed` is how far the edge wanders: ~0.04-0.06 for objects,
  0.25-0.3 for sky glazes. `solid` objects use dense pigment that mostly hides what's behind (a trace shows
  through, like a real glaze); otherwise it's a light glaze. Every wash has its own seed; same seed, same pixels.
- `WC.drawWash(ctx, wash, p, sweep)`: `p` 0..1 is the paint-in (14 layers accumulate behind a wavy wet edge);
  `sweep` is `"down"`, `"up"`, `"right"`, `"grow"` or `"none"`. At `p` = 1 it draws a cached bitmap, so finished
  washes are cheap and can move: build them around (0, 0), then `ctx.save(); ctx.translate(x, y); ctx.rotate(r);
  WC.drawWash(ctx, w, 1, "none"); ctx.restore()`.
- **Ink boil**: `WC.ink(ctx, pts, closed, t, seed, q, width)` draws a near-black line (2-3 px) through `pts` that
  boils: three seeded jittered drawings cycling at 12 fps, chosen from `t`, so it seeks. `q` 0..1 is the drawn-on
  fraction.
- **Glow**: clear the glow canvas every `draw`, then fill a warm radial gradient (e.g. `rgba(255,214,140,0.55)` →
  transparent); the canvas's screen blend makes it light, not paint. `S.drawGlow(gctx, t)` is the example.
- Cost: only washes still painting in (`p` < 1) are re-rendered each frame. Big sky washes painting in at the
  same time are the slow frames.

**The rest of the example scene**, as the skeleton's `draw` extends it (`L = S.lantern`; `parts` is unused):
- **Lit windows**: per shape, draw them right after its wash and before its ink. Each `sh.windows[j]` is a wash
  `makeWash(win.poly, "#f2c66d", win.seed, 0.06, true)` that pops on over 0.35 s from `win.t0`: `p = S.prog(t,
  win.t0, 0.35)`, `globalAlpha = min(1, 2p)`, scaled by `S.backOut(p)` around its centre (`poly[0]` + (15, 19)),
  drawn with `drawWash(ctx, w, 1, "none")`.
- **Lantern**, last (in front), at `S.lanternPose(t)` (skip while `!on`; translate to `x, y`, rotate `rot`):
  finished washes (`p` = 1) `body` (`L.color`, seed 77, bleed 0.05), `capTop` and `capBot` (`L.capColor`, seeds
  78 and 79, bleed 0.04), all solid; then full ink (`q` = 1): rib index `k` (0-2) open, seed 300 + k, 2 px; `body` closed, 310, 3.2 px;
  `capTop` and `capBot` closed, 311 and 312, 2.6 px; `string` open, 313, 2 px.

## With each Video type

- **Showreel**: the through-line object is one wash with its ink outline; paint-in sweeps, the ink draw-on, the
  boil and the glow are techniques in their own right. The boil stays 12 fps at 60 fps: a hand-drawn hold.
- **Lyric video**: each world is a new set of washes painted over the last on its section change; a sung word can
  land as an ink draw-on or a `"grow"` bloom starting at its onset.
- **Story film**: as Level 3 already requires, index.html owns the environment (here the paper) and Shots are
  transparent. A seam can be the next Shot's first washes sweeping in over the outgoing one (overlap the hosts).

## Lessons from the Story-film test render (Abeceda)

- Text overlays that sit under the multiplied paper trip the layout check ("text_occluded"). Mark each overlay
  text node (and word span) `data-layout-allow-occlusion`; the paper canvas carries the attribute too.
- A **solid** object's paint-in reads as a translucent grey slab at p < 0.5 (the meadow shows through). Keep its
  paint-in short (0.4 s), start it before its Shot's first beat, and never film a hit while it is half painted.
- A hit needs a visible change in one frame: pop the object in at its final paint (group `t0` + a back-eased scale),
  don't rely on a paint-in that is at p = 0.03 on the hit frame.
- Shots as data: `assets/watercolor/book.js` mounts a Shot from groups of washes (move / rot / squash / bob / exit,
  a per-group speed `k`), so a Shot file is a list, not a draw routine.

## Check

`SKILL/scripts/hf check` with 0 errors, then seek safety: snapshot the same times forward and in reverse (two
browser runs); the PNGs at each time must be byte-identical. Pick times where things change.

```bash
cd <project>
SKILL/scripts/hf snapshot . --at 0.5,1.5,3,5.9 --no-end -o snapshots/fwd
SKILL/scripts/hf snapshot . --at 5.9,3,1.5,0.5 --no-end -o snapshots/rev
for f in snapshots/fwd/*.png; do t=${f##*-at-}; cmp -s "$f" snapshots/rev/*-at-$t && echo "same $t" || echo "DIFF $t"; done
```
