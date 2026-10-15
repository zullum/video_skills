# usage: python3 slice.py SHEET.png OUTDIR --cols 3 --rows 3 [--floor] [--drop 4,7] [--keep-small] [--clip]
# Cuts a generated sprite sheet into frames and traces each one to SVG (trace2: potrace ink + vtracer fills).
# Frames keep their CELL coordinates: the template pre-drew the character in every cell, so no
# alignment is needed and nothing shakes. Writes OUTDIR/frames.json and OUTDIR/frames.js:
#   {cell:[w,h], bg:[r,g,b], floor:[y0,y1]|null, frames:[{file,x,y,w,h}]}
#   --floor       detect the floor line, erase it from every frame (the player draws one steady line)
#   --drop        frame indexes to skip (bad cells)
#   --keep-small  keep separate small marks (motion lines, sweat drops) instead of only the main figure
#   --anchor 0.25,0.45  align every frame on the head: the topmost ink inside this column band (fractions
#                 of the cell width) must not move. Use it when the head stays still (flex, curls); the
#                 model drifts a few px from row to row, which shows as a jump. Skip it when the whole
#                 body moves (push-up) and the cells are already locked by the template.
#   --clip        transparent outside the figure (for scenes on another background)
#   --ink-keep "#23305A"  dark fill colours (navy shorts) stay fills instead of turning into black ink
#   --ground      align every frame on its planted foot: the heel (left end of the lowest ink) and
#                 the sole stay where they are in frame 0. Use it for standing moves (squat, lunge,
#                 jumps land) where the model slides the feet a few % per cell. Adds a floor line
#                 under the sole when --floor found none.
import sys, os, json, argparse, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trace2

