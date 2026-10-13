# usage: python3 colorfix.py SHEET.png REF.png OUT.png COLS ROWS REFCOLS REFROWS
# Each Nano Banana edit drifts the colours a little (bluer skin, pinker background). Before slicing,
# map a sheet's colours onto the reference sheet's with one affine colour transform, fitted on
# matching patches of cell 1 (background, skin, shorts, outline), so frames from several sheets
# can be cut together without colour jumps.
import sys, numpy as np
from PIL import Image
src, ref, out = sys.argv[1:4]; c, r, rc, rr = map(int, sys.argv[4:8])
# patch centres in the 630x540 cell space of the templates (character on the left, head top ~95)
P = {"bg": (560, 60), "chest": (175, 285), "abs": (215, 340), "shorts": (175, 450), "head": (210, 120)}
def samples(path, cols, rows):
    a = np.array(Image.open(path).convert("RGB")).astype(float); cw, ch = a.shape[1] / cols, a.shape[0] / rows
    sx, sy = cw / 630, ch / 540; out = []
    for x, y in P.values():
        X, Y = int(x * sx), int(y * sy); out.append(np.median(a[Y - 6:Y + 6, X - 6:X + 6].reshape(-1, 3), 0))
    a2 = a.reshape(-1, 3); dark = a2[a2.sum(1) < np.percentile(a2.sum(1), 1)]
    out.append(np.median(dark, 0)); return np.array(out), a
S, a = samples(src, c, r); R, _ = samples(ref, rc, rr)
for k, s_, r_ in zip(list(P) + ["outline"], S, R): print(k, s_.astype(int), "->", r_.astype(int))
M, *_ = np.linalg.lstsq(np.c_[S, np.ones(len(S))], R, rcond=None)
o = np.clip(np.c_[a.reshape(-1, 3), np.ones(a.shape[0] * a.shape[1])] @ M, 0, 255).reshape(a.shape)
Image.fromarray(o.astype("uint8")).save(out)
