// @scene space @actions title
// The "space" backdrop: one palette tone and twinkling 4-point sparkles. Every scene draws its background
// with TOON.backdrop (density 0 = a flat colour, no sparkles).
(function () {
  var T = window.TOON;

  T.backdrop = function (parent, tone, ctx, density) {
    tone = tone || "deep";
    var role = "bg" + tone.charAt(0).toUpperCase() + tone.slice(1), stars = [];
    var bg = T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:100%;background:" + T.c(role) + ";" }, parent);
    if (density !== 0) {
      var rnd = T.rng(T.hash(ctx.id + "stars")), svg = T.svg(parent), n = density || 36;
      for (var i = 0; i < n; i++) stars.push(T.shape.sparkle(svg, rnd() * T.W, rnd() * T.H, 5 + rnd() * 9, "text"));
    }
    return { bg: bg, stars: stars };
  };

  T.twinkle = function (tl, stars, dur, rng) {
    stars.forEach(function (s) {
      var half = (1.2 + rng() * 1.4) / 2, n = Math.max(1, Math.floor(dur / half));
      tl.fromTo(s, { opacity: 1 }, { opacity: 0.35, duration: half, ease: "sine.inOut", repeat: n - 1, yoyo: true }, rng() * half);
    });
  };

  T.scene.space = {
    build: function (rig, p, ctx) {
      var b = T.backdrop(rig, p.tone, ctx, p.flat ? 0 : p.density);
      return { stars: b.stars, layer: T.layer(rig) };
    },
    idle: function (tl, st, dur) { T.twinkle(tl, st.stars, dur, T.rng(T.hash(st.ctx.id + "tw"))); },
    actions: {
      title: function (tl, st, t, a) {
        var h = T.shape.title(st.layer, a.x || T.W / 2, a.y || T.H / 2, a.text, { size: a.size || 110, color: a.color });
        T.pop(tl, h, t);
      }
    }
  };
})();
