// @actions push,zoomInto,flash,shake,fadeOut
// TOON: the runtime every mascot-explainer scene shares. Everything goes on the scene's one paused GSAP
// timeline, so any frame renders on its own (seek-safe): seeded random only, no clocks, no CSS animations.
(function () {
  var NS = "http://www.w3.org/2000/svg";
  var SVG_TAGS = /^(svg|g|path|circle|ellipse|rect|line|polyline|polygon|text|tspan|defs|clipPath|mask|radialGradient|linearGradient|stop|filter|feGaussianBlur|use)$/;
  var T = window.TOON = { scene: {}, actions: {}, shape: {}, style: null, manifest: { assets: {}, sprites: {} }, W: 1920, H: 1080 };

  T.init = function (style, manifest) {
    T.style = style; T.manifest = manifest || T.manifest;
    T.W = style.size[0]; T.H = style.size[1];
  };
  T.c = function (role) { return ((T.style && T.style.palette) || {})[role] || role; };
  T.rng = function (seed) {                                   // mulberry32
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0; var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  T.hash = function (s) {                                     // FNV-1a
    var h = 2166136261; s = String(s);
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  };
  T.el = function (tag, attrs, parent) {
    var e = SVG_TAGS.test(tag) ? document.createElementNS(NS, tag) : document.createElement(tag);
    for (var k in (attrs || {})) {
      if (k === "style") e.style.cssText = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    if (parent) parent.appendChild(e);
    return e;
  };
  T.layer = function (parent) {
    return T.el("div", { style: "position:absolute;left:0;top:0;width:" + T.W + "px;height:" + T.H + "px;" }, parent);
  };
  T.svg = function (parent, w, h) {
    w = w || T.W; h = h || T.H;
    return T.el("svg", { width: w, height: h, viewBox: "0 0 " + w + " " + h, style: "position:absolute;left:0;top:0;overflow:visible;" }, parent);
  };
  // A box whose anchor point (ax, ay as fractions) sits at (x, y); scale and rotation pivot there too.
  T.box = function (parent, x, y, w, h, ax, ay) {
    ax = ax == null ? 0.5 : ax; ay = ay == null ? 0.5 : ay;
    return T.el("div", { style: "position:absolute;left:" + (x - w * ax) + "px;top:" + (y - h * ay) + "px;width:" + w +
      "px;height:" + h + "px;transform-origin:" + ax * 100 + "% " + ay * 100 + "%;" }, parent);
  };
  // Pop, fly and scale act on `el`; bob and dim act on `inner`, which holds the content.
  T.item = function (parent, x, y, w, h, ax, ay) {
    var el = T.box(parent, x, y, w, h, ax, ay);
    return { el: el, inner: T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:100%;" }, el) };
  };
  T.img = function (parent, name, o) {
    var a = T.manifest.assets[name]; if (!a) throw new Error("unknown asset " + name);
    var h = o.h || (o.w ? o.w * a.h / a.w : a.h), w = h * a.w / a.h, an = o.anchor || a.anchor;
    var b = T.box(parent, o.x, o.y, w, h, an[0], an[1]);
    T.el("img", { src: a.file, style: "position:absolute;left:0;top:0;width:100%;height:100%;" + (o.flip ? "transform:scaleX(-1);" : "") }, b);
    return b;
  };
  T.text = function (parent, str, o) {
    var label = o.font === "label", size = o.size || 96, center = o.align !== "left";
    var e = T.el("div", { text: o.upper === false ? str : String(str).toUpperCase(), style: "position:absolute;white-space:nowrap;line-height:1;" +
      "font-family:" + (label ? "TLabel" : "TDisplay") + ";font-weight:" + (label ? 700 : 800) + ";font-style:" + (label ? "normal" : "italic") +
      ";font-size:" + size + "px;color:" + T.c(o.color || "text") + ";top:" + (o.y - size * 0.55) + "px;" +
      (center ? "left:" + (o.x - 2000) + "px;width:4000px;text-align:center;" : "left:" + o.x + "px;") }, parent);
    return e;
  };

  // Motion. An element that pops is hidden until its pop (fromTo renders its start state at once).
  T.pop = function (tl, el, t, o) {
    o = o || {};
    tl.fromTo(el, { scale: 0, opacity: 0, filter: "blur(" + (o.blur == null ? 6 : o.blur) + "px)" },
      { scale: 1, opacity: 1, filter: "blur(0px)", duration: o.dur || 0.35, ease: "back.out(" + (o.back || 1.6) + ")" }, t);
    return tl;
  };
  T.out = function (tl, el, t, o) {
    o = o || {};
    tl.to(el, { scale: o.scale == null ? 0.6 : o.scale, opacity: 0, duration: o.dur || 0.25, ease: "power2.in" }, t);
    return tl;
  };
  T.bob = function (tl, el, t0, t1, o) {
    o = o || {};
    var amp = o.amp == null ? 6 : o.amp, half = (o.period || 3.6) / 2, n = Math.max(1, Math.floor((t1 - t0) / half));
    tl.fromTo(el, { y: -amp }, { y: amp, duration: half, ease: "sine.inOut", repeat: n - 1, yoyo: true }, t0);
    return tl;
  };
  T.draw = function (tl, el, t, dur) {                        // el needs pathLength="1" stroke-dasharray="1"
    tl.fromTo(el, { attr: { "stroke-dashoffset": 1 } }, { attr: { "stroke-dashoffset": 0 }, duration: dur || 0.4, ease: "power2.out" }, t);
    return tl;
  };
  function overlay(stage, color) {
    return T.el("div", { style: "position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;background:" + T.c(color || "#ffffff") + ";" }, stage);
  }

  var ENTER = {
    pop: function (tl, cam) { tl.fromTo(cam, { scale: 1.06 }, { scale: 1, duration: 0.3, ease: "power2.out" }, 0); },
    zoomIn: function (tl, cam) { tl.fromTo(cam, { scale: 1.35, filter: "blur(10px)" }, { scale: 1, filter: "blur(0px)", duration: 0.45, ease: "power3.out" }, 0); },
    whip: function (tl, cam) { tl.fromTo(cam, { x: -T.W * 0.25, filter: "blur(24px)" }, { x: 0, filter: "blur(0px)", duration: 0.3, ease: "power3.out" }, 0); },
    flash: function (tl, cam, stage) { tl.fromTo(overlay(stage), { opacity: 1 }, { opacity: 0, duration: 0.35, ease: "power2.out" }, 0); }
  };
  var EXIT = {
    whip: function (tl, cam, stage, dur) { tl.to(cam, { x: T.W * 0.25, filter: "blur(24px)", duration: 0.22, ease: "power2.in" }, dur - 0.22); },
    flash: function (tl, cam, stage, dur) { tl.fromTo(overlay(stage), { opacity: 0 }, { opacity: 1, duration: 0.12, ease: "none" }, dur - 0.12); }
  };

  // A push-in on its own layer (zoom): the idle camera drift tweens rig.scale for the whole shot, and two live
  // tweens on one property make the frame depend on the order frames are rendered in.
  T.actions.push = function (tl, st, t, a) {
    st.zoom.style.transformOrigin = (a.x == null ? T.W / 2 : a.x) + "px " + (a.y == null ? T.H / 2 : a.y) + "px";
    tl.fromTo(st.zoom, { scale: 1 }, { scale: a.to || 1.12, duration: a.dur || 1.2, ease: a.ease || "power2.inOut" }, t);
  };
  T.actions.zoomInto = function (tl, st, t, a) {
    tl.set(st.cam, { transformOrigin: a.x + "px " + a.y + "px" }, t);
    tl.to(st.cam, { scale: a.scale || 6, filter: "blur(8px)", duration: a.dur || 0.5, ease: "power2.in" }, t);
  };
  T.actions.flash = function (tl, st, t, a) {
    var f = overlay(st.stage, a.color);
    tl.fromTo(f, { opacity: 0 }, { opacity: 0.9, duration: 0.06, ease: "none" }, t).to(f, { opacity: 0, duration: 0.3 }, t + 0.06);
  };
  T.actions.shake = function (tl, st, t, a) {
    tl.fromTo(st.rig, { x: 0 }, { x: a.amp || 8, duration: 0.04, repeat: 5, yoyo: true, ease: "none" }, t).set(st.rig, { x: 0 }, t + 0.24);
  };
  T.actions.fadeOut = function (tl, st, t, a) { tl.to(st.rig, { opacity: 0, duration: a.dur || 0.3 }, t); };

  T.run = function (id, shot, dur) {
    var stage = document.getElementById(id + "-stage"), tl = gsap.timeline({ paused: true });
    var S = T.scene[shot.scene]; if (!S) throw new Error(id + ": unknown scene " + shot.scene);
    var p = shot.params || {}, cam = T.layer(stage), zoom = T.layer(cam), rig = T.layer(zoom);
    var ctx = { id: id, dur: dur, tl: tl, rng: T.rng(T.hash(id)) };
    var st = S.build(rig, p, ctx) || {}; st.cam = cam; st.zoom = zoom; st.rig = rig; st.stage = stage; st.dur = dur; st.ctx = ctx;
    if (p.push !== 0) tl.fromTo(rig, { scale: 1 }, { scale: p.push || 1.03, duration: dur, ease: "none" }, 0);
    if (S.idle) S.idle(tl, st, dur);
    if (ENTER[shot["in"]]) ENTER[shot["in"]](tl, cam, stage);
    (shot.beats || []).forEach(function (b) {
      var fn = (S.actions || {})[b.do] || T.actions[b.do];
      if (!fn) throw new Error(id + ": " + shot.scene + " has no action " + b.do);
      fn(tl, st, b.t, b.args || {});
    });
    if (EXIT[shot.out]) EXIT[shot.out](tl, cam, stage, dur);
    tl.set({}, {}, dur);
    return tl;
  };
})();
