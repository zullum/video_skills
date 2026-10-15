// @scene days @actions split,fill,tag,out
// The weekly plan: MON | WED | FRI columns. White separators draw down, labels drop in, the same bubbles appear
// in every column, then "2x12 / 3/WEEK" tags pop beside them.
(function () {
  var T = window.TOON, K = function () { return T.bubbleKit; };

  T.scene.days = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.flat ? 0 : p.density);
      var labels = p.labels || ["MON", "WED", "FRI"], n = labels.length, cw = T.W / n, layer = T.layer(rig);
      var seps = [], labs = [], cols = [];
      for (var k = 0; k < n; k++) {
        var cx = cw * (k + 0.5);
        if (k > 0) {
          seps.push(T.el("div", { style: "position:absolute;left:" + (k * cw - 3) + "px;top:0;width:6px;height:" + T.H +
            "px;background:" + T.c("text") + ";transform-origin:50% 0%;" }, layer));
        }
        labs.push(T.shape.title(layer, cx, p.labelY || 70, labels[k], { size: p.labelSize || 72 }));
        var items = (p.items || []).map(function (it) {
          return { asset: it.asset, sprite: it.sprite, rep: it.rep, texture: it.texture, x: cx + (it.dx || 0), y: T.H / 2 + (it.dy || 0), r: it.r || 100 };
        });
        cols.push(K().make(layer, items, { id: ctx.id + "c" + k, dur: ctx.dur }, ctx.tl));
      }
      return { layer: layer, seps: seps, labs: labs, cols: cols };
    },
    idle: function (tl, st, dur) {
      st.cols.forEach(function (bs) { K().idle(tl, bs, dur, st.ctx.rng); });
    },
    actions: {
      split: function (tl, st, t, a) {
        var sg = a.stagger == null ? 0.2 : a.stagger;
        st.labs.forEach(function (lab, k) {
          tl.fromTo(lab, { y: -40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35, ease: "power3.out" }, t + k * sg);
          if (k > 0) tl.fromTo(st.seps[k - 1], { scaleY: 0 }, { scaleY: 1, duration: 0.35, ease: "power2.out" }, t + k * sg - 0.1);
        });
      },
      fill: function (tl, st, t, a) {
        var sg = a.stagger == null ? 0.15 : a.stagger;
        (a.cols || st.cols.map(function (_, k) { return k; })).forEach(function (k, j) {
          K().pop(tl, st.cols[k], t + j * sg, { stagger: 0.05 });
        });
      },
      tag: function (tl, st, t, a) {
        var sg = a.stagger == null ? 0.12 : a.stagger, i = 0;
        (a.cols || st.cols.map(function (_, k) { return k; })).forEach(function (k) {
          st.cols[k].forEach(function (b) {
            T.pop(tl, T.shape.tag(st.layer, b.x + 0.9 * b.r, b.y - 0.6 * b.r, a.lines || ["2x12", "3/WEEK"], { size: a.size || 30 }), t + (i++) * sg);
          });
        });
      },
      out: function (tl, st, t) {
        st.cols.forEach(function (bs) { K().out(tl, bs, t, {}); });
      }
    }
  };
})();
