// The generic "item" beat (listed in toon-core.js's @actions line, so every scene has it): a small asset from the
// item sheet or a hand-written SVG enters the shot on its word, may float or turn while it stays, and may leave.
//   {"do": "item", "args": {"asset": "camera", "x": 1500, "y": 320, "h": 240, "in": "pop|fly|drop|spin",
//    "from": [x, y] (fly), "rot": 0, "turn": 0, "float": false, "out": seconds}}
// Entrances move the box; the float and the turn move the picture inside it (two tweens never share a property).
(function () {
  var T = window.TOON;
  var ENTER = {
    pop: function (tl, b, t) { T.pop(tl, b, t, { dur: 0.35 }); },
    fly: function (tl, b, t, a) {
      var f = a.from || [-200, a.y];
      tl.fromTo(b, { x: f[0] - a.x, y: f[1] - a.y, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, t);
    },
    drop: function (tl, b, t, a) {
      tl.fromTo(b, { y: -(a.y + a.h), opacity: 1 }, { y: 0, duration: 0.7, ease: "bounce.out" }, t);
    },
    spin: function (tl, b, t) {
      tl.fromTo(b, { scale: 0, rotation: -360, opacity: 0 }, { scale: 1, rotation: 0, opacity: 1, duration: 0.6, ease: "back.out(1.4)" }, t);
    }
  };

  T.actions.item = function (tl, st, t, a) {
    if (!ENTER[a.in || "pop"]) throw new Error(st.ctx.id + ": item has no entrance " + a.in);
    var layer = st.itemLayer || (st.itemLayer = T.layer(st.rig));      // above the scene, moves with its camera
    var h = a.h || 200, b = T.img(layer, a.asset, { x: a.x, y: a.y, h: h });
    var pic = b.firstChild, end = a.out ? Math.min(st.dur, t + a.out) : st.dur;
    if (a.rot) tl.set(pic, { rotation: a.rot }, 0);
    ENTER[a.in || "pop"](tl, b, t, { x: a.x, y: a.y, h: h, from: a.from });
    if (a.float) T.bob(tl, pic, t + 0.6, end, { amp: Math.max(4, h * 0.03), period: 2.4 });
    if (a.turn) tl.fromTo(pic, { rotation: a.rot || 0 }, { rotation: (a.rot || 0) + a.turn, duration: Math.max(0.1, end - t), ease: "none" }, t);
    if (a.out) T.out(tl, b, end);
  };
})();
