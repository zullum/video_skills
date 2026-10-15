// @scene seqRows @actions show,tag,out
// Progressions as rows: this exercise -> its harder variation, each row a bubble, an arrow and a bubble, with a
// set badge on the first one ("tag": "2x12") and optionally on the second ("toTag": "2x13").
(function () {
  var T = window.TOON, K = function () { return T.bubbleKit; };

  T.scene.seqRows = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "mid", ctx, p.flat === false ? p.density : 0);
      var rows = p.rows || [], n = rows.length, r = p.r || 70, x0 = p.x0 || 640, x1 = p.x1 || 1280;
      var layer = T.layer(rig), svg = T.svg(rig), top = T.layer(rig);
      var out = rows.map(function (row, i) {
        var y = T.H / 2 + (i - (n - 1) / 2) * (2 * r + 50);
        var bs = K().make(layer, [Object.assign({ x: x0, y: y, r: r }, row.from), Object.assign({ x: x1, y: y, r: r }, row.to)],
          { id: ctx.id + "r" + i, dur: ctx.dur }, ctx.tl);
        var arrow = T.shape.arrow(svg, x0 + r + 20, y, x1 - r - 20, y, { color: p.arrow || "ink" });
        ctx.tl.set(arrow.head, { opacity: 0 }, 0);
        ctx.tl.set(arrow.line, { attr: { "stroke-dashoffset": 1 } }, 0);
        var mk = function (text, x) {
          if (!text) return null;
          var b = T.shape.badge(top, x + 0.75 * r, y - 0.75 * r, Math.max(30, r * 0.5), text);
          ctx.tl.set(b, { opacity: 0 }, 0);
          return b;
        };
        return { bs: bs, arrow: arrow, badges: [mk(row.tag, x0), mk(row.toTag, x1)].filter(Boolean) };
      });
      return { rows: out };
    },
    idle: function (tl, st, dur) { st.rows.forEach(function (row) { K().idle(tl, row.bs, dur, st.ctx.rng); }); },
    actions: {
      show: function (tl, st, t, a) {
        (a.rows || st.rows.map(function (_, i) { return i; })).forEach(function (i, k) {
          var row = st.rows[i], at = t + k * (a.stagger == null ? 0.2 : a.stagger);
          T.pop(tl, row.bs[0].el, at);
          T.draw(tl, row.arrow.line, at + 0.1, 0.3);
          tl.fromTo(row.arrow.head, { opacity: 0 }, { opacity: 1, duration: 0.08 }, at + 0.35);
          T.pop(tl, row.bs[1].el, at + 0.3);
        });
      },
      tag: function (tl, st, t, a) {
        (a.rows || st.rows.map(function (_, i) { return i; })).forEach(function (i, k) {
          st.rows[i].badges.forEach(function (b, j) { T.pop(tl, b, t + k * 0.1 + j * 0.25); });
        });
      },
      out: function (tl, st, t) { st.rows.forEach(function (row) { K().out(tl, row.bs, t, {}); }); }
    }
  };
})();
