# usage: python3 pushup_side_spec.py pushup_base.png SPEC.json
# The demo's 24-frame push-up (6x4 cells of 917x768 on a 4K 16:9 sheet; frame 1 = top, frame 24 = bottom),
# adapted from sprite-video's examples/pushup_spec.py: the body rotates about the toes, both arms are erased
# (in profile the far arm sits right behind the near one), the hands stay planted, and the near arm is a red
# shoulder-elbow-wrist guide from 2-link IK with the upper arm foreshortened up to 25 % at the bottom.
# Points measured on the demo's base fitted to 917x768.
import json, math, sys

PIVOT = (140, 585)
SHOULDER = (665, 300)
WRIST = (685, 545)
ARM_ERASE = [(615, 290), (705, 285), (720, 340), (722, 528), (790, 540), (790, 596), (600, 596), (600, 400)]
HAND_BOX = [630, 528, 780, 592]
FLOOR = {"y": 590, "x": [60, 855], "width": 4}
BOTTOM_DEG = 12.0
N = 24
L = math.dist(SHOULDER, WRIST) / 2


def rot(p, deg):
    r = math.radians(deg); x, y = p[0] - PIVOT[0], p[1] - PIVOT[1]
    return (PIVOT[0] + x * math.cos(r) - y * math.sin(r), PIVOT[1] + x * math.sin(r) + y * math.cos(r))


def elbow(S, prog):
    lu, lf = L * (1 - .25 * prog), L
    dx, dy = WRIST[0] - S[0], WRIST[1] - S[1]; dist = math.hypot(dx, dy)
    if dist >= lu + lf: return (S[0] + dx * lu / dist, S[1] + dy * lu / dist)
    a = (lu ** 2 - lf ** 2 + dist ** 2) / (2 * dist); h = math.sqrt(max(lu ** 2 - a ** 2, 0))
    ux, uy = dx / dist, dy / dist; px, py = uy, -ux
    if px > 0: px, py = -px, -py                                      # elbow points back to the feet
    return (S[0] + ux * a + px * h, S[1] + uy * a + py * h)


top = math.degrees(math.atan2(PIVOT[1] - SHOULDER[1], SHOULDER[0] - PIVOT[0]))
cells = []
for k in range(N):
    p = 0.5 - 0.5 * math.cos(math.pi * k / (N - 1))                 # eased: small steps near the top and bottom
    d = p * (top - BOTTOM_DEG); S = rot(SHOULDER, d); E = elbow(S, p)
    cells.append({"rotate": {"pivot": PIVOT, "deg": d}, "erase": [ARM_ERASE], "keep": [HAND_BOX],
                  "guide": [[[round(v, 1) for v in q] for q in (S, E, WRIST)]]})
json.dump({"base": sys.argv[1], "cols": 6, "rows": 4, "cell": [917, 768], "fit": "stretch",
           "floor": FLOOR, "cells": cells}, open(sys.argv[2], "w"), indent=1)
print("wrote", sys.argv[2])
