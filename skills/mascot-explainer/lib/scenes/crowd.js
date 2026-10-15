// @scene crowd @actions think,coins,clear,out
// People in front of the study tables: two rows of tinted silhouettes, "?" thought bubbles popping over their
// heads, then "$" coins over the ones who bought.
(function () {
  var T = window.TOON;

  function row(layer, p, n, y, h, op, shift, rnd) {
    var a = T.manifest.assets[p.asset], out = [];
    for (var k = 0; k < n; k++) {
      var x = T.W / (2 * n) + k * T.W / n + shift, hh = h * (0.96 + rnd() * 0.08);
      var el = T.img(layer, p.asset, { x: x, y: y, h: hh, flip: k % 2 === 1 });
      el.style.opacity = op;
      out.push({ el: el, x: x, top: y - hh * a.anchor[1], h: hh });
    }
    return out;
  }

  T.scene.crowd = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "light", ctx, 0);
      var n = p.n || 7, y = p.y == null ? T.H : p.y, h = p.h || 520, rnd = T.rng(T.hash(ctx.id + "crowd"));
      if (n > 1) row(T.layer(rig), p, n - 1, y - 40, h * 0.88, 0.55, T.W / (2 * n), rnd);
      return { front: row(T.layer(rig), p, n, y, h, 1, 0, rnd), marks: [], byHead: {}, top: T.layer(rig) };
    },
    actions: {
      think: function (tl, st, t, a) { st.mark(tl, t, a, function (L, x, y, r) { return T.shape.think(L, x, y, r, a.symbol || "?"); }); },
      coins: function (tl, st, t, a) { st.mark(tl, t, a, function (L, x, y, r) { return T.shape.coin(L, x, y, r); }); },
      clear: function (tl, st, t) { st.marks.forEach(function (m) { T.out(tl, m, t); }); },
      out: function (tl, st, t) { st.front.forEach(function (f) { T.out(tl, f.el, t); }); }
    }
  };
  // Shared by think and coins: one mark above each listed head.
  var build = T.scene.crowd.build;
  T.scene.crowd.build = function (rig, p, ctx) {
    var st = build(rig, p, ctx);
    st.mark = function (tl, t, a, make) {
      (a.heads || st.front.map(function (_, k) { return k; })).forEach(function (k, i) {
        var f = st.front[k], r = Math.max(44, f.h * 0.2), m = make(st.top, f.x, f.top - r - 20, r), at = t + i * (a.stagger == null ? 0.1 : a.stagger);
        m.setAttribute("data-layout-allow-overlap", "");
        if (st.byHead[k]) T.out(tl, st.byHead[k], at, { dur: 0.15 });   // "?" turns into "$"
        st.byHead[k] = m;
        st.marks.push(m);
        T.pop(tl, m, at);
      });
    };
    return st;
  };
})();