ap = argparse.ArgumentParser()
ap.add_argument("sheet"); ap.add_argument("out")
ap.add_argument("--cols", type=int, required=True); ap.add_argument("--rows", type=int, required=True)
ap.add_argument("--floor", action="store_true"); ap.add_argument("--drop", default="")
ap.add_argument("--keep-small", action="store_true"); ap.add_argument("--anchor", default="")
ap.add_argument("--ground", action="store_true"); ap.add_argument("--clip", action="store_true")
ap.add_argument("--ink-keep", default="")
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
drop = {int(x) for x in A.drop.split(",") if x}
a = np.array(Image.open(A.sheet).convert("RGB")).astype(int); H, W = a.shape[:2]
cw, ch = W / A.cols, H / A.rows
bg = np.median(a[20:60, 20:200].reshape(-1, 3), 0); BGQ = tuple(int(c) for c in bg)
# one palette for the whole sheet: background + white (eye glow, shine) + 14 colours of the art
m_all = np.abs(a - bg).sum(2) > 70
ink = a[::4, ::4][m_all[::4, ::4]].astype("uint8")
auto = Image.fromarray(ink.reshape(1, -1, 3)).quantize(colors=14, method=Image.Quantize.MEDIANCUT).getpalette()[:42]
fixed = [18, 18, 22, 255, 255, 255] + list(BGQ)
pal = Image.new("P", (1, 1)); pal.putpalette(fixed + auto + [0] * (768 - len(fixed) - len(auto)))
frames, floors = [], []
for k in range(A.cols * A.rows):
    if k in drop: continue
    r, c = divmod(k, A.cols); m_ = 10                                   # stay off the grid lines
    X0, Y0 = int(c * cw) + m_, int(r * ch) + m_; X1, Y1 = int((c + 1) * cw) - m_, int((r + 1) * ch) - m_
    cell = a[Y0:Y1, X0:X1].copy(); dark = (cell.sum(2) < 260) & (np.abs(cell - bg).sum(2) > 70)   # a dark chroma bg is not ink
    if A.floor:
        band = np.where(dark.mean(1) > .55)[0]
        if len(band):
            b0, b1 = band.min() - 2, band.max() + 3; floors.append((b0 + m_, b1 + m_))
            sl = cell[b0:b1]; sl[dark[b0:b1]] = bg
    m = ndimage.binary_opening(np.abs(cell - bg).sum(2) > 70, iterations=1)
    lab, n = ndimage.label(ndimage.binary_closing(m, iterations=3))
    if n == 0: continue
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = lab == (np.argmax(sizes) + 1)
    if A.keep_small:                                                   # marks near the figure stay
        near = ndimage.binary_dilation(keep, iterations=int(.05 * max(cw, ch)))
        for i in range(1, n + 1):
            if sizes[i - 1] > 30 and (near & (lab == i)).any(): keep |= lab == i
    ys, xs = np.where(keep)
    bx0, by0 = max(xs.min() - 8, 0), max(ys.min() - 8, 0)
    bx1, by1 = min(xs.max() + 9, cell.shape[1]), min(ys.max() + 9, cell.shape[0])
    msk = ndimage.binary_dilation(keep, iterations=4)[by0:by1, bx0:bx1]
    cc = np.where(msk[..., None], cell[by0:by1, bx0:bx1], bg)
    if A.floor:                                                       # pale floor smudges left of the feet
        for yy in range(max(cc.shape[0] - 60, 0), cc.shape[0]):
            d = np.where(cc[yy].sum(1) < 200)[0]
            if len(d) and d[0] < cc.shape[1] * .25: cc[yy, :d[0]] = bg
    anc = None
    if A.anchor:
        f0, f1 = (float(v) for v in A.anchor.split(",")); c0, c1 = int(f0 * cell.shape[1]), int(f1 * cell.shape[1])
        rows = np.where(keep[:, c0:c1].any(1))[0]
        if len(rows):
            top = rows[0]; band = keep[top:top + int(.08 * ch), c0:c1]
            anc = [float(m_ + c0 + np.where(band)[1].mean()), float(m_ + top)]
    gnd = None
    if A.ground:                                                       # heel x, sole y of the planted foot
        yb = np.where(keep.any(1))[0].max(); band = keep[max(yb - int(.07 * ch), 0):yb + 1]
        gnd = [float(m_ + np.where(band.any(0))[0].min()), float(m_ + yb)]
    name = f"f{len(frames):02d}.svg"
    trace2.trace(cc.astype("uint8"), pal, BGQ, f"{A.out}/{name}", clip=A.clip,
                 ink_keep=[tuple(int(h.strip("#")[i:i + 2], 16) for i in (0, 2, 4)) for h in A.ink_keep.split(",") if h] or None)
    frames.append(dict(file=name, src=k, x=float(m_ + bx0), y=float(m_ + by0), w=int(bx1 - bx0), h=int(by1 - by0), anc=anc, gnd=gnd))
    print(k, "->", name)
fl = None
if floors:
    fl = [float(np.median([f[0] for f in floors])) + 2, float(np.median([f[1] for f in floors])) - 3]
anchor = None
if A.anchor and frames and frames[0]["anc"]:
    anchor = frames[0]["anc"]                                        # shift every frame onto frame 0's head
    for f in frames:
        if f["anc"]: f["x"] += anchor[0] - f["anc"][0]; f["y"] += anchor[1] - f["anc"][1]
if A.ground and frames and frames[0]["gnd"]:
    g0 = frames[0]["gnd"]                                            # shift every frame onto frame 0's foot
    for f in frames:
        if f["gnd"]: f["x"] += g0[0] - f["gnd"][0]; f["y"] += g0[1] - f["gnd"][1]
    if fl is None: fl = [g0[1] - 1, g0[1] + 4]
d = dict(cell=[cw, ch], bg=list(BGQ), floor=fl, anchor=anchor, frames=frames)
json.dump(d, open(f"{A.out}/frames.json", "w"), indent=1)
open(f"{A.out}/frames.js", "w").write("window.FR=" + json.dumps(d) + ";")
print(len(frames), "frames ->", A.out)
