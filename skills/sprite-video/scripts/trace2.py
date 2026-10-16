# Two-layer vectorizer for flat cartoon frames (round 9): the black ink is traced with potrace from a
# 4x supersampled darkness map (smooth Bezier outlines, sub-pixel accurate), the colour fills are traced
# with vtracer from a 2x smoothed, palette-snapped image with the ink pushed out (fills run under the
# lines, so no gaps). Edges stay sharp at any output size, e.g. 3840x2160 from a 2K grid cell.
import re, io, numpy as np, potrace, vtracer, tempfile, os
from PIL import Image, ImageFilter
from scipy import ndimage
INK = "#141418"
def _near(rgb, keep):                                                # distance to the nearest kept dark fill colour
    c = rgb[..., :3].astype(int)
    return np.min([np.abs(c - np.array(k)).max(2) for k in keep], 0)
def ink_paths(rgb, up=4, lo=45, hi=95, ink_keep=None):
    L = rgb[..., :3] @ np.array([.299, .587, .114])
    dark = np.clip((hi - L) / (hi - lo), 0, 1)                      # 1 = line, 0 = fill
    if ink_keep:                                                     # a dark fill colour (navy shorts) is not ink
        dark *= np.clip((_near(rgb, ink_keep) - 24) / 16, 0, 1)
    big = np.array(Image.fromarray((dark * 255).astype("uint8")).resize(
        (rgb.shape[1] * up, rgb.shape[0] * up), Image.BICUBIC)).astype(float)
    big = ndimage.gaussian_filter(big, up * .9) > 127                   # blur before threshold: no edge ripple
    big = ndimage.binary_opening(big, iterations=1)
    return f'<path fill="{INK}" fill-rule="evenodd" d="{_outline(big, up)}"/>'
def _outline(mask, up):                                              # True pixels -> SVG path data (1/up px)
    plist = potrace.Bitmap(~mask).trace(  # potracer fills the False pixels
        turdsize=up * up * 3, alphamax=1.2, opticurve=True, opttolerance=0.4)
    f = lambda p: f"{p.x / up:.2f},{p.y / up:.2f}"
    d = []
    for c in plist:
        d.append("M" + f(c.start_point))
        for s in c.segments:
            d.append(("L" + f(s.c) + "L" + f(s.end_point)) if s.is_corner else
                     ("C" + f(s.c1) + " " + f(s.c2) + " " + f(s.end_point)))
        d.append("Z")
    return "".join(d)
def clip_def(rgb, bg, up=4):
    # Figure mask (same test as slice.py) eroded 2 px, so the clip edge hides under the ink outline and no
    # background-coloured fill survives outside the figure or inside its holes.
    m = np.abs(rgb[..., :3].astype(int) - np.array(bg)).sum(2) > 70
    m = ndimage.binary_erosion(ndimage.binary_opening(m, iterations=1), iterations=2)
    big = np.array(Image.fromarray((m * 255).astype("uint8")).resize(
        (rgb.shape[1] * up, rgb.shape[0] * up), Image.BICUBIC)) > 127
    return f'<clipPath id="fig"><path clip-rule="evenodd" d="{_outline(big, up)}"/></clipPath>'
