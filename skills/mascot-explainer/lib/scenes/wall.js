// @scene cardWall @actions fill,fgIn,out
// A wall of video thumbnails with shouty titles flies in around the figure, who stands in front seen from behind.
(function () {
  var T = window.TOON;

  T.scene.cardWall = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.flat ? 0 : p.density);
      var area = p.area || [60, 40, 1860, 760], cols = p.cols || 5, rows = p.rows || 3, rnd = T.rng(T.hash(ctx.id + "wall"));
      var cw = (area[2] - area[0]) / cols, ch = (area[3] - area[1]) / rows, layer = T.layer(rig);
      var cards = (p.cards || []).slice(0, cols * rows).map(function (c, i) {
        var col = i % cols, row = Math.floor(i / cols);
        var x = area[0] + cw * (col + 0.5) + (rnd() - 0.5) * 60, y = area[1] + ch * (row + 0.5) + (rnd() - 0.5) * 60;
        var el = T.shape.card(layer, x, y, cw * 0.88, ch * 0.84, { fill: c.fill, title: c.title, asset: c.asset });
        return { el: el, rot: (rnd() - 0.5) * 10, dx: (rnd() - 0.5) * 800, dy: (rnd() - 0.5) * 600 };
      });
      var fg = p.fg ? T.img(T.layer(rig), p.fg.asset, p.fg) : null;
      return { cards: cards, fg: fg };
    },
    actions: {
      fill: function (tl, st, t, a) {
        st.cards.forEach(function (c, i) {
          tl.fromTo(c.el, { x: c.dx, y: c.dy, scale: 0.6, rotation: c.rot * 3, opacity: 0 },
            { x: 0, y: 0, scale: 1, rotation: c.rot, opacity: 1, duration: 0.45, ease: "power3.out" }, t + i * (a.stagger == null ? 0.06 : a.stagger));
        });
      },
      fgIn: function (tl, st, t) {
        if (st.fg) tl.fromTo(st.fg, { y: 300, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "power3.out" }, t);
      },
      out: function (tl, st, t) { st.cards.forEach(function (c) { T.out(tl, c.el, t); }); }
    }
  };
})();
