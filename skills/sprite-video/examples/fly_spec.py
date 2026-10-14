# usage: python3 fly_spec.py base.png SPEC.json [--frames 6 --cols 3 --rows 2]
# Example two-arm guide: writes a template.py SPEC for incline dumbbell flyes seen from the FRONT
# (frame 1 = top, arms up with the dumbbells together; last frame = bottom, arms wide). The body stays
# still, so frame 1 is the base as is and in every other cell both arms (and the dumbbells) are erased
# and shown as red shoulder-elbow-wrist guides with a red circle for the dumbbell. The right arm is the
# left one mirrored about MID_X. A fly keeps the elbows only slightly bent through the whole arc
# (BEND), so the guides rotate a nearly straight arm about the shoulder; free per-joint angles made the
# middle frames read as a shoulder press. A short red line through each circle sets the dumbbell bar
# angle, turning evenly from horizontal (top) to vertical (bottom), so it never flips in one frame.
# Measure the points on YOUR base image (BASE pixels, coordinate overlay).
import json, math, argparse

MID_X = 1400                                    # body centre line
SHOULDER = (1100, 620)                          # viewer's left shoulder joint
TOP = {"elbow": (1010, 440), "wrist": (1140, 235)}    # as drawn in the base
BOTTOM_UPPER = 162.0                            # upper-arm angle at the bottom (deg, 180 = straight left)
BEND = (59.0, 22.0)                             # elbow bend at the top (as drawn) and through the arc
BAR = 230                                       # length of the bar guide (BASE px)
CROP = [490, 20, 2310, 1536]                    # box around the widest pose
CELL = [917, 764]                               # CROP scaled to a 3x2 cell of a 16:9 sheet
ERASE = [[(860, 40), (1940, 40), (1940, 370), (860, 370)],                   # dumbbells + forearms
         [(880, 370), (1200, 370), (1200, 520), (1110, 600), (960, 640), (880, 600)]]   # left upper arm

ap = argparse.ArgumentParser(); ap.add_argument("base"); ap.add_argument("spec")
ap.add_argument("--frames", type=int, default=6); ap.add_argument("--cols", type=int, default=3)
ap.add_argument("--rows", type=int, default=2); A = ap.parse_args()

s = CELL[0] / (CROP[2] - CROP[0])
C = lambda p: [round((p[0] - CROP[0]) * s, 1), round((p[1] - CROP[1]) * s, 1)]
M = lambda p: (2 * MID_X - p[0], p[1])                                   # mirror to the right arm
ang = lambda a, b: math.atan2(b[1] - a[1], b[0] - a[0])
lerp_ang = lambda a0, a1, t: a0 + (math.atan2(math.sin(a1 - a0), math.cos(a1 - a0))) * t
U = math.dist(SHOULDER, TOP["elbow"]); F = math.dist(TOP["elbow"], TOP["wrist"])
erase = [[C(p) for p in poly] for poly in ERASE] + [[C(M(p)) for p in ERASE[1]]]
cells = [{}]
for k in range(1, A.frames):
    t = k / (A.frames - 1)
    au = lerp_ang(ang(SHOULDER, TOP["elbow"]), math.radians(BOTTOM_UPPER), t)
    bend = BEND[1] + (BEND[0] - BEND[1]) * (1 - min(t * 2.5, 1))      # straightens early, then holds
    af = au + math.radians(bend)
    E = (SHOULDER[0] + U * math.cos(au), SHOULDER[1] + U * math.sin(au))
    W = (E[0] + F * math.cos(af), E[1] + F * math.sin(af))
    b = math.radians(90 * t); h = (BAR / 2 * math.cos(b), BAR / 2 * math.sin(b))
    bar = [(W[0] - h[0], W[1] + h[1]), (W[0] + h[0], W[1] - h[1])]     # tilts outward-down as it turns
    cells.append({"erase": erase,
                  "guide": [[C(SHOULDER), C(E), C(W)], [C(M(SHOULDER)), C(M(E)), C(M(W))],
                            [C(p) for p in bar], [C(M(p)) for p in bar]],
                  "circle": [C(W), C(M(W))]})
json.dump({"base": A.base, "crop": CROP, "cols": A.cols, "rows": A.rows, "cell": CELL,
           "fit": "stretch", "cells": cells}, open(A.spec, "w"), indent=1)
print("wrote", A.spec)
