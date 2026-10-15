// @scene shelf @actions fill,clear,split,cite,out
// A study on a shelf: items (jam jars) build up in a small or a big pyramid, the screen splits to compare the
// two, and a small citation card names the source.
(function () {
  var T = window.TOON;

  // Pyramid rows from the shelf up: bottom row m (m(m+1)/2 >= n, at most 8), then m-1, m-2, ...
  function layout(n, cx, shelfY, iw, ih) {
    var m = 1, out = [];
    while (m * (m + 1) / 2 < n && m < 8) m++;
    for (var row = 0, left = n; left > 0; row++) {
      var k = Math.min(left, Math.max(1, m - row)), y = shelfY - row * ih * 0.82;
      for (var j = 0; j < k; j++) out.push([cx + (j - (k - 1) / 2) * iw * 1.05, y]);
      left -= k;
    }
    return out;
  }

  T.scene.shelf = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "light", ctx, 0);
      var a = T.manifest.assets[p.item], ih = p.itemH || 110, iw = ih * a.w / a.h, shelfY = p.shelfY || 780, counts = p.counts || [6, 24];
      var svg = T.svg(rig);
      T.el("rect", { x: -10, y: shelfY, width: T.W + 20, height: 40, fill: T.c("panel"), stroke: T.c("ink"), "stroke-width": 6 }, svg);
      var divider = T.el("line", { x1: T.W / 2, y1: 40, x2: T.W / 2, y2: shelfY, stroke: T.c("ink"), "stroke-width": 6,
        pathLength: 1, "stroke-dasharray": 1, "stroke-dashoffset": 1 }, svg);
      var sets = counts.map(function (n, s) {
        var g = T.layer(rig), cx = s === 0 ? T.W / 2 : T.W * 0.75;
        var items = layout(n, cx, shelfY, iw, ih).map(function (q) { return T.img(g, p.item, { x: q[0], y: q[1], h: ih, anchor: [0.5, 1] }); });
        items.forEach(function (el) { ctx.tl.set(el, { opacity: 0 }, 0); });
        return { g: g, items: items };
      });
      var cite = null;
      if (p.citation) {
        cite = T.el("div", { text: p.citation, style: "position:absolute;right:40px;bottom:24px;background:#fff;border:3px solid " + T.c("ink") +
          ";padding:6px 12px;transform-origin:100% 100%;" + T.shape.font({ font: "label", size: 22, color: "ink" }) }, rig);
        ctx.tl.set(cite, { opacity: 0 }, 0);
      }
      return { sets: sets, divider: divider, cite: cite };
    },
    actions: {
      fill: function (tl, st, t, a) {
        var set = st.sets[a.set || 0], sg = a.stagger == null ? 0.04 : a.stagger;
        set.items.slice(0, a.count || set.items.length).forEach(function (el, i) { T.pop(tl, el, t + i * sg, { dur: 0.25 }); });
      },
      clear: function (tl, st, t, a) {
        st.sets[a.set || 0].items.forEach(function (el) { T.out(tl, el, t); });
      },
      split: function (tl, st, t) {
        T.draw(tl, st.divider, t, 0.4);
        tl.to(st.sets[0].g, { x: -T.W / 4, duration: 0.45, ease: "power2.inOut" }, t);
      },
      cite: function (tl, st, t) { if (st.cite) T.pop(tl, st.cite, t, { blur: 0, dur: 0.25 }); },
      out: function (tl, st, t) { st.sets.forEach(function (s) { s.items.forEach(function (el) { T.out(tl, el, t); }); }); }
    }
  };
})();
