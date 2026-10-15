// @scene powerUp @actions ignite,burst,freeze,rays,off
// Energy beats around the figure: a dark flame aura flares up behind it (ignite), lightning bursts out of it
// (burst), the frame freezes grey under a pause badge (freeze), or slow rays turn behind it (rays).
(function () {
  var T = window.TOON;

  function target(layer, t, tl, dur) {
    if (t.sprite) {
      var sp = T.sprite(layer, t.sprite, { x: t.x, y: t.y, h: t.h });
      if (t.rep) T.playReps(tl, sp, 0, dur, t.rep);
      return { el: sp.el, base: t.y };
    }
    var a = T.manifest.assets[t.asset], el = T.img(layer, t.asset, t);
    return { el: el, base: t.y + t.h * (1 - a.anchor[1]) };
  }

  T.scene.powerUp = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "mid", ctx, p.flat === false ? p.density : 0);
      // The aura scales as an HTML layer: GSAP scale + svgOrigin on this SVG group left it unrendered.
      var t = p.target, auraBox = T.layer(rig), g = T.el("g", {}, T.svg(auraBox)), vars = [];
      var rays = T.layer(rig), tg = target(T.layer(rig), t, ctx.tl, ctx.dur), base = tg.base;
      for (var k = 0; k < 3; k++) {
        var v = T.shape.flame(g, t.x, base, t.h * 1.3, t.h * 1.5, k + 1, { color: p.color, color2: p.color2 });
        v.setAttribute("opacity", k ? 0 : 1);
        vars.push(v);
      }
      auraBox.style.transformOrigin = t.x + "px " + base + "px";
      ctx.tl.set(auraBox, { opacity: 0 }, 0);
      return { aura: auraBox, vars: vars, x: t.x, cy: base - t.h * 0.5, base: base, h: t.h, rays: rays, top: T.layer(rig) };
    },
    actions: {
      ignite: function (tl, st, t) {
        tl.fromTo(st.aura, { scale: 0.2, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: "back.out(1.6)" }, t);
        for (var k = 1, s = t + 0.1; s < st.dur; k++, s += 0.1) {
          st.vars.forEach(function (v, i) { tl.set(v, { opacity: i === k % 3 ? 1 : 0 }, s); });
        }
      },
      burst: function (tl, st, t, a) {
        var n = a.n || 8, rnd = T.rng(T.hash(st.ctx.id + "bolts")), svg = T.svg(st.top), g = T.el("g", {}, svg);
        for (var i = 0; i < n; i++) {
          var ang = i * 2 * Math.PI / n + (rnd() - 0.5) * 0.4, r0 = st.h * 0.45, r1 = 300 + rnd() * 220;
          T.shape.bolt(g, st.x + Math.cos(ang) * r0, st.cy + Math.sin(ang) * r0, st.x + Math.cos(ang) * r1, st.cy + Math.sin(ang) * r1, i + 1, { w: 14 });
        }
        var glow = T.shape.rays(st.rays, st.x, st.cy, st.h * 1.6, { color: "accent", key: st.ctx.id + "burst" });
        T.pop(tl, glow, t, { blur: 0, dur: 0.2 });
        [[0, 1], [0.12, 0], [0.18, 1], [0.3, 0], [0.36, 1], [0.5, 0]].forEach(function (s) { tl.set(g, { opacity: s[1] }, t + s[0]); });
        tl.set(g, { opacity: 0 }, 0);
        T.out(tl, glow, t + 0.5, { dur: 0.3, scale: 1.2 });
        T.actions.shake(tl, st, t, { amp: 10 });
      },
      freeze: function (tl, st, t) {
        tl.set(st.cam, { filter: "grayscale(1) brightness(0.85)" }, t);
        T.pop(tl, T.shape.pauseIcon(st.top, T.W / 2, T.H / 2, 150), t, { dur: 0.25 });
      },
      rays: function (tl, st, t) {
        var r = T.shape.rays(st.rays, st.x, st.cy, st.h * 1.4, { color: "accent", key: st.ctx.id + "rays" });
        T.pop(tl, r, t, { blur: 0 });
        tl.to(r, { rotation: 30, duration: Math.max(0.1, st.dur - t), ease: "none" }, t);
      },
      off: function (tl, st, t) { tl.to(st.aura, { opacity: 0, duration: 0.25 }, t); }
    }
  };
})();
