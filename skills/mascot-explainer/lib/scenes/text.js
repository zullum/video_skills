// @scene textSlam @actions slam,type,sub,out
// A bold italic uppercase headline: the words punch in on the spoken word (slam) or the letters type on (type),
// with an optional smaller line under it.
(function () {
  var T = window.TOON;

  T.scene.textSlam = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "deep", ctx, p.flat ? 0 : p.density);
      var size = p.size || 150, x = p.x || T.W / 2, y = p.y || T.H / 2, layer = T.layer(rig);
      var row = T.el("div", { style: T.shape.font({ size: size, color: p.color }) }, T.shape.center(layer, x, y));
      var words = [], chars = [];
      String(p.text).toUpperCase().split(/\s+/).forEach(function (w) {
        var ws = T.el("span", { style: "display:inline-block;margin:0 0.12em;transform-origin:50% 60%;" }, row);
        words.push(ws);
        w.split("").forEach(function (c) { chars.push(T.el("span", { text: c }, ws)); });
      });
      var sub = p.sub ? T.shape.title(layer, x, y + size * 0.9, p.sub.text, { size: p.sub.size || 64, color: p.sub.color }) : null;
      return { words: words, chars: chars, sub: sub };
    },
    actions: {
      slam: function (tl, st, t, a) {
        var sg = a.stagger == null ? 0.12 : a.stagger;
        st.words.forEach(function (w, i) {
          tl.fromTo(w, { scale: 1.6, opacity: 0, y: -30 }, { scale: 1, opacity: 1, y: 0, duration: 0.18, ease: "power4.out" }, t + i * sg);
        });
        T.actions.shake(tl, st, t + (st.words.length - 1) * sg + 0.12, { amp: 6 });
      },
      type: function (tl, st, t, a) {
        var cps = a.cps || 16;
        st.chars.forEach(function (c, i) { tl.set(c, { opacity: 0 }, 0); tl.set(c, { opacity: 1 }, t + i / cps); });
      },
      sub: function (tl, st, t) { if (st.sub) T.pop(tl, st.sub, t); },
      out: function (tl, st, t) {
        st.words.forEach(function (w) { tl.to(w, { scale: 0.8, opacity: 0, duration: 0.25, ease: "power2.in" }, t); });
        if (st.sub) T.out(tl, st.sub, t);
      }
    }
  };
})();
