"""Cut a sheet of several assets on a flat (chroma) background into one clipped SVG per asset.
  scripts/py scripts/asset_sheet.py SHEET PROJECT --names a,b,c [--grid 3x3] [--anchor feet|center|a=center,...]
Writes PROJECT/assets/svg/<name>.svg and assets/manifest.json entries {file, w, h, anchor, holes}.
Without --grid every large connected shape is one asset (reading order); with it, every non-empty cell."""
import argparse
import importlib
import os
import sys

import numpy as np
from PIL import Image

import deps
from mx import manifest, sheet

PAD = 8


def anchor_kinds(spec, names):
    if spec and "=" not in spec:
        return {n: spec for n in names}
    kinds = {n: "feet" for n in names}
    for pair in [p for p in (spec or "").split(",") if p]:
        n, k = pair.split("=")
        kinds[n] = k
    return kinds


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("project")
    ap.add_argument("--names", required=True); ap.add_argument("--grid"); ap.add_argument("--anchor")
    A = ap.parse_args(argv)
    a = np.array(Image.open(A.sheet).convert("RGB")).astype(int)
    H, W = a.shape[:2]
    bg = sheet.background(a)
    m = sheet.mask(a, bg)
    grid = tuple(int(v) for v in A.grid.lower().split("x")) if A.grid else None
    boxes = sheet.find_assets(m, grid)
    names = [n for n in A.names.split(",") if n]
    if len(boxes) != len(names):
        sys.exit(f"found {len(boxes)} assets, --names has {len(names)} (boxes: {boxes}); use --grid or fix the sheet")
    kinds = anchor_kinds(A.anchor, names)
    sys.path.insert(0, os.path.join(deps.locate("sv"), "scripts"))
    trace2 = importlib.import_module("trace2")
    pal = sheet.palette(a, bg)
    man = manifest.load(A.project)
    out_dir = os.path.join(A.project, "assets", "svg")
    os.makedirs(out_dir, exist_ok=True)
    for name, (x0, y0, x1, y1) in zip(names, boxes):
        X0, Y0, X1, Y1 = max(x0 - PAD, 0), max(y0 - PAD, 0), min(x1 + PAD, W), min(y1 + PAD, H)
        crop, mc = a[Y0:Y1, X0:X1].copy(), m[Y0:Y1, X0:X1].copy()
        inside = np.zeros_like(mc)
        inside[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
        crop[mc & ~inside] = bg                                  # a neighbour reaching into the padding
        mc &= inside
        trace2.trace(crop.astype("uint8"), pal, bg, os.path.join(out_dir, f"{name}.svg"), clip=True)
        man["assets"][name] = {"file": f"assets/svg/{name}.svg", "w": int(X1 - X0), "h": int(Y1 - Y0),
                               "anchor": sheet.anchor(mc, kinds[name]), "holes": sheet.holes(mc)}
        print(f"{name}: {X1 - X0}x{Y1 - Y0}, anchor {man['assets'][name]['anchor']}, holes {len(man['assets'][name]['holes'])}")
    manifest.save(A.project, man)


if __name__ == "__main__":
    main()
