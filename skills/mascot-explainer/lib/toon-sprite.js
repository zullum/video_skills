// TOON sprite player: every frame of a traced sprite is an <img> stacked in one box (sprite-video's cell
// coordinates); exactly one is visible, switched with tl.set on the timeline (seek-safe).
(function () {
  var T = window.TOON;

  // {x, y} is where the anchor of the cell lands (default: the floor line, or the bottom centre); h = cell height.
  T.sprite = function (parent, name, o) {
    var s = T.manifest.sprites[name]; if (!s) throw new Error("unknown sprite " + name);
    var k = o.h / s.cell[1], w = s.cell[0] * k;
    var an = o.anchor || [0.5, s.floor ? s.floor[0] / s.cell[1] : 1];
    var b = T.box(parent, o.x, o.y, w, o.h, an[0], an[1]);
    var imgs = s.frames.map(function (f, i) {
      return T.el("img", { src: s.dir + "/" + f.file, style: "position:absolute;left:" + f.x * k + "px;top:" + f.y * k + "px;width:" +
        f.w * k + "px;height:" + f.h * k + "px;opacity:" + (i ? 0 : 1) + ";" }, b);
    });
    return { el: b, imgs: imgs, cur: 0, k: k };
  };

  // Frames must be scheduled in time order (sp.cur tracks the frame on screen at the latest scheduled time).
  T.show = function (tl, sp, i, t) {
    if (i === sp.cur) return;
    tl.set(sp.imgs[sp.cur], { opacity: 0 }, t);
    tl.set(sp.imgs[i], { opacity: 1 }, t);
    sp.cur = i;
  };

  // seq = [[frame, holdFrames], ...] (sprite-video's format). Returns the end time.
  T.playSeq = function (tl, sp, t0, seq, fps) {
    var t = t0; fps = fps || 30;
    seq.forEach(function (p) { T.show(tl, sp, p[0], t); t += p[1] / fps; });
    return t;
  };

  // Whole cycles of `rep` that fit before t1, then rest on the first frame.
  T.playReps = function (tl, sp, t0, t1, rep, fps) {
    fps = fps || 30;
    var len = rep.reduce(function (s, p) { return s + p[1]; }, 0) / fps, t = t0;
    while (len > 0 && t + len <= t1 + 1e-6) t = T.playSeq(tl, sp, t, rep, fps);
    T.show(tl, sp, rep[0][0], t);
    return t;
  };
})();
