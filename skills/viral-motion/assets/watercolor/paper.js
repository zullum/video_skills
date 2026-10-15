// Watercolor (references/watercolor.md): window.PAPER, the paper for index.html. Needs scene.js.
// A near-white sheet (cockle blotches + cold-press tooth + specks + fibres), multiplied
// over every Shot, so all paint looks like it sits in the same paper. Seeded, built once.
(function () {
  // Smooth value noise on a grid of cell-size `cs`, sampled bilinearly (smoothstep).
  function lattice(rnd, cs, W, H) {
    var nx = Math.ceil(W / cs) + 2, ny = Math.ceil(H / cs) + 2, g = new Float32Array(nx * ny);
    for (var i = 0; i < g.length; i++) g[i] = rnd();
    return function (x, y) {
      var fx = x / cs, fy = y / cs, x0 = fx | 0, y0 = fy | 0, tx = fx - x0, ty = fy - y0;
      tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
      var a = g[y0 * nx + x0], b = g[y0 * nx + x0 + 1], c = g[(y0 + 1) * nx + x0], d = g[(y0 + 1) * nx + x0 + 1];
      return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty;
    };
  }

  function paint(canvas, seed) {
    var W = canvas.width, H = canvas.height, ctx = canvas.getContext("2d");
    var rnd = window.SCENE.mulberry32(seed);
    var cockle = lattice(rnd, 260, W, H), blotch = lattice(rnd, 48, W, H), tooth = lattice(rnd, 4, W, H);
    var img = ctx.createImageData(W, H), d = img.data;
    for (var y = 0; y < H; y++) {
      for (var x = 0; x < W; x++) {
        var s = rnd(), v = 1 - 0.05 * cockle(x, y) - 0.035 * blotch(x, y) - 0.07 * tooth(x, y)
          - (s > 0.985 ? 0.12 * rnd() : 0);
        var i = (y * W + x) * 4;
        d[i] = 255 * v; d[i + 1] = 251 * v; d[i + 2] = 244 * v; d[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    ctx.strokeStyle = "rgba(110,92,70,0.06)"; ctx.lineWidth = 1;
    for (var f = 0; f < 1400; f++) { // paper fibres
      var fx = rnd() * W, fy = rnd() * H, a = rnd() * 6.2832, l = 8 + rnd() * 30;
      ctx.beginPath(); ctx.moveTo(fx, fy);
      ctx.quadraticCurveTo(fx + Math.cos(a + 0.6) * l * 0.5, fy + Math.sin(a + 0.6) * l * 0.5,
        fx + Math.cos(a) * l, fy + Math.sin(a) * l);
      ctx.stroke();
    }
  }

  window.PAPER = { paint: paint };
})();
