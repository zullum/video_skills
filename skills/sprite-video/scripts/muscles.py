# usage: python3 muscles.py SHEET.png FRAMESDIR MARKED.png [--color "#ff2020"] [--shift 14]
# Highlights the muscles a move works (chest in a fly, quads in a squat) as an overlay per frame that
# the player fades in and pulses (player.html hl=...). MARKED.png is ONE extra Nano Banana edit of the
# finished SHEET with the working muscles painted pure red in every cell (1K is enough; prompt in
# references/prompts.md "Muscle map"). Marking the sheet, not the base image, matters: the model redraws
# the torso a little in every cell, so a map made on the base slid off the chest by 10-20 px.
# Per frame: the marked cell is aligned to the sheet cell on the black ink (search +-SHIFT px), then
# overlay = painted red ∩ that frame's skin pixels, traced to FRAMESDIR/mNN.svg ("muscle" in frames.json).
import sys, os, json, argparse, numpy as np, potrace
from PIL import Image
from scipy import ndimage

ap = argparse.ArgumentParser(); ap.add_argument("sheet"); ap.add_argument("frames"); ap.add_argument("marked")
ap.add_argument("--color", default="#ff2020"); ap.add_argument("--shift", type=int, default=14)
A = ap.parse_args()
FR = json.load(open(f"{A.frames}/frames.json"))
sheet = np.array(Image.open(A.sheet).convert("RGB")).astype(int); H, W = sheet.shape[:2]
mk = np.array(Image.open(A.marked).convert("RGB").resize((W, H), Image.LANCZOS)).astype(int)
# painted = pure red AND changed from the sheet (a dark orange shadow is also "reddish" on its own)
red = (mk[..., 0] > 190) & (mk[..., 1] < 70) & (mk[..., 2] < 70) & (np.abs(mk - sheet).sum(2) > 60)
red = ndimage.binary_closing(ndimage.binary_opening(red, iterations=2), iterations=5)
cw, ch = FR["cell"]; C = round(W / cw)

def svg_path(m, up=4):
    big = np.array(Image.fromarray((m * 255).astype("uint8")).resize((m.shape[1] * up, m.shape[0] * up), Image.BICUBIC))
    big = ndimage.gaussian_filter(big.astype(float), up) > 127
    f = lambda p: f"{p.x / up:.2f},{p.y / up:.2f}"; d = []
    for c in potrace.Bitmap(~big).trace(turdsize=up * up * 20, alphamax=1.1, opticurve=True):
        d.append("M" + f(c.start_point))
        for s in c.segments:
            d.append(("L" + f(s.c) + "L" + f(s.end_point)) if s.is_corner else
                     ("C" + f(s.c1) + " " + f(s.c2) + " " + f(s.end_point)))
        d.append("Z")
    return "".join(d)

def best_shift(a, b, n):
    """(dy, dx) that moves ink map b onto ink map a best (small integer search)."""
    a = ndimage.binary_dilation(a, iterations=2); best = (-1, 0, 0)
    for dy in range(-n, n + 1, 2):
        for dx in range(-n, n + 1, 2):
            sc = (a & np.roll(b, (dy, dx), (0, 1))).sum()
            if sc > best[0]: best = (sc, dy, dx)
    return best[1:]

for fr in FR["frames"]:
    r, c = divmod(fr["src"], C); X0, Y0, X1, Y1 = int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch)
    cell, mcell, rcell = sheet[Y0:Y1, X0:X1], mk[Y0:Y1, X0:X1], red[Y0:Y1, X0:X1]
    dy, dx = best_shift(cell.sum(2) < 200, mcell.sum(2) < 200, A.shift)
    rcell = np.roll(rcell, (dy, dx), (0, 1))
    # skin = any saturated colour (lit or shaded); ink, gray metal, the bench and the background are not
    sat = ndimage.binary_closing((cell.max(2) - cell.min(2) > 60) & (cell.sum(2) < 690), iterations=4)
    m = ndimage.binary_opening(rcell & sat, iterations=2)
    x, y, w, h = int(fr["x"]), int(fr["y"]), fr["w"], fr["h"]
    sub = np.zeros((h, w), bool); part = m[y:y + h, x:x + w]; sub[:part.shape[0], :part.shape[1]] = part
    name = fr["file"].replace("f", "m", 1)
    open(f"{A.frames}/{name}", "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<path fill="{A.color}" fill-rule="evenodd" d="{svg_path(sub)}"/></svg>')
    fr["muscle"] = name; print(fr["src"], "shift", dy, dx, "px", int(m.sum()))
json.dump(FR, open(f"{A.frames}/frames.json", "w"), indent=1)
open(f"{A.frames}/frames.js", "w").write("window.FR=" + json.dumps(FR) + ";")
print("muscle overlays ->", A.frames)
