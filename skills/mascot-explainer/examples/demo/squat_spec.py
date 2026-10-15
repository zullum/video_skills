# usage: python3 squat_spec.py squat_base.png SPEC.json   (run it in the folder that should get base_clean.png)
# The demo's 8-frame squat, sprite-video's examples/squat_spec.py with the points measured on the demo's base
# (1696x2528, facing right, arms forward). Foot planted, shin about the ankle, thigh about the knee, torso about
# the hip, arms level; the model repairs the joints.
import sys, json, math, argparse, numpy as np
from PIL import Image

ANKLE, KNEE, HIP, SHOULDER = (760, 2090), (760, 1830), (790, 1330), (790, 690)
SOLE_Y = 2250                     # lowest ink of the foot
CROP = [80, 100, 1696, 2290]      # box around the figure with room for the hips going back
CELL = [632, 848]                 # one cell of a 4x2 grid on a 2K 3:2 sheet (CROP has the same aspect)
# pose at the bottom (degrees; 0 = standing): shin forward, thigh back, torso forward
SHIN, THIGH, TORSO = 32.0, 92.0, 38.0
# piece polygons around each part (loose boxes are fine: only figure pixels are cut)
FOOT = [(640, 2090), (1040, 2090), (1040, 2275), (640, 2275)]
SHIN_P = [(600, 1820), (900, 1820), (900, 2100), (600, 2100)]
THIGH_P = [(560, 1260), (1000, 1260), (1000, 1840), (560, 1840)]
TORSO_P = [(520, 120), (1000, 120), (1000, 600), (880, 610), (880, 840), (1000, 840), (1000, 1300), (520, 1320)]
ARM_P = [(870, 600), (1700, 600), (1700, 840), (870, 840)]

ap = argparse.ArgumentParser(); ap.add_argument("base"); ap.add_argument("spec")
ap.add_argument("--frames", type=int, default=8); ap.add_argument("--cols", type=int, default=4)
ap.add_argument("--rows", type=int, default=2); A = ap.parse_args()

# remove the floor line drawn behind the legs (rows that are dark across most of the image)
a = np.array(Image.open(A.base).convert("RGB")).astype(int); bg = np.median(a[5:60, 5:200].reshape(-1, 3), 0)
rows = np.where((a.sum(2) < 200).mean(1) > .5)[0]
if len(rows):
    y0, y1 = rows.min() - 2, rows.max() + 3; above = a[y0 - 4]
    clear = np.abs(above - bg).sum(1) < 60                     # columns that are background just above
    a[y0:y1, clear] = bg
Image.fromarray(a.astype("uint8")).save("base_clean.png")

s = CELL[0] / (CROP[2] - CROP[0])
C = lambda p: (round((p[0] - CROP[0]) * s, 1), round((p[1] - CROP[1]) * s, 1))   # base -> cell px
L1, L2, L3 = math.dist(ANKLE, KNEE), math.dist(KNEE, HIP), math.dist(HIP, SHOULDER)
up = lambda base, length, deg: (base[0] + length * math.sin(math.radians(deg)),
                                base[1] - length * math.cos(math.radians(deg)))
cells = []
for k in range(A.frames):
    t = k / (A.frames - 1); t = t * t * (3 - 2 * t) * .35 + t * .65         # a touch of ease
    a1, a2, a3 = SHIN * t, -THIGH * t, TORSO * t
    knee = up(ANKLE, L1, a1); hip = up(knee, L2, a2); sh = up(hip, L3, a3)
    P = lambda poly: [C(p) for p in poly]
    cells.append({"pieces": [
        {"poly": P(SHIN_P), "pivot": C(ANKLE), "to": C(ANKLE), "deg": a1},
        {"poly": P(THIGH_P), "pivot": C(KNEE), "to": C(knee), "deg": a2},
        {"poly": P(TORSO_P), "pivot": C(HIP), "to": C(hip), "deg": a3},
        {"poly": P(ARM_P), "pivot": C(SHOULDER), "to": C(sh), "deg": 0},
        {"poly": P(FOOT), "pivot": C(ANKLE), "to": C(ANKLE), "deg": 0}]})
cells[0] = {}                                                               # frame 1 = the base as is
json.dump({"base": "base_clean.png", "crop": CROP, "cols": A.cols, "rows": A.rows, "cell": CELL,
           "fit": "stretch", "floor": {"y": round(C((0, SOLE_Y))[1] + 3), "x": [20, CELL[0] - 20], "width": 4},
           "cells": cells}, open(A.spec, "w"), indent=1)
print("wrote", A.spec, "and base_clean.png")
