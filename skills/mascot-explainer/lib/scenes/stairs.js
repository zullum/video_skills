// @scene stairs @actions build,place,out
// A staircase of progressions: steps grow up from the floor one by one, then figures and equipment stand on
// them (the hardest variation on the top step).
(function () {
  var T = window.TOON;

  T.scene.stairs = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "light", ctx, 0);
      var n = p.steps || 4, x0 = p.x0 == null ? 120 : p.x0, x1 = p.x1 == null ? 1800 : p.x1, ytop = p.ytop || 520, ybot = p.ybot || 900;
      var sw = (x1 - x0) / n, layer = T.layer(rig), steps = [];
      for (var k = 0; k < n; k++) {
        var h = (ybot - ytop) * (p.dir === "up" ? k + 1 : n - k) / n;
        var el = T.el("div", { style: "position:absolute;left:" + (x0 + k * sw) + "px;top:" + (ybot - h) + "px;width:" + sw + "px;height:" + h +
          "px;background:" + T.c("panel") + ";border:3px solid " + T.c("ink") + ";border-top-width:5px;transform-origin:50% 100%;" }, layer);
        steps.push({ el: el, cx: x0 + (k + 0.5) * sw, top: ybot - h });
      }
      var items = (p.items || []).map(function (it) {
        var s = steps[Math.min(it.step || 0, n - 1)];
        return T.img(layer, it.asset, { x: s.cx + (it.dx || 0), y: s.top, h: it.h || 200, anchor: it.anchor || [0.5, 1], flip: it.flip });
      });
      return { steps: steps, items: items };
    },
    actions: {
      build: function (tl, st, t, a) {
        st.steps.forEach(function (s, k) {
          tl.fromTo(s.el, { scaleY: 0 }, { scaleY: 1, duration: 0.35, ease: "back.out(1.4)" }, t + k * (a.stagger == null ? 0.15 : a.stagger));
        });
      },
      place: function (tl, st, t, a) {
        (a.items || st.items.map(function (_, i) { return i; })).forEach(function (i, k) {
          T.pop(tl, st.items[i], t + k * (a.stagger == null ? 0.12 : a.stagger));
        });
      },
      out: function (tl, st, t) { st.items.forEach(function (el) { T.out(tl, el, t); }); }
    }
  };
})();
