// @scene document @actions in,flip,out
// A guide built in code: a cover slides in, then page spreads with a heading, grey text lines and figures.
(function () {
  var T = window.TOON;

  function face(layer, w, h) {
    var box = T.box(layer, T.W / 2, T.H / 2, w, h);
    var f = T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:100%;background:#fff;border-radius:6px;" +
      "box-shadow:0 18px 40px rgba(0,0,0,0.35);overflow:hidden;" }, box);
    return { box: box, face: f };
  }
  function lines(parent, x, y, w, n, rnd) {
    for (var i = 0; i < n; i++) {
      T.el("div", { style: "position:absolute;left:" + x + "px;top:" + (y + i * 26) + "px;width:" + w * (0.6 + rnd() * 0.35) + "px;height:12px;" +
        "border-radius:6px;background:" + T.c("bgLight") + ";opacity:0.5;" }, parent);
    }
  }

  function cover(layer, pg) {
    var pf = face(layer, 560, 760), f = pf.face;
    T.el("div", { text: String(pg.title || "").toUpperCase(), style: "position:absolute;left:40px;top:50px;width:480px;text-align:center;white-space:normal;" +
      T.shape.font({ size: 92, color: "ink" }) + "line-height:0.95;" }, f);
    if (pg.subtitle) T.el("div", { text: pg.subtitle, style: "position:absolute;left:40px;top:300px;width:480px;text-align:center;" +
      T.shape.font({ font: "label", size: 30, color: "ink" }) + "white-space:normal;" }, f);
    if (pg.asset) T.img(f, pg.asset, { x: 280, y: 720, h: 330, anchor: [0.5, 1] });
    return pf.box;
  }

  function spread(layer, pg, rnd) {
    var pf = face(layer, 1100, 760), f = pf.face, n = pg.lines || 12;
    T.el("div", { style: "position:absolute;left:549px;top:30px;width:2px;height:700px;background:" + T.c("bgLight") + ";opacity:0.6;" }, f);
    T.el("div", { text: String(pg.heading || "").toUpperCase(), style: "position:absolute;left:50px;top:50px;" + T.shape.font({ size: 40, color: "ink" }) }, f);
    lines(f, 50, 120, 440, Math.ceil(n / 2), rnd);
    lines(f, 600, 60, 440, Math.floor(n / 2), rnd);
    (pg.figures || []).forEach(function (a, i) { T.img(f, a, { x: 820 + (i % 2) * 140 - (pg.figures.length > 1 ? 70 : 0), y: 700, h: 300, anchor: [0.5, 1] }); });
    return pf.box;
  }

  T.scene.document = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.flat ? 0 : p.density);
      var layer = T.layer(rig), rnd = T.rng(T.hash(ctx.id + "doc"));
      var pages = (p.pages || []).map(function (pg) { return pg.kind === "spread" ? spread(layer, pg, rnd) : cover(layer, pg); });
      pages.forEach(function (b) { ctx.tl.set(b, { opacity: 0 }, 0); });
      return { pages: pages, cur: -1 };
    },
    actions: {
      "in": function (tl, st, t, a) {
        var i = a.i || 0;
        tl.fromTo(st.pages[i], { scale: 0.6, opacity: 0, rotation: 6 }, { scale: 1, opacity: 1, rotation: -2, duration: 0.5, ease: "back.out(1.4)" }, t);
        st.cur = i;
      },
      flip: function (tl, st, t, a) {
        var to = a.to == null ? st.cur + 1 : a.to;
        if (st.cur >= 0) tl.to(st.pages[st.cur], { x: -900, rotation: -12, opacity: 0, duration: 0.45, ease: "power2.in" }, t);
        tl.fromTo(st.pages[to], { x: 900, rotation: 8, opacity: 0 }, { x: 0, rotation: -2, opacity: 1, duration: 0.5, ease: "power3.out" }, t + 0.15);
        st.cur = to;
      },
      out: function (tl, st, t) { if (st.cur >= 0) tl.to(st.pages[st.cur], { opacity: 0, duration: 0.3 }, t); }
    }
  };
})();
