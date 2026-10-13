# usage: python3 squat_spec.py base.png SPEC.json [--frames 8 --cols 4 --rows 2]
# Example multi-joint rig: writes a template.py SPEC for a squat seen from the side, facing right
# (frame 1 = standing, last frame = bottom). The foot stays planted; the shin leans forward about the
# ankle, the thigh folds back about the knee, the torso leans forward about the hip, and the straight
# arms stay level (they point at the same spot in every frame, like a real bodyweight squat).
# Each body part is a "piece" (template.py), placed by forward kinematics, so the model only has to
# repair the joints instead of inventing the pose. Also writes base_clean.png: the base without the
# floor line the model drew through or behind the legs (the template draws its own).
# Measure the points below on YOUR base image (BASE pixels; use a coordinate overlay).
import sys, json, math, argparse, numpy as np
from PIL import Image

ANKLE, KNEE, HIP, SHOULDER = (1310, 1340), (1320, 1130), (1320, 850), (1330, 430)
SOLE_Y = 1430                     # lowest ink of the foot
CROP = [980, 120, 2020, 1450]     # box around the figure with room for the hips going back
CELL = [640, 818]                 # CROP scaled to the cell (keep the aspect ratio)
# pose at the bottom (degrees; 0 = standing): shin forward, thigh back, torso forward
SHIN, THIGH, TORSO = 32.0, 92.0, 38.0
# piece polygons around each part (loose boxes are fine: only figure pixels are cut)
FOOT = [(1200, 1335), (1520, 1335), (1520, 1445), (1200, 1445)]
SHIN_P = [(1200, 1080), (1440, 1080), (1440, 1350), (1200, 1350)]
THIGH_P = [(1080, 820), (1440, 820), (1440, 1150), (1080, 1150)]
TORSO_P = [(1040, 100), (1440, 100), (1440, 350), (1395, 372), (1395, 700), (1475, 700), (1475, 845),
           (1040, 870)]                       # head + chest + shorts waist with the drawstring
ARM_P = [(1395, 368), (1960, 340), (1960, 540), (1395, 540)]

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
