# usage: python3 template.py SPEC.json OUT.png
# Builds the sprite-sheet TEMPLATE that goes to Nano Banana together with the prompt.
# The key trick: the base character is pre-drawn in EVERY cell, so the model keeps one size and one
# position in all cells and only repaints what moves. Per cell you can also
#   rotate  the figure about a pivot (rough rig, e.g. a push-up body pivoting on the toes),
#   erase   polygons (the limb that will be redrawn),
#   keep    rectangles of the unrotated base (a hand that stays planted on the floor),
#   guide   red polylines with dots / circles showing where the limb must go (the model follows them,
#           it cannot invent in-between angles on its own).
#
# SPEC (all coordinates in CELL pixels, i.e. after the base is fitted into a cell):
# {
#   "base": "base.png",               # neutral pose, plain background
#   "cols": 6, "rows": 4, "cell": [640, 540],
#   "fit": "stretch" | {"height": 0.9, "x": 0, "anchor": "bottom"},   # how the base sits in a cell
#   "trim": 10,                       # px cut from left/top/right of the base (generated images often have a frame line)
#   "floor": {"y": 434, "x": [80, 835], "width": 4},    # optional: floor line kept out of the rotating figure
#   "cells": [ {}, {"rotate": {"pivot": [190, 430], "deg": -2.5},
#                   "erase": [[[578,228],[660,222],[712,436],[590,436]]],
#                   "keep": [[595,383,705,431]],
#                   "guide": [[[615,203],[578,301],[620,400]]],
#                   "circle": [[620,400]]}, ... ]       # missing cells = plain copy of the base
# }
import sys, json, math, numpy as np
from PIL import Image, ImageDraw

RED, GRID = (230, 40, 40), (170, 170, 170)

def rot(p, piv, deg):
    r = math.radians(deg); x, y = p[0] - piv[0], p[1] - piv[1]
    return (piv[0] + x * math.cos(r) - y * math.sin(r), piv[1] + x * math.sin(r) + y * math.cos(r))

def fitted_base(spec):
    b = Image.open(spec["base"]).convert("RGB"); t = spec.get("trim", 0)
    if t: b = b.crop((t, t, b.width - t, b.height))
    cw, ch = spec["cell"]; a = np.array(b)
    bg = tuple(int(v) for v in np.median(a[5:60, 5:min(200, a.shape[1])].reshape(-1, 3), 0))
    cell = Image.new("RGB", (cw, ch), bg); fit = spec.get("fit", "stretch")
    if fit == "stretch":
        cell = b.resize((cw, ch), Image.LANCZOS)
    else:
        s = fit.get("height", 1.0) * ch / b.height
        bb = b.resize((round(b.width * s), round(b.height * s)), Image.LANCZOS)
        y = ch - bb.height if fit.get("anchor", "bottom") == "bottom" else 0
        cell.paste(bb, (int(fit.get("x", 0)), y))
    return cell, bg

def build(spec):
    cell0, bg = fitted_base(spec); cw, ch = spec["cell"]; C, R = spec["cols"], spec["rows"]
    a = np.array(cell0).astype(int)
    fig = np.abs(a - bg).sum(2) > 60                                   # figure mask
    fl = spec.get("floor")
    if fl:                                                             # the floor never rotates with the body
        y0 = fl["y"] - fl.get("width", 4) // 2 - 2
        dark = a.sum(2) < 200
        fig[y0:, :] &= ~dark[y0:, :] | (np.arange(y0, ch)[:, None] < y0)
        fig[fl["y"] - 3:fl["y"] + 4, :] = False
    sheet = Image.new("RGB", (cw * C, ch * R), bg)
    cells = spec.get("cells", [])
    for k in range(C * R):
        c = cells[k] if k < len(cells) else {}
        out = Image.new("RGB", (cw, ch), bg); d = ImageDraw.Draw(out)
        if fl: d.line([(fl["x"][0], fl["y"]), (fl["x"][1], fl["y"])], fill=(20, 20, 24), width=fl.get("width", 4))
        m = Image.fromarray((fig * 255).astype("uint8")); figim = cell0
        rt = c.get("rotate")
        if rt:
            piv, deg = rt["pivot"], rt["deg"]
            figim = cell0.rotate(-deg, center=tuple(piv), resample=Image.BICUBIC)
            m = m.rotate(-deg, center=tuple(piv), resample=Image.BILINEAR)
        er = Image.new("L", (cw, ch), 0); ed = ImageDraw.Draw(er)
        for poly in c.get("erase", []):
            ed.polygon([rot(p, rt["pivot"], rt["deg"]) if rt else tuple(p) for p in poly], fill=255)
        m = Image.fromarray(np.minimum(np.array(m), 255 - np.array(er)))
        out.paste(figim, (0, 0), m)
        for x0, y0, x1, y1 in c.get("keep", []):                      # e.g. the planted hand, unrotated
            km = np.zeros((ch, cw), bool); km[y0:y1, x0:x1] = fig[y0:y1, x0:x1]
            out.paste(cell0, (0, 0), Image.fromarray((km * 255).astype("uint8")))
        for line in c.get("guide", []):
            pts = [tuple(p) for p in line]
            d.line(pts, fill=RED, width=9)
            for p in pts: d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=RED)
        for p in c.get("circle", []):
            d.ellipse([p[0] - 20, p[1] - 20, p[0] + 20, p[1] + 20], outline=RED, width=6)
        sheet.paste(out, ((k % C) * cw, (k // C) * ch))
    d = ImageDraw.Draw(sheet)
    for i in range(1, C): d.line([(i * cw, 0), (i * cw, ch * R)], fill=GRID, width=4)
    for j in range(1, R): d.line([(0, j * ch), (cw * C, j * ch)], fill=GRID, width=4)
    return sheet

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: template.py SPEC.json OUT.png")
    build(json.load(open(sys.argv[1]))).save(sys.argv[2]); print("wrote", sys.argv[2])
