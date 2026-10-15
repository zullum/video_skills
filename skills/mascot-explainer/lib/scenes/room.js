// @scene windowRoom @actions pop,highlight,dim,swarm,fgIn,out
// Spaceship interior: a wide window with a faint grid on the glass, angled side walls, a lit panel strip on the
// sill and a floor; bubbles float behind the glass; an astronaut (or any figure) stands in the foreground.
(function () {
  var T = window.TOON, K = function () { return T.bubbleKit; };

  function poly(svg, pts, fill, op) {
    return T.el("polygon", { points: pts.map(function (p) { return p.join(","); }).join(" "), fill: T.c(fill), opacity: op == null ? 1 : op,
      stroke: T.c("ink"), "stroke-width": 4, "stroke-linejoin": "round" }, svg);
  }

  function room(rig, win, grid, rnd) {
    var W = T.W, H = T.H, x0 = win[0], y0 = win[1], x1 = win[2], y1 = win[3], f = 28;
    var fx0 = x0 - f, fy0 = y0 - f, fx1 = x1 + f, fy1 = y1 + f, svg = T.svg(rig);
    T.el("rect", { x: 0, y: 0, width: W, height: H, fill: T.c("bgMid") }, svg);
    poly(svg, [[0, 0], [W, 0], [fx1, fy0], [fx0, fy0]], "bgDeep", 0.35);
    poly(svg, [[0, 0], [fx0, fy0], [fx0, fy1], [0, H]], "bgDeep", 0.5);
    poly(svg, [[W, 0], [fx1, fy0], [fx1, fy1], [W, H]], "bgDeep", 0.5);
    poly(svg, [[0, H], [fx0, fy1 + 40], [fx1, fy1 + 40], [W, H]], "bgLight");
    T.el("rect", { x: fx0, y: fy0, width: fx1 - fx0, height: fy1 - fy0, rx: 10, fill: T.c("panel"), stroke: T.c("ink"), "stroke-width": 6 }, svg);
    T.el("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: T.c("bgDeep"), stroke: T.c("ink"), "stroke-width": 4 }, svg);
    var g = T.el("g", { stroke: T.c("rim"), "stroke-width": 2, opacity: 0.1 }, svg);
    for (var x = x0 + grid; x < x1; x += grid) T.el("line", { x1: x, y1: y0, x2: x, y2: y1 }, g);
    for (var y = y0 + grid; y < y1; y += grid) T.el("line", { x1: x0, y1: y, x2: x1, y2: y }, g);
    for (var i = 0; i < 8; i++) T.shape.sparkle(svg, x0 + 30 + rnd() * (x1 - x0 - 60), y0 + 30 + rnd() * (y1 - y0 - 60), 5 + rnd() * 7, "text");
    T.el("rect", { x: fx0, y: fy1, width: fx1 - fx0, height: 40, fill: T.c("panel"), stroke: T.c("ink"), "stroke-width": 4 }, svg);
    var pw = (fx1 - fx0 - 5 * 24) / 4;
    for (var k = 0; k < 4; k++) T.el("rect", { x: fx0 + 24 + k * (pw + 24), y: fy1 + 8, width: pw, height: 24, rx: 6, fill: T.c("rim"), opacity: 0.9 }, svg);
  }

  T.scene.windowRoom = {
    build: function (rig, p, ctx) {
      var win = p.window || [200, 70, 1720, 740];
      room(rig, win, p.grid || 72, T.rng(T.hash(ctx.id + "room")));
      var glass = T.el("div", { style: "position:absolute;left:" + win[0] + "px;top:" + win[1] + "px;width:" + (win[2] - win[0]) +
        "px;height:" + (win[3] - win[1]) + "px;overflow:hidden;" }, rig);
      var items = (p.items || []).map(function (it) { return Object.assign({}, it, { x: it.x - win[0], y: it.y - win[1] }); });
      var st = { win: win, glass: glass, items: items, bs: K().make(glass, items, ctx, ctx.tl) };
      if (p.fg) st.fg = T.img(T.layer(rig), p.fg.asset, p.fg);
      return st;
    },
    idle: function (tl, st, dur) { K().idle(tl, st.bs, dur, st.ctx.rng); },
    actions: {
      pop: function (tl, st, t, a) { K().pop(tl, st.bs, t, a); },
      highlight: function (tl, st, t, a) { K().highlight(tl, st.bs, t, a, st.dur); },
      dim: function (tl, st, t, a) { K().dim(tl, (a.items || []).map(function (i) { return st.bs[i]; }), t); },
      swarm: function (tl, st, t, a) {
        var w = st.win;
        st.bs = st.bs.concat(K().swarm(tl, st.glass, t, a, st.ctx, st.items, [10, 10, w[2] - w[0] - 10, w[3] - w[1] - 10]));
      },
      fgIn: function (tl, st, t, a) {
        if (st.fg) tl.fromTo(st.fg, { x: a.from === "left" ? -420 : 420, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: "power3.out" }, t);
      },
      out: function (tl, st, t, a) { K().out(tl, st.bs, t, a); }
    }
  };
})();
