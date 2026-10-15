// TOON.shape, part 1: code-drawn pieces of the style. Sizes in px, colours are palette roles or hex.
// SVG ids are made unique on the assembled page with TOON.hash(key).
(function () {
  var T = window.TOON, S = T.shape;

  // 4-point star with concave sides (quadratic curves through the centre).
  S.sparkle = function (svg, x, y, r, fill) {
    var q = "Q" + x + "," + y + " ";
    var d = "M" + x + "," + (y - r) + q + (x + r) + "," + y + q + x + "," + (y + r) + q + (x - r) + "," + y + q + x + "," + (y - r) + "Z";
    return T.el("path", { d: d, fill: T.c(fill || "text") }, svg);
  };

  // A planet bubble: disc, texture clipped to it, a circular content slot, a white rim on top.
  S.bubble = function (parent, x, y, r, o) {
    o = o || {};
    var it = T.item(parent, x, y, 2 * r, 2 * r, 0.5, 0.5), s = T.svg(it.inner, 2 * r, 2 * r), rnd = T.rng(o.seed || 1);
    var id = "bc" + T.hash(o.key || [x, y, r].join(",")), rr = r * 0.97;
    T.el("circle", { cx: r, cy: r, r: rr, fill: T.c(o.fill || "panel") }, s);
    if (o.texture !== "none") {
      var clip = T.el("clipPath", { id: id }, T.el("defs", {}, s));
      T.el("circle", { cx: r, cy: r, r: rr }, clip);
      var tex = T.el("g", { "clip-path": "url(#" + id + ")", fill: T.c(o.mark || "bgLight"), opacity: 0.45 }, s);
      if (o.texture === "stripes") {
        var g = T.el("g", { transform: "rotate(35 " + r + " " + r + ")" }, tex);
        for (var i = -4; i <= 4; i++) T.el("rect", { x: r + i * r * 0.46 - r * 0.11, y: -r, width: r * 0.22, height: 4 * r }, g);
      } else {
        for (var k = 0; k < 7; k++) {
          T.el("ellipse", { cx: rnd() * 2 * r, cy: rnd() * 2 * r, rx: r * (0.12 + rnd() * 0.22), ry: r * (0.1 + rnd() * 0.18) }, tex);
        }
      }
    }
    var content = T.el("div", { style: "position:absolute;left:" + (r - rr) + "px;top:" + (r - rr) + "px;width:" + 2 * rr +
      "px;height:" + 2 * rr + "px;border-radius:50%;overflow:hidden;", "data-layout-allow-overflow": "" }, it.inner);
    T.el("circle", { cx: r, cy: r, r: rr, fill: "none", stroke: T.c(o.rim || "rim"), "stroke-width": Math.max(3, r * 0.035) },
      T.svg(it.inner, 2 * r, 2 * r));
    return { el: it.el, inner: it.inner, content: content, r: r, x: x, y: y };
  };

  // Glow + n wedge rays (a highlight behind a bubble or the figure). Rotate the returned box.
  S.rays = function (parent, x, y, r, o) {
    o = o || {};
    var n = o.n || 12, b = T.box(parent, x, y, 2 * r, 2 * r), s = T.svg(b, 2 * r, 2 * r), col = T.c(o.color || "accent");
    var gid = "rg" + T.hash(o.key || [x, y, r].join(","));
    var g = T.el("radialGradient", { id: gid, gradientUnits: "userSpaceOnUse", cx: r, cy: r, r: r }, T.el("defs", {}, s));
    [["0%", 0.95], ["45%", 0.55], ["100%", 0]].forEach(function (st) {
      T.el("stop", { offset: st[0], "stop-color": col, "stop-opacity": st[1] }, g);
    });
    T.el("circle", { cx: r, cy: r, r: r * 0.6, fill: "url(#" + gid + ")" }, s);
    var w = Math.PI / n * 0.45, rays = T.el("g", { fill: "url(#" + gid + ")" }, s);
    for (var i = 0; i < n; i++) {
      var a = i * 2 * Math.PI / n;
      T.el("polygon", { points: [r, r, r + r * Math.cos(a - w), r + r * Math.sin(a - w), r + r * Math.cos(a + w), r + r * Math.sin(a + w)].join(",") }, rays);
    }
    return b;
  };

  function head(g, x, y, ang, hd, col) {
    var bx = x - Math.cos(ang) * hd, by = y - Math.sin(ang) * hd, nx = -Math.sin(ang) * hd * 0.55, ny = Math.cos(ang) * hd * 0.55;
    return T.el("polygon", { points: [x, y, bx + nx, by + ny, bx - nx, by - ny].join(","), fill: col }, g);
  }
  function stroke(g, x0, y0, x1, y1, w, col) {
    return T.el("path", { d: "M" + x0 + "," + y0 + "L" + x1 + "," + y1, stroke: col, "stroke-width": w, "stroke-linecap": "round",
      fill: "none", pathLength: 1, "stroke-dasharray": 1, "stroke-dashoffset": 0 }, g);
  }
  // Arrow from (x0,y0) to (x1,y1). Animate with TOON.draw(tl, a.line, t) and pop a.head.
  S.arrow = function (svg, x0, y0, x1, y1, o) {
    o = o || {};
    var col = T.c(o.color || "ink"), hd = o.head || 26, ang = Math.atan2(y1 - y0, x1 - x0), g = T.el("g", {}, svg);
    var line = stroke(g, x0, y0, x1 - Math.cos(ang) * hd * 0.6, y1 - Math.sin(ang) * hd * 0.6, o.w || 8, col);
    return { g: g, line: line, head: head(g, x1, y1, ang, hd, col) };
  };
  S.doubleArrow = function (svg, x0, y0, x1, y1, o) {
    o = o || {};
    var col = T.c(o.color || "ink"), hd = o.head || 22, ang = Math.atan2(y1 - y0, x1 - x0), g = T.el("g", {}, svg);
    var c = Math.cos(ang) * hd * 0.6, s = Math.sin(ang) * hd * 0.6;
    var line = stroke(g, x0 + c, y0 + s, x1 - c, y1 - s, o.w || 6, col);
    return { g: g, line: line, heads: [head(g, x0, y0, ang + Math.PI, hd, col), head(g, x1, y1, ang, hd, col)] };
  };

  // A centred holder: a 600x300 box around (x, y) that centres its child, so pops scale about (x, y).
  S.center = function (parent, x, y) {
    return T.el("div", { style: "position:absolute;left:" + (x - 300) + "px;top:" + (y - 150) + "px;width:600px;height:300px;" +
      "display:flex;align-items:center;justify-content:center;transform-origin:50% 50%;pointer-events:none;" }, parent);
  };
  // White card with an ink border and bold label lines ("2x12" / "3/WEEK"), tilted 3 degrees, centred on (x, y).
  S.tag = function (parent, x, y, lines, o) {
    o = o || {};
    var size = o.size || 34, b = S.center(parent, x, y);
    var card = T.el("div", { style: "transform:rotate(" + (o.rot == null ? -3 : o.rot) + "deg);background:#fff;border:4px solid " + T.c("ink") +
      ";border-radius:6px;padding:" + size * 0.28 + "px " + size * 0.45 + "px;" }, b);
    lines.forEach(function (l) {
      T.el("div", { text: l, style: "font-family:TLabel;font-weight:700;font-size:" + size + "px;line-height:1.05;color:" + T.c("ink") +
        ";white-space:nowrap;text-align:center;" }, card);
    });
    return b;
  };

  // Callout ring (hidden until TOON.draw).
  S.callout = function (svg, x, y, r, o) {
    o = o || {};
    return T.el("circle", { cx: x, cy: y, r: r, fill: "none", stroke: T.c(o.color || "bgDeep"), "stroke-width": o.w || 7,
      pathLength: 1, "stroke-dasharray": 1, "stroke-dashoffset": 1, transform: "rotate(-90 " + x + " " + y + ")" }, svg);
  };

  // Flame aura: a solid body with 9 spiky tongues on top, an inner lighter flame, rising from `base`.
  S.flame = function (svg, cx, base, w, h, seed, o) {
    o = o || {};
    var rnd = T.rng(seed || 1), n = 9, x0 = cx - w / 2, g = T.el("g", {}, svg), d = "M" + x0 + "," + base;
    for (var i = 0; i < n; i++) {
      var u0 = i / n, u1 = (i + 1) / n, um = (i + 0.5) / n, env = Math.sin(Math.PI * um);
      var valley = base - h * (0.5 + 0.3 * Math.sin(Math.PI * u0)), tip = base - h * (0.72 + 0.28 * env) * (0.9 + 0.2 * rnd());
      d += "L" + (x0 + u0 * w) + "," + valley + "Q" + (x0 + um * w) + "," + (valley - h * 0.05) + " " +
        (x0 + (um + (rnd() - 0.5) * 0.04) * w) + "," + tip + "Q" + (x0 + (um + 0.1 / n) * w) + "," + (valley - h * 0.04) + " " +
        (x0 + u1 * w) + "," + (base - h * (0.5 + 0.3 * Math.sin(Math.PI * u1)));
    }
    d += "L" + (cx + w / 2) + "," + base + "Z";
    T.el("path", { d: d, fill: T.c(o.color || "bgDeep"), stroke: T.c("ink"), "stroke-width": 4, "stroke-linejoin": "round" }, g);
    T.el("path", { d: d, fill: T.c(o.color2 || "bgLight"), opacity: 0.55,
      transform: "translate(" + cx + "," + base + ") scale(0.62,0.6) translate(" + -cx + "," + -base + ")" }, g);
    return g;
  };

  // Lightning bolt: a 6-segment zigzag polygon tapering to its tip at (x1, y1).
  S.bolt = function (svg, x0, y0, x1, y1, seed, o) {
    o = o || {};
    var rnd = T.rng(seed || 1), n = 6, w = o.w || 10, dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L, pts = [];
    for (var i = 0; i <= n; i++) {
      var off = (i % 2 ? 1 : -1) * L * 0.07 * (0.5 + rnd()) * (i && i < n ? 1 : 0);
      pts.push([x0 + dx * i / n + nx * off, y0 + dy * i / n + ny * off]);
    }
    var side = function (p, i, sgn) { var k = sgn * w * (1 - i / n) / 2 + sgn * 1; return (p[0] + nx * k) + "," + (p[1] + ny * k); };
    var left = pts.map(function (p, i) { return side(p, i, 1); });
    var right = pts.map(function (p, i) { return side(p, i, -1); }).reverse();
    return T.el("polygon", { points: left.concat(right).join(" "), fill: T.c(o.color || "accent"), stroke: T.c("ink"),
      "stroke-width": 3, "stroke-linejoin": "round" }, svg);
  };
})();
