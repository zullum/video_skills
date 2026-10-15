// TOON.shape, part 2: badges and cards (HTML boxes, so they can pop, fly and spin).
(function () {
  var T = window.TOON, S = T.shape;

  // CSS of the two fonts: o.font "display" (TDisplay 800 italic, default) or "label" (TLabel 700).
  S.font = function (o) {
    var label = o.font === "label";
    return "font-family:" + (label ? "TLabel" : "TDisplay") + ";font-weight:" + (label ? 700 : 800) + ";font-style:" +
      (label ? "normal" : "italic") + ";font-size:" + (o.size || 96) + "px;line-height:1;color:" + T.c(o.color || "text") + ";white-space:nowrap;";
  };
  // A line of text centred on (x, y) (pop the returned holder).
  S.title = function (parent, x, y, text, o) {
    o = o || {};
    var b = S.center(parent, x, y);
    T.el("div", { text: o.upper === false ? text : String(text).toUpperCase(), style: S.font(o) }, b);
    return b;
  };

  function disc(parent, x, y, r, fill, border) {
    var b = T.box(parent, x, y, 2 * r, 2 * r), s = T.svg(b, 2 * r, 2 * r);
    T.el("circle", { cx: r, cy: r, r: r - border / 2, fill: T.c(fill), stroke: T.c("ink"), "stroke-width": border }, s);
    return { b: b, s: s };
  }
  function glyph(b, text, size, color) {
    T.el("div", { text: text, style: "position:absolute;left:0;top:0;width:100%;height:100%;display:flex;align-items:center;" +
      "justify-content:center;font-family:TDisplay;font-weight:800;font-style:italic;line-height:1;font-size:" + size + "px;color:" + T.c(color) + ";" }, b);
  }

  // Thought bubble with a symbol ("?"), two trailing dots down-left.
  S.think = function (parent, x, y, r, symbol) {
    var d = disc(parent, x, y, r, "#ffffff", 4);
    d.s.style.overflow = "visible";
    T.el("circle", { cx: r * 0.5, cy: r * 2.15, r: r * 0.2, fill: "#fff", stroke: T.c("ink"), "stroke-width": 3 }, d.s);
    T.el("circle", { cx: r * 0.22, cy: r * 2.5, r: r * 0.12, fill: "#fff", stroke: T.c("ink"), "stroke-width": 3 }, d.s);
    glyph(d.b, symbol || "?", r * 1.25, "ink");
    return d.b;
  };

  // Gold coin with "$".
  S.coin = function (parent, x, y, r) {
    var d = disc(parent, x, y, r, "accent", 4);
    glyph(d.b, "$", r * 1.2, "ink");
    return d.b;
  };

  // Round badge with a short text ("15 MIN", "3x12").
  S.badge = function (parent, x, y, r, text) {
    var d = disc(parent, x, y, r, "#ffffff", 5);
    glyph(d.b, text, r * (String(text).length > 3 ? 0.5 : 0.8), "ink");
    return d.b;
  };

  // Bookmark ribbon icon, s = height.
  S.bookmark = function (parent, x, y, s) {
    var w = s * 0.72, b = T.box(parent, x, y, w, s), v = T.svg(b, w, s), k = 4;
    T.el("path", { d: "M" + k + "," + k + "H" + (w - k) + "V" + (s - k) + "L" + w / 2 + "," + (s * 0.68) + "L" + k + "," + (s - k) + "Z",
      fill: "#fff", stroke: T.c("ink"), "stroke-width": 4, "stroke-linejoin": "round" }, v);
    return b;
  };

  // Pause badge: white disc, thick ink ring, two bars.
  S.pauseIcon = function (parent, x, y, r) {
    var d = disc(parent, x, y, r, "#ffffff", r * 0.09), bw = r * 0.2, bh = r * 0.9;
    [-1, 1].forEach(function (k) {
      T.el("rect", { x: r + k * r * 0.24 - bw / 2, y: r - bh / 2, width: bw, height: bh, rx: bw * 0.15, fill: T.c("ink") }, d.s);
    });
    return d.b;
  };

  // Thumbnail card (walls, phone feeds): coloured panel, ink border, optional figure, a shouty title.
  S.card = function (parent, x, y, w, h, o) {
    o = o || {};
    var b = T.box(parent, x, y, w, h);
    var face = T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:100%;border:5px solid " + T.c("ink") +
      ";border-radius:10px;overflow:hidden;background:" + T.c(o.fill || "bgMid") + ";transform:rotate(" + (o.rot || 0) + "deg);" }, b);
    if (o.asset) T.img(face, o.asset, { x: w * 0.72, y: h * 1.02, h: h * 0.95 });
    if (o.title) {
      T.el("div", { text: String(o.title).toUpperCase(), style: "position:absolute;left:" + w * 0.06 + "px;top:" + h * 0.08 + "px;width:" + w * 0.62 +
        "px;font-family:TDisplay;font-weight:800;font-style:italic;line-height:0.95;font-size:" + h * 0.22 + "px;color:#fff;" +
        "-webkit-text-stroke:" + Math.max(2, h * 0.012) + "px " + T.c("ink") + ";paint-order:stroke fill;" }, face);
    }
    return b;
  };
})();
