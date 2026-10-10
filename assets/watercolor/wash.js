// Watercolor (references/watercolor.md): window.WC, a seeded Canvas2D wash and ink engine. Needs scene.js.
// Technique (Tyler Hobbs layering, as in a-small-odyssey): deform a polygon by recursive
// gaussian midpoint subdivision, stack N translucent deformed layers, darken alternate
// edges, punch pigment holes with a noise map. Same seed -> same pixels; draw is pure in p/t.
(function () {
  var S = window.SCENE, N = 14;

  function gauss(rnd) {
    var u = 1 - rnd(), v = rnd();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.2832 * v);
  }
  function shade(hex, k) {
    var n = parseInt(hex.slice(1), 16);
    return "rgb(" + [(n >> 16) & 255, (n >> 8) & 255, n & 255]
      .map(function (c) { return Math.round(c * k); }).join(",") + ")";
  }
  function canvas(w, h) {
    var c = document.createElement("canvas");
    c.width = Math.ceil(w); c.height = Math.ceil(h);
    return c;
  }

  // Midpoint subdivision; each vertex carries its own "wetness" v, so some edges bleed more.
  function deform(pts, depth, amt, rnd) {
    for (var d = 0; d < depth; d++) {
      var out = [];
      for (var i = 0; i < pts.length; i++) {
        var a = pts[i], b = pts[(i + 1) % pts.length];
        var len = Math.hypot(b[0] - a[0], b[1] - a[1]), v = (a[2] + b[2]) / 2;
        out.push(a, [(a[0] + b[0]) / 2 + gauss(rnd) * len * amt * v,
          (a[1] + b[1]) / 2 + gauss(rnd) * len * amt * v, v * (0.5 + rnd() * 0.8)]);
      }
      pts = out;
    }
    return pts;
  }

  // Tileable value noise as alpha: where it is high, pigment gets lifted (destination-out).
  var punch = (function () {
    var size = 512, c = canvas(size, size), x = c.getContext("2d");
    var img = x.createImageData(size, size), rnd = S.mulberry32(31337);
    var octaves = [128, 64, 16].map(function (cell) {
      var n = size / cell, g = [];
      for (var i = 0; i < n * n; i++) g.push(rnd());
      return { cell: cell, n: n, g: g };
    });
    function at(o, px, py) {
      var fx = px / o.cell, fy = py / o.cell, x0 = Math.floor(fx), y0 = Math.floor(fy);
      var tx = fx - x0, ty = fy - y0, n = o.n;
      var a = o.g[(y0 % n) * n + (x0 % n)], b = o.g[(y0 % n) * n + ((x0 + 1) % n)];
      var c2 = o.g[((y0 + 1) % n) * n + (x0 % n)], d = o.g[((y0 + 1) % n) * n + ((x0 + 1) % n)];
      tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
      return (a + (b - a) * tx) * (1 - ty) + (c2 + (d - c2) * tx) * ty;
    }
    for (var py = 0; py < size; py++) {
      for (var px = 0; px < size; px++) {
        var v = 0.55 * at(octaves[0], px, py) + 0.3 * at(octaves[1], px, py) + 0.15 * at(octaves[2], px, py);
        var k = Math.min(1, Math.max(0, (v - 0.42) / 0.4));
        img.data[(py * size + px) * 4 + 3] = Math.round(255 * k * k * (3 - 2 * k));
      }
    }
    x.putImageData(img, 0, 0);
    return c;
  })();

  // solid: dense pigment for objects; otherwise a light glaze (sky, clouds)
  function makeWash(poly, color, seed, bleed, solid) {
    var rnd = S.mulberry32(seed);
    var pts = resample(poly.concat([poly[0]]), 90).slice(0, -1); // wobble scales with ~90 px edges
    var base = deform(pts.map(function (p) { return [p[0], p[1], 0.6 + rnd() * 0.8]; }), 2, bleed, rnd);
    var layers = [], x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (var i = 0; i < N; i++) {
      var l = deform(base, 3, bleed * 0.7, rnd);
      l.forEach(function (p) {
        x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]);
      });
      layers.push(l);
    }
    var pad = 4;
    return { layers: layers, color: color, edge: shade(color, 0.6), cache: null, seed: seed,
      alpha: solid ? 0.24 : 0.15, punch: solid ? 0.2 : 0.16,
      bbox: { x: x0 - pad, y: y0 - pad, w: x1 - x0 + pad * 2, h: y1 - y0 + pad * 2 },
      punchOff: [rnd() * 512, rnd() * 512] };
  }

  // Paint the first p*N layers (the last one fading in) into c, then lift pigment.
  function render(w, p, c) {
    var b = w.bbox, x = c.getContext("2d"), n = p * N;
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.clearRect(0, 0, c.width, c.height);
    x.translate(-b.x, -b.y);
    for (var i = 0; i < N; i++) {
      var a = Math.min(1, n - i);
      if (a <= 0) break;
      x.beginPath();
      w.layers[i].forEach(function (pt, k) { k ? x.lineTo(pt[0], pt[1]) : x.moveTo(pt[0], pt[1]); });
      x.closePath();
      x.globalAlpha = w.alpha * a; x.fillStyle = w.color; x.fill();
      if (i % 2) { x.globalAlpha = 0.18 * a; x.strokeStyle = w.edge; x.lineWidth = 2.2; x.stroke(); }
    }
    x.setTransform(1, 0, 0, 1, -w.punchOff[0], -w.punchOff[1]);
    x.globalCompositeOperation = "destination-out";
    x.globalAlpha = w.punch;
    x.fillStyle = x.createPattern(punch, "repeat");
    x.fillRect(w.punchOff[0], w.punchOff[1], b.w, b.h);
    x.globalCompositeOperation = "source-over"; x.globalAlpha = 1;
    x.setTransform(1, 0, 0, 1, 0, 0);
    return c;
  }

  var scratch = canvas(1600, 2400);

  // Wet leading edge: the region painted so far, with a seeded wavy front.
  function clipSweep(ctx, b, sp, sweep, seed) {
    if (sp >= 1 || sweep === "none") return;
    function wave(u) { return 22 * Math.sin(u * 0.013 + seed) + 10 * Math.sin(u * 0.041 + seed * 2); }
    ctx.beginPath();
    if (sweep === "grow") {
      ctx.ellipse(b.x + b.w / 2, b.y + b.h / 2, b.w * 0.75 * sp, b.h * 0.75 * sp, 0, 0, 6.2832);
    } else if (sweep === "right") {
      ctx.moveTo(b.x, b.y);
      for (var y = b.y; y <= b.y + b.h + 20; y += 20) ctx.lineTo(b.x + b.w * sp + wave(y), y);
      ctx.lineTo(b.x, b.y + b.h + 20);
    } else { // "down" paints from the top, "up" from the bottom
      var front = sweep === "down" ? b.y + b.h * sp : b.y + b.h * (1 - sp);
      var back = sweep === "down" ? b.y - 40 : b.y + b.h + 40;
      ctx.moveTo(b.x - 40, back);
      for (var x = b.x - 40; x <= b.x + b.w + 40; x += 20) ctx.lineTo(x, front + wave(x));
      ctx.lineTo(b.x + b.w + 40, back);
    }
    ctx.closePath();
    ctx.clip();
  }

  function drawWash(ctx, w, p, sweep) {
    if (p <= 0) return;
    var b = w.bbox, src;
    if (p >= 1) src = w.cache || (w.cache = render(w, 1, canvas(b.w, b.h)));
    else {
      if (b.w > scratch.width || b.h > scratch.height) scratch = canvas(Math.max(b.w, scratch.width), Math.max(b.h, scratch.height));
      src = render(w, p, scratch);
    }
    ctx.save();
    clipSweep(ctx, b, S.easeOut(Math.min(1, p / 0.6)), sweep, w.seed);
    ctx.drawImage(src, 0, 0, b.w, b.h, b.x, b.y, b.w, b.h);
    ctx.restore();
  }

  function resample(pts, step) {
    var out = [pts[0]];
    for (var i = 1; i < pts.length; i++) {
      var a = pts[i - 1], b = pts[i], k = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
      for (var j = 1; j <= k; j++) out.push([a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k]);
    }
    return out;
  }

  // Ink line with "boil": 3 jittered drawings cycling at 12 fps; q = drawn-on fraction.
  function ink(ctx, pts, closed, t, seed, q, width) {
    if (q <= 0) return;
    var rnd = S.mulberry32(seed * 7 + (Math.floor(t * 12) % 3));
    var line = resample(closed ? pts.concat([pts[0]]) : pts, 10);
    var n = Math.max(2, Math.floor(line.length * q)), ox = 0, oy = 0, prev = null;
    ctx.save();
    ctx.lineCap = "round"; ctx.strokeStyle = "#1b1822"; ctx.globalAlpha = 0.9;
    for (var i = 0; i < n; i++) {
      ox = ox * 0.75 + gauss(rnd) * 0.9; oy = oy * 0.75 + gauss(rnd) * 0.9;
      var cur = [line[i][0] + ox, line[i][1] + oy];
      if (prev) {
        ctx.lineWidth = width * (0.65 + 0.35 * Math.sin(i * 0.17 + seed));
        ctx.beginPath(); ctx.moveTo(prev[0], prev[1]); ctx.lineTo(cur[0], cur[1]); ctx.stroke();
      }
      prev = cur;
    }
    ctx.restore();
  }

  window.WC = { makeWash: makeWash, drawWash: drawWash, ink: ink };
})();
