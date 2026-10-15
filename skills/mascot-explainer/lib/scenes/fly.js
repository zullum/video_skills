// @scene flyBy @actions fly,launch,badge,out
// Something crosses the frame: a satellite with a "15 MIN" badge drifting across, rockets launching upward
// with flickering exhaust, a small rocket streaking past. rot0 = the asset's own heading (-90 = points up).
(function () {
  var T = window.TOON;

  function teardrop(g, tx, ty, w, L, fill) {
    var d = "M" + (tx - w / 2) + "," + ty + "C" + (tx - w / 2) + "," + (ty + L * 0.6) + " " + tx + "," + (ty + L) + " " + tx + "," + (ty + L) +
      "C" + tx + "," + (ty + L) + " " + (tx + w / 2) + "," + (ty + L * 0.6) + " " + (tx + w / 2) + "," + ty + "Z";
    return T.el("path", { d: d, fill: T.c(fill), stroke: T.c("ink"), "stroke-width": 3, "stroke-linejoin": "round" }, g);
  }

  // Exhaust behind the object, drawn pointing down in the box frame and turned to the tail side.
  function flame(inner, w, h, rot0) {
    var s = T.svg(inner, w, h), tx = w / 2, ty = h * 0.92;
    inner.insertBefore(s, inner.firstChild);
    var turn = T.el("g", { transform: "rotate(" + ((rot0 == null ? -90 : rot0) + 90) + " " + w / 2 + " " + h / 2 + ")" }, s);
    var grow = T.el("g", {}, turn), flick = T.el("g", {}, grow);
    teardrop(flick, tx - w * 0.16, ty - 6, w * 0.16, h * 0.32, "accent");
    teardrop(flick, tx + w * 0.16, ty - 6, w * 0.16, h * 0.32, "accent");
    teardrop(flick, tx, ty - 6, w * 0.24, h * 0.6, "rim");
    return { grow: grow, flick: flick, origin: tx + " " + ty };
  }

  T.scene.flyBy = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.flat ? 0 : p.density);
      var a = T.manifest.assets[p.asset], h = p.h || 260, w = h * a.w / a.h, path = p.path || [[T.W / 2, T.H / 2]];
      var it = T.item(T.layer(rig), path[0][0], path[0][1], w, h, 0.5, 0.5);
      var st = { it: it, path: path, rot0: p.rot0, w: w, h: h };
      if (p.flame !== false) st.flame = flame(it.inner, w, h, p.rot0);
      st.img = T.img(it.inner, p.asset, { x: w / 2, y: h / 2, h: h, anchor: [0.5, 0.5] });
      if (p.badge) st.badge = T.shape.badge(it.inner, w * 0.85, h * 0.12, p.badge.r || 70, p.badge.text);
      if (p.rot0 != null && path.length > 1) {
        ctx.tl.set(it.el, { rotation: Math.atan2(path[1][1] - path[0][1], path[1][0] - path[0][0]) * 180 / Math.PI - p.rot0 }, 0);
      }
      return st;
    },
    idle: function (tl, st, dur) {
      if (!st.flame) return;
      var n = Math.max(1, Math.floor(dur / 0.066));
      tl.fromTo(st.flame.flick, { scaleY: 0.8 }, { scaleY: 1.2, duration: 0.066, repeat: n - 1, yoyo: true, ease: "none", svgOrigin: st.flame.origin }, 0);
    },
    actions: {
      fly: function (tl, st, t, a) {
        var path = a.path || st.path, dur = a.dur || 1.6, L = [], tot = 0;
        for (var i = 1; i < path.length; i++) { L.push(Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])); tot += L[i - 1]; }
        if (!tot) return;
        var kf = path.slice(1).map(function (q, i) {
          var k = { x: q[0] - path[0][0], y: q[1] - path[0][1], duration: dur * L[i] / tot, ease: a.ease || "power1.inOut" };
          if (st.rot0 != null) k.rotation = Math.atan2(q[1] - path[i][1], q[0] - path[i][0]) * 180 / Math.PI - st.rot0;
          return k;
        });
        tl.to(st.it.el, { keyframes: kf }, t);
        tl.to(st.img, { filter: "blur(1.5px)", duration: 0.15 }, t).to(st.img, { filter: "blur(0px)", duration: 0.2 }, t + dur - 0.2);
      },
      launch: function (tl, st, t, a) {
        var dur = a.dur || 1.2;
        tl.fromTo(st.it.el, { y: T.H * 0.7 }, { y: 0, duration: dur, ease: "power2.out" }, t);
        if (st.flame) tl.fromTo(st.flame.grow, { scaleY: 1.6 }, { scaleY: 1, duration: dur, ease: "power2.out", svgOrigin: st.flame.origin }, t);
      },
      badge: function (tl, st, t) { if (st.badge) T.pop(tl, st.badge, t); },
      out: function (tl, st, t) { T.out(tl, st.it.el, t); }
    }
  };
})();
