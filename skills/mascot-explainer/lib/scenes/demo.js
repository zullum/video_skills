// @scene exerciseDemo @actions reps,callout,arrow,tag,insets,out
// The exercise itself on a flat background: the sprite loops its rep on a soft floor shadow with an optional prop
// behind it; a callout ring draws round a joint, a double arrow shows the range of motion, a prescription tag
// pops, and muscle insets (magnified crops of any asset) pop around the figure while it keeps repping.
(function () {
  var T = window.TOON;

  T.scene.exerciseDemo = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "mid", ctx, p.flat === false ? p.density : 0);
      var x = p.x == null ? T.W / 2 : p.x, y = p.y == null ? 900 : p.y, h = p.h || 600, s = T.manifest.sprites[p.sprite];
      if (p.shadow !== false) {
        var cw = s ? s.cell[0] * h / s.cell[1] : h;
        T.el("ellipse", { cx: x, cy: y, rx: cw * 0.28, ry: 13, fill: T.c("ink"), opacity: 0.12 }, T.svg(rig));
      }
      if (p.prop) T.img(rig, p.prop.asset, p.prop);
      var sp = p.sprite ? T.sprite(rig, p.sprite, { x: x, y: y, h: h, anchor: p.anchor }) : null;
      return { sp: sp, svg: T.svg(rig), layer: T.layer(rig), p: p };
    },
    idle: function (tl, st, dur) {
      var p = st.p, start = p.start || 0;
      if (!st.sp || !p.rep || p.reps === "beats") return;
      if (p.reps === "fill" || p.reps == null) T.playReps(tl, st.sp, start, dur, p.rep);
      else for (var i = 0, t = start; i < p.reps; i++) t = T.playSeq(tl, st.sp, t, p.rep);
    },
    actions: {
      // Explicit cycles (use with params.reps = "beats", so the idle loop doesn't schedule the same frames).
      reps: function (tl, st, t, a) {
        var rep = a.rep || st.p.rep;
        for (var i = 0; i < (a.n || 1); i++) t = T.playSeq(tl, st.sp, t, rep);
        T.show(tl, st.sp, rep[0][0], t);
      },
      callout: function (tl, st, t, a) {
        T.draw(tl, T.shape.callout(st.svg, a.x, a.y, a.r || 90, { color: a.color, w: a.w || 9 }), t, a.dur || 0.4);
      },
      arrow: function (tl, st, t, a) {
        var d = T.shape.doubleArrow(st.svg, a.x0, a.y0, a.x1, a.y1, { color: a.color || "bgDeep", w: a.w || 10, head: 30 });
        T.draw(tl, d.line, t, a.dur || 0.5);
        d.heads.forEach(function (hd) { tl.fromTo(hd, { opacity: 0 }, { opacity: 1, duration: 0.1 }, t + (a.dur || 0.5) * 0.8); });
      },
      tag: function (tl, st, t, a) {
        T.pop(tl, T.shape.tag(st.layer, a.x == null ? 230 : a.x, a.y == null ? 110 : a.y, a.lines || ["2x12", "3/WEEK"], { size: a.size }), t);
      },
      insets: function (tl, st, t, a) {
        (a.items || []).forEach(function (it, k) {
          var b = T.shape.bubble(st.layer, it.x, it.y, it.r, { texture: "none", fill: it.fill || "panel", key: st.ctx.id + "in" + k });
          var rr = it.r * 0.97, as = T.manifest.assets[it.asset];
          if (as) T.img(b.content, it.asset, { x: rr, y: rr, h: 2 * it.r * (it.zoom || 2.2), anchor: [it.fx == null ? 0.5 : it.fx, it.fy == null ? 0.35 : it.fy] });
          var at = t + k * (a.stagger == null ? 0.2 : a.stagger);
          T.pop(tl, b.el, at);
          if (it.label) T.pop(tl, T.shape.tag(st.layer, it.x, it.y + it.r + 34, [it.label], { size: it.labelSize || 30, rot: 0 }), at + 0.1);
        });
      },
      out: function (tl, st, t) { if (st.sp) T.out(tl, st.sp.el, t); }
    }
  };
})();