def palette(art, bg, n=14, extra=6, miss=80, twin=30):
    # one palette for a sheet: ink, white, the background, n median-cut colours of the art pixels (minus near-twins
    # closer than `twin` to an earlier entry: sheet noise split one flat skin into mottled patches), then up to
    # `extra` colours, one per round: the commonest colour (32-level bins) of the art pixels still more than `miss`
    # (summed RGB) from every entry, while it covers 0.3 % of the art. The cut weighs by area: on a blue sheet it
    # spent its slots on near-identical blues and merged a small red headband into navy, a blue hand into grey.
    art = np.asarray(art, "uint8").reshape(-1, 3)
    cut = Image.fromarray(art.reshape(1, -1, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT).getpalette()[:3 * n]
    cols = [18, 18, 22, 255, 255, 255, *(int(v) for v in bg)]
    for c in np.array(cut).reshape(-1, 3):
        if np.abs(np.array(cols).reshape(-1, 3) - c).sum(1).min() >= twin:
            cols += [int(v) for v in c]
    s = art[::max(1, len(art) // 100000)].astype(int)
    for _ in range(extra):
        far = s[np.abs(s[:, None] - np.array(cols).reshape(-1, 3)[None]).sum(2).min(1) > miss]
        if not len(far):
            break
        _, inv, cnt = np.unique(far // 32, axis=0, return_inverse=True, return_counts=True)
        if cnt.max() < 0.003 * len(s):
            break
        cols += [int(v) for v in np.median(far[inv.ravel() == cnt.argmax()], 0)]
    pal = Image.new("P", (1, 1)); pal.putpalette(cols + [0] * (768 - len(cols)))
    return pal
def fill_layer(rgb, pal, bg, up=2, ink_keep=None):
    L = rgb[..., :3] @ np.array([.299, .587, .114])
    if ink_keep:
        L = np.where(_near(rgb, ink_keep) <= 32, 255, L)            # kept dark fills are fills
    # ink = what ink_paths draws (L below the 45..95 midpoint); dark gray fills (shorts, L ~ 90) are NOT
    # ink, else they get refilled from the nearest light pixel and show a cream stripe inside the outline
    line = ndimage.binary_dilation(L < 72, iterations=2)          # include the anti-aliased rim (else a pale halo)
    idx = ndimage.distance_transform_edt(line, return_distances=False, return_indices=True)
    filled = rgb[idx[0], idx[1]].astype("uint8")                     # push fills under the ink
    im = Image.fromarray(filled).filter(ImageFilter.MedianFilter(5)).resize(
        (rgb.shape[1] * up, rgb.shape[0] * up), Image.BICUBIC).filter(ImageFilter.MedianFilter(5))
    q = im.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    with tempfile.TemporaryDirectory() as t:
        q.save(f"{t}/q.png")
        vtracer.convert_image_to_svg_py(f"{t}/q.png", f"{t}/q.svg", colormode="color", hierarchical="stacked",
            mode="spline", filter_speckle=16, color_precision=8, layer_difference=10, corner_threshold=60,
            length_threshold=4.0, splice_threshold=45, path_precision=3)
        svg = open(f"{t}/q.svg").read()
    inner = svg[svg.index(">", svg.index("<svg")) + 1:svg.rindex("</svg>")]
    bgx = "%02X%02X%02X" % tuple(bg)
    def nb(m):
        c = [int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)]
        return f'fill="#{bgx}"' if min(c) > 190 and sum(abs(c[i] - bg[i]) for i in range(3)) < 28 else m.group(0)
    return f'<g transform="scale({1 / up})">' + re.sub(r'fill="#([0-9A-Fa-f]{6})"', nb, inner) + "</g>"
def trace(rgb, pal, bg, out, clip=False, ink_keep=None):
    # clip=True: transparent outside the figure (for scenes whose background differs from the sheet's)
    # ink_keep=[(35,48,90)]: dark fill colours (navy shorts) stay fills; every other dark pixel is ink
    h, w = rgb.shape[:2]
    fills = fill_layer(rgb, pal, bg, ink_keep=ink_keep)
    if clip:
        # a background-coloured fill inside the clip is chroma trapped where the clip can't reach (between fingers):
        # drop it, the stacked layer under it shows through
        def chroma(m):
            c = [int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)]
            return "" if sum(abs(c[i] - bg[i]) for i in range(3)) < 30 else m.group(0)
        fills = re.sub(r'<path[^>]*fill="#([0-9A-Fa-f]{6})"[^>]*/>', chroma, fills)
        fills = f'<defs>{clip_def(rgb, bg)}</defs><g clip-path="url(#fig)">{fills}</g>'
    open(out, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                         + fills + ink_paths(rgb, ink_keep=ink_keep) + "</svg>")
