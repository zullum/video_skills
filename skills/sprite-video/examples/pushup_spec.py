# usage: python3 pushup_spec.py top.png SPEC.json
# Example rig: writes a template.py SPEC for a 3x3 push-up sheet (frame 1 = top, frame 9 = bottom).
# The body is rotated about the toes, the near arm is erased, the hand stays planted, and the arm is
# shown as a red shoulder-elbow-wrist guide from 2-link IK. The upper arm is foreshortened up to 25%
# at the bottom (elbow flares toward the camera), which looks more natural than a pure backward bend.
# Measure the four points below on YOUR base image (cell pixels after it is fitted to 917x512).
import sys, json, math

PIVOT = (190, 430)      # toes on the floor
SHOULDER = (605, 185)   # shoulder joint in the top pose
WRIST = (620, 400)      # wrist, fixed on the floor
ARM_ERASE = [(578, 228), (660, 222), (712, 400), (712, 436), (590, 436), (575, 300)]
HAND_BOX = [595, 383, 705, 431]
FLOOR = {"y": 434, "x": [80, 835], "width": 4}
BOTTOM_DEG = 11.0       # body angle at the bottom (top angle is measured from PIVOT -> SHOULDER)
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
for k in range(9):
    d = k * (top - BOTTOM_DEG) / 8; S = rot(SHOULDER, d); E = elbow(S, d / (top - BOTTOM_DEG))
    cells.append({"rotate": {"pivot": PIVOT, "deg": d}, "erase": [ARM_ERASE], "keep": [HAND_BOX],
                  "guide": [[[round(v, 1) for v in p] for p in (S, E, WRIST)]]})
json.dump({"base": sys.argv[1], "cols": 3, "rows": 3, "cell": [917, 512], "fit": "stretch",
           "floor": FLOOR, "cells": cells}, open(sys.argv[2], "w"), indent=1)
print("wrote", sys.argv[2])
