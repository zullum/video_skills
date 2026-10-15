// @scene bubbles @actions pop,highlight,dim,undim,zoom,swarm,out
// Planet bubbles: an exercise (asset, or a looping sprite) inside a textured disc with a white rim. They pop in
// one by one, float, one glows with rays while the others grey out, and the camera can dive into one (zoom).
(function () {
  var T = window.TOON;

  function fill(b, it, tl, ctx) {
    if (it.sprite) {
      b.sp = T.sprite(b.content, it.sprite, { x: it.r * 0.97, y: it.r * 1.72, h: it.r * 1.45 });
      if (it.rep) T.playReps(tl, b.sp, 0, ctx.dur, it.rep);
    } else if (it.asset) {
      var feet = T.manifest.assets[it.asset].anchor[1] > 0.9;
      T.img(b.content, it.asset, { x: it.r * 0.97, y: it.r * (feet ? 1.72 : 0.97), h: it.r * (it.h || 1.45) });
    }
  }

  // Shared with days and windowRoom.
  var K = T.bubbleKit = {
    make: function (parent, items, ctx, tl) {
      return items.map(function (it, i) {
        var b = T.shape.bubble(parent, it.x, it.y, it.r, { texture: it.texture || (i % 2 ? "stripes" : "craters"),
          seed: T.hash(ctx.id + i), key: ctx.id + "-b" + i });
        fill(b, it, tl, ctx);
        return b;
      });
    },
    idle: function (tl, bs, dur, rng) {
      bs.forEach(function (b) { T.bob(tl, b.inner, 0, dur, { amp: 6, period: 3.2 + rng() }); });
    },
    pop: function (tl, bs, t, a) {
      var ids = a.items || bs.map(function (_, i) { return i; }), st = a.stagger == null ? 0.12 : a.stagger;
      ids.forEach(function (i, k) { T.pop(tl, bs[i].el, t + k * st); });
    },
    highlight: function (tl, bs, t, a, dur) {
      var b = bs[a.i || 0];
      var rays = T.shape.rays(b.el.parentNode, b.x, b.y, b.r * 2.4, { color: a.color || "accent", key: "hl" + b.x + "," + b.y });
      b.el.parentNode.insertBefore(rays, b.el);
      T.pop(tl, rays, t, { blur: 0 });
      tl.to(rays, { rotation: 25, duration: Math.max(0.1, dur - t), ease: "none" }, t);
      tl.to(b.el, { scale: 1.12, duration: 0.3, ease: "back.out(2)" }, t);
      if (a.dimOthers !== false) K.dim(tl, bs.filter(function (x) { return x !== b; }), t);
    },
    dim: function (tl, bs, t) {
      bs.forEach(function (b) { tl.to(b.inner, { opacity: 0.55, filter: "grayscale(1) brightness(1.1)", duration: 0.3 }, t); });
    },
    undim: function (tl, bs, t) {
      bs.forEach(function (b) { tl.to(b.inner, { opacity: 1, filter: "grayscale(0) brightness(1)", duration: 0.3 }, t); });
    },
    // n small bubbles at seeded spots inside `area` [x0, y0, x1, y1], popping fast: "too many options".
    swarm: function (tl, parent, t, a, ctx, items, area) {
      var rnd = T.rng(T.hash(ctx.id + "swarm")), n = a.n || 24, rmin = a.rmin || 26, rmax = a.rmax || 50, made = [];
      area = area || [40, 40, T.W - 40, T.H - 40];
      for (var k = 0; k < n; k++) {
        var r = rmin + rnd() * (rmax - rmin);
        var it = { x: area[0] + r + rnd() * (area[2] - area[0] - 2 * r), y: area[1] + r + rnd() * (area[3] - area[1] - 2 * r), r: r };
        if (items.length) { var src = items[k % items.length]; it.asset = src.asset; it.sprite = src.sprite; }
        var b = K.make(parent, [it], { id: ctx.id + "s" + k, dur: ctx.dur }, tl)[0];
        T.pop(tl, b.el, t + k * (a.stagger || 0.04), { dur: 0.25 });
        made.push(b);
      }
      return made;
    },
    out: function (tl, bs, t, a) {
      (a.items || bs.map(function (_, i) { return i; })).forEach(function (i, k) { T.out(tl, bs[i].el, t + k * (a.stagger || 0.06)); });
    }
  };

  T.scene.bubbles = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.flat ? 0 : p.density);
      var layer = T.layer(rig);
      return { layer: layer, items: p.items || [], bs: K.make(layer, p.items || [], ctx, ctx.tl) };
    },
    idle: function (tl, st, dur) { K.idle(tl, st.bs, dur, st.ctx.rng); },
    actions: {
      pop: function (tl, st, t, a) { K.pop(tl, st.bs, t, a); },
      highlight: function (tl, st, t, a) { K.highlight(tl, st.bs, t, a, st.dur); },
      dim: function (tl, st, t, a) { K.dim(tl, (a.items || []).map(function (i) { return st.bs[i]; }), t); },
      undim: function (tl, st, t) { K.undim(tl, st.bs, t); },
      zoom: function (tl, st, t, a) {
        var b = st.bs[a.i || 0];
        T.actions.zoomInto(tl, st, t, { x: b.x, y: b.y, scale: a.scale || 7, dur: a.dur || 0.6 });
      },
      swarm: function (tl, st, t, a) { st.bs = st.bs.concat(K.swarm(tl, st.layer, t, a, st.ctx, st.items)); },
      out: function (tl, st, t, a) { K.out(tl, st.bs, t, a); }
    }
  };
})();
