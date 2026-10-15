// @scene phone @actions scroll,icons,swipe,out
// A phone held into frame: a traced hand-with-phone asset whose screen is a hole (manifest holes[0]), or a
// code-drawn phone. Its screen shows a scrolling feed, an app, a video or a colour; bookmarks can fly out of it.
(function () {
  var T = window.TOON;

  function codePhone(layer, x, y, h) {
    var w = h * 0.48, body = T.el("div", { style: "position:absolute;left:" + (x - w / 2) + "px;top:" + (y - h / 2) + "px;width:" + w +
      "px;height:" + h + "px;border-radius:" + w * 0.12 + "px;background:#111;border:12px solid " + T.c("ink") + ";" }, layer);
    var i = 18, rect = [x - w / 2 + 12 + i, y - h / 2 + 12 + i, w - 24 - 2 * i, h - 24 - 2 * i];
    return { body: body, rect: rect, notch: [x - w * 0.12, y - h / 2 + 12 + i + 8, w * 0.24, 18] };
  }

  function screenContent(scr, s, w, h) {
    var kind = s.kind || "color";
    scr.style.background = T.c(kind === "app" ? "#ffffff" : kind === "video" ? "ink" : (s.color || "panel"));
    if (kind === "feed") {
      var col = T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:100%;" }, scr), cw = w * 0.9, ch = cw * 9 / 16;
      (s.cards || []).forEach(function (c, i) {
        T.shape.card(col, w / 2, 14 + ch / 2 + i * (ch + 14), cw, ch, { fill: c.fill, title: c.title, asset: c.asset });
      });
      return col;
    }
    if (kind === "app") {
      T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:" + h * 0.18 + "px;background:" + T.c("accent") + ";" }, scr);
      if (s.title) T.shape.title(scr, w / 2, h * 0.1, s.title, { size: w * 0.13, color: "ink" });
      if (s.asset) T.img(scr, s.asset, { x: w / 2, y: h * 0.62, h: h * 0.4, anchor: [0.5, 0.5] });
      T.el("div", { style: "position:absolute;left:" + w * 0.15 + "px;top:" + h * 0.88 + "px;width:" + w * 0.7 + "px;height:" + h * 0.07 +
        "px;border-radius:" + h * 0.035 + "px;background:" + T.c("accent") + ";border:4px solid " + T.c("ink") + ";" }, scr);
    }
    if (kind === "video") {
      if (s.asset) T.img(scr, s.asset, { x: w / 2, y: h * 0.5, h: h * 0.5, anchor: [0.5, 0.5] });
      T.el("div", { style: "position:absolute;left:8%;top:76%;width:84%;height:6px;background:#555;" }, scr);
      T.el("div", { style: "position:absolute;left:8%;top:76%;width:38%;height:6px;background:#E63946;" }, scr);
      T.el("div", { text: "♥", style: "position:absolute;right:8%;top:58%;font-size:" + w * 0.14 + "px;color:#E63946;" }, scr);
    }
    return null;
  }

  T.scene.phone = {
    build: function (rig, p, ctx) {
      T.backdrop(rig, p.tone || "mid", ctx, p.flat === false ? p.density : 0);
      var x = p.x == null ? T.W / 2 : p.x, y = p.y == null ? 560 : p.y, h = p.h || 900;
      var wrap = T.layer(rig), rect, phone = null, notch = null;
      wrap.style.transformOrigin = x + "px " + y + "px";
      if (p.rot) wrap.style.transform = "rotate(" + p.rot + "deg)";
      if (p.hand) {
        var a = T.manifest.assets[p.hand], hw = h * a.w / a.h, hole = (a.holes || [])[0] || [0.3, 0.1, 0.4, 0.6];
        var left = x - hw * a.anchor[0], top = y - h * a.anchor[1];
        rect = [left + hole[0] * hw, top + hole[1] * h, hole[2] * hw, hole[3] * h];
      } else {
        phone = codePhone(wrap, x, y, h); rect = phone.rect; notch = phone.notch;
      }
      var scr = T.el("div", { style: "position:absolute;left:" + rect[0] + "px;top:" + rect[1] + "px;width:" + rect[2] + "px;height:" + rect[3] +
        "px;overflow:hidden;border-radius:" + rect[2] * 0.06 + "px;", "data-layout-allow-overflow": "" }, wrap);
      var feed = screenContent(scr, p.screen || {}, rect[2], rect[3]);
      if (notch) T.el("div", { style: "position:absolute;left:" + notch[0] + "px;top:" + notch[1] + "px;width:" + notch[2] + "px;height:" + notch[3] +
        "px;border-radius:9px;background:#111;" }, wrap);
      if (p.hand) T.img(wrap, p.hand, { x: x, y: y, h: h });
      return { wrap: wrap, scr: scr, sw: rect[2], feed: feed, x: x, y: y, h: h, top: T.layer(rig) };
    },
    actions: {
      scroll: function (tl, st, t, a) {
        if (st.feed) tl.to(st.feed, { y: -(a.dist || 600), duration: a.dur || 1.2, ease: "power1.inOut" }, t);
      },
      icons: function (tl, st, t, a) {
        var n = a.n || 8, R = st.h * 0.6, s = st.h * 0.11;
        for (var i = 0; i < n; i++) {
          var ang = -Math.PI / 2 + i * 2 * Math.PI / n, b = T.shape.bookmark(st.top, st.x, st.y, s);
          tl.fromTo(b, { x: 0, y: 0, scale: 0, rotation: 0 }, { x: Math.cos(ang) * R, y: Math.sin(ang) * R * 0.8, scale: 1,
            rotation: (i % 2 ? 1 : -1) * 18, duration: 0.5, ease: "back.out(1.4)" }, t + i * (a.stagger == null ? 0.06 : a.stagger));
        }
      },
      swipe: function (tl, st, t, a) {
        var target = st.feed || st.scr.firstChild;
        if (target) tl.to(target, { x: (a.dir === "right" ? 1 : -1) * st.sw, duration: 0.35, ease: "power2.in" }, t);
      },
      out: function (tl, st, t) { tl.to(st.wrap, { opacity: 0, duration: 0.25 }, t); }
    }
  };
})();
