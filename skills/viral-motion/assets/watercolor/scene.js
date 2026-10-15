// Watercolor (references/watercolor.md): window.SCENE = the helpers wash.js and paper.js need
// (mulberry32 seeded random, prog, easeOut) plus an example scene: a night city paints in,
// windows light up, a paper lantern rises. 6 s, 1080x1920. Seeded: same file -> same scene.
(function () {
  var W = 1080, H = 1920;

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  function prog(t, t0, dur) { return clamp01((t - t0) / dur); }
  function easeOut(p) { return 1 - Math.pow(1 - p, 3); }
  function backOut(p) { var c = 1.9; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); }

  function rect(x, y, w, h) { return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]; }
  function ellipse(cx, cy, rx, ry, n) {
    var pts = [];
    for (var i = 0; i < n; i++) {
      var a = (i / n) * Math.PI * 2;
      pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
    }
    return pts;
  }

  var rnd = mulberry32(707);
  var shapes = [];   // washes, painted back to front

  // bleed: how far the wash wanders past its outline (0..1); sweep: how it paints in;
  // solid: an object that hides what is behind it (dense pigment), not a sky glaze
  function add(id, poly, color, t0, dur, sweep, bleed, solid) {
    shapes.push({ id: id, poly: poly, color: color, t0: t0, dur: dur, sweep: sweep,
      bleed: bleed, solid: !!solid, seed: 1000 + shapes.length * 97 });
  }

  add("sky-top", rect(-160, -160, 1400, 1380), "#2a2e5a", 0.0, 1.4, "down", 0.3);
  add("sky-mid", rect(-160, 640, 1400, 760), "#5a4e85", 0.25, 1.3, "down", 0.3);
  add("sky-glow", rect(-160, 1120, 1400, 420), "#c4878d", 0.45, 1.2, "right", 0.3);
  add("moon-halo", ellipse(780, 380, 190, 190, 18), "#8f86b8", 0.55, 1.0, "grow", 0.25);
  add("moon", ellipse(780, 380, 92, 92, 14), "#f1dfa6", 0.6, 0.9, "grow", 0.05, true);
  add("cloud-1", ellipse(300, 560, 330, 70, 16), "#7b6f9e", 0.8, 1.1, "right", 0.25);
  add("cloud-2", ellipse(840, 760, 300, 55, 16), "#6c6191", 1.0, 1.1, "right", 0.25);

  // Three rows of buildings, back (pale, early) to front (dark, late)
  var rows = [
    { color: "#4b4f7d", top: [1080, 1260], w: [130, 210], t0: 0.9, ink: false, lit: 0 },
    { color: "#353961", top: [1250, 1420], w: [170, 250], t0: 1.3, ink: true, lit: 0.3 },
    { color: "#22243d", top: [1440, 1600], w: [210, 320], t0: 1.7, ink: true, lit: 0.35 },
  ];
  rows.forEach(function (row, r) {
    var x = -30 - rnd() * 60, i = 0;
    while (x < W + 20) {
      var w = row.w[0] + rnd() * (row.w[1] - row.w[0]);
      var top = row.top[0] + rnd() * (row.top[1] - row.top[0]);
      var poly = rect(x, top, w, H + 60 - top), parts = null;
      if (rnd() < 0.35) { // stepped roof
        var sw = w * (0.35 + rnd() * 0.3), sx = x + (w - sw) * rnd(), sh = 50 + rnd() * 70;
        poly = [[x, top], [sx, top], [sx, top - sh], [sx + sw, top - sh], [sx + sw, top],
          [x + w, top], [x + w, H + 60], [x, H + 60]];
        parts = [rect(x, top, w, H + 60 - top), rect(sx, top - sh, sw, sh + 4)]; // convex pieces
      }
      var t0 = row.t0 + i * 0.07;
      add("b" + r + "-" + i, poly, row.color, t0, 0.9, "up", 0.04, true);
      var b = shapes[shapes.length - 1];
      b.parts = parts;
      b.windows = []; // small warm washes that pop on, drawn right after their building
      if (row.ink) b.ink = { t0: t0 + 0.6, dur: 0.6, seed: 5000 + shapes.length * 13 }; // outline draws on
      for (var wy = top + 46; wy < H - 120 && row.lit; wy += 78) {
        for (var wx = x + 30; wx < x + w - 50; wx += 62) {
          if (rnd() < row.lit) {
            b.windows.push({ poly: rect(wx, wy, 30, 38), t0: 2.3 + rnd() * 1.4,
              seed: 9000 + wx * 7 + wy });
          }
        }
      }
      x += w - 10 - rnd() * 30; i++;
    }
  });

  // Lantern: local geometry around (0,0); pose(t) places it.
  var lantern = {
    body: ellipse(0, 0, 78, 100, 20), color: "#f6e7b8",
    capTop: rect(-46, -116, 92, 24), capBot: rect(-40, 92, 80, 22), capColor: "#6b4a33",
    ribs: [-40, 0, 40].map(function (k) {
      var pts = [];
      for (var j = 0; j <= 10; j++) {
        var a = -Math.PI / 2 + (j / 10) * Math.PI;
        pts.push([k * Math.cos(a) * 1.0, Math.sin(a) * 96]);
      }
      return pts;
    }),
    string: [[0, 114], [4, 150], [-3, 186]],
    t0: 2.6,
  };
  function lanternPose(t) {
    var p = prog(t, lantern.t0, 6 - lantern.t0), k = t - lantern.t0;
    return { on: t >= lantern.t0, x: 560 + 50 * Math.sin(1.4 * k),
      y: 2100 - 1180 * (1 - Math.pow(1 - p, 2)), rot: 0.07 * Math.sin(1.9 * k),
      glow: 0.75 + 0.25 * Math.sin(5.1 * k) };
  }

  // Warm glow on the Shot's glow canvas (CSS screen blend).
  function drawGlow(ctx, t) {
    ctx.clearRect(0, 0, W, H);
    var L = lanternPose(t);
    if (!L.on) return;
    var r = 330 * L.glow, g = ctx.createRadialGradient(L.x, L.y, 0, L.x, L.y, r);
    g.addColorStop(0, "rgba(255,214,140,0.55)");
    g.addColorStop(0.35, "rgba(255,190,110,0.22)");
    g.addColorStop(1, "rgba(255,170,90,0)");
    ctx.fillStyle = g;
    ctx.fillRect(L.x - r, L.y - r, r * 2, r * 2);
  }

  window.SCENE = { W: W, H: H, mulberry32: mulberry32, prog: prog, easeOut: easeOut,
    backOut: backOut, shapes: shapes,
    lantern: lantern, lanternPose: lanternPose, drawGlow: drawGlow };
})();
