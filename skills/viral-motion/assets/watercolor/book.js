// Picture-book layer over the Watercolor engine: a Shot is DATA (groups of washes and ink lines),
// BOOK.mount turns it into a seek-safe draw(t). Needs scene.js and wash.js loaded first.
(function () {
  var S = window.SCENE, WC = window.WC;
  var EASE = {
    linear: function (p) { return p; }, out: S.easeOut, back: S.backOut,
    in: function (p) { return p * p * p; },
    io: function (p) { return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; },
  };

  function ellipse(cx, cy, rx, ry, n) {
    var pts = [], k = n || 18;
    for (var i = 0; i < k; i++) {
      var a = (i / k) * Math.PI * 2;
      pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
    }
    return pts;
  }
  function rect(x, y, w, h) { return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]; }
  function rrect(x, y, w, h, r) {
    var c = [[x + r, y + r, 180], [x + w - r, y + r, 270], [x + w - r, y + h - r, 0], [x + r, y + h - r, 90]], pts = [];
    c.forEach(function (k) {
      for (var i = 0; i <= 4; i++) {
        var a = (k[2] + i * 22.5) * Math.PI / 180;
        pts.push([k[0] + Math.cos(a) * r, k[1] + Math.sin(a) * r]);
      }
    });
    return pts;
  }

  // group: { at:[x,y], t0, move:{to:[x,y],t0,dur,ease}, rot:{from,to,t0,dur,ease}|deg, bob:{amp,per},
  //          scale:{from,to,t0,dur,ease}|n, squash:{t0,dur,amt}, items:[...] }
  // item:  { poly, color, t0, dur, sweep, bleed, solid, ink:{t0,dur,w}, line:{pts,t0,dur,w} }
  function pose(g, t) {
    var x = g.at ? g.at[0] : 0, y = g.at ? g.at[1] : 0, r = 0, sx = 1, sy = 1, m = g.move;
    if (m) {
      var p = EASE[m.ease || "out"](S.prog(t, m.t0, m.dur));
      x += (m.to[0] - x) * p; y += (m.to[1] - y) * p;
    }
    if (g.exit) {
      var pe = EASE[g.exit.ease || "in"](S.prog(t, g.exit.t0, g.exit.dur));
      x += (g.exit.to[0] - x) * pe; y += (g.exit.to[1] - y) * pe;
    }
    if (g.bob) y +=Math.sin((t / g.bob.per) * Math.PI * 2) * g.bob.amp;
    if (typeof g.rot === "number") r = g.rot;
    else if (g.rot) r = g.rot.from + (g.rot.to - g.rot.from) * EASE[g.rot.ease || "out"](S.prog(t, g.rot.t0, g.rot.dur));
    if (typeof g.scale === "number") sx = sy = g.scale;
    else if (g.scale) sx = sy = g.scale.from + (g.scale.to - g.scale.from) * EASE[g.scale.ease || "back"](S.prog(t, g.scale.t0, g.scale.dur));
    if (g.squash) {
      var k = Math.sin(S.prog(t, g.squash.t0, g.squash.dur) * Math.PI) * g.squash.amt;
      sx *= 1 + k; sy *= 1 - k;
    }
    return { x: x, y: y, r: r * Math.PI / 180, sx: sx, sy: sy };
  }

  function drawItem(ctx, it, t) {
    if (it.wash) {
      var p = S.prog(t, it.t0, it.dur);
      if (p > 0) WC.drawWash(ctx, it.wash, p, it.sweep || "none");
    }
    if (it.ink) {
      var q = EASE.out(S.prog(t, it.ink.t0, it.ink.dur));
      if (q > 0) WC.ink(ctx, it.poly, true, t, it.iseed, q, it.ink.w || 2.6);
    }
    if (it.line) {
      var ql = EASE.out(S.prog(t, it.line.t0, it.line.dur));
      if (ql > 0) WC.ink(ctx, it.line.pts, false, t, it.iseed, ql, it.line.w || 2.2);
    }
  }

  function drawGlow(gctx, glow, t) {
    gctx.clearRect(0, 0, S.W, S.H);
    glow.forEach(function (o) {
      var p = S.prog(t, o.t0, o.dur);
      if (p <= 0) return;
      var gr = gctx.createRadialGradient(o.x, o.y, 0, o.x, o.y, o.r * (0.6 + 0.4 * p));
      gr.addColorStop(0, "rgba(" + o.rgb + "," + o.a * p + ")");
      gr.addColorStop(1, "rgba(" + o.rgb + ",0)");
      gctx.fillStyle = gr;
      gctx.fillRect(0, 0, S.W, S.H);
    });
  }

  function mount(paintId, glowId, spec, dur) {
    var ctx = document.getElementById(paintId).getContext("2d");
    var gctx = glowId ? document.getElementById(glowId).getContext("2d") : null;
    var n = 0;
    spec.groups.forEach(function (g) {
      g.items.forEach(function (it) {
        if (g.k) {   // a group can run faster: item times are scaled about g.base
          var m = function (x) { return g.base + (x - g.base) * g.k; };
          it.t0 = m(it.t0); it.dur *= g.k;
          if (it.ink) it.ink = { t0: m(it.ink.t0), dur: it.ink.dur * g.k, w: it.ink.w };
          if (it.line) it.line = { pts: it.line.pts, t0: m(it.line.t0), dur: it.line.dur * g.k, w: it.line.w };
        }
        if (it.poly) it.wash = WC.makeWash(it.poly, it.color, it.seed || 500 + (n += 53), it.bleed == null ? 0.05 : it.bleed, it.solid !== false);
        if (it.ink || it.line) it.iseed = it.seed || 900 + (n += 31);
      });
    });
    function draw(t) {
      ctx.clearRect(0, 0, S.W, S.H);
      spec.groups.forEach(function (g) {
        if (g.t0 != null && t < g.t0) return;
        var ps = pose(g, t);
        ctx.save();
        ctx.translate(ps.x, ps.y); ctx.rotate(ps.r); ctx.scale(ps.sx, ps.sy);
        g.items.forEach(function (it) { drawItem(ctx, it, t); });
        ctx.restore();
      });
      if (gctx) drawGlow(gctx, spec.glow || [], t);
    }
    var tl = gsap.timeline({ paused: true }), clock = { _t: 0 };
    Object.defineProperty(clock, "t", { get: function () { return this._t; }, set: function (v) { this._t = v; draw(v); } });
    tl.to(clock, { t: dur, duration: dur, ease: "none" }, 0);
    draw(0);
    return tl;
  }

  window.BOOK = { mount: mount, ellipse: ellipse, rect: rect, rrect: rrect };
})();
