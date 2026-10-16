"""Add a hand-written SVG to a project as an asset.   scripts/py scripts/svg_asset.py PROJECT NAME FILE.svg [--anchor center|feet]
For small things simple enough to draw in code (a clock, a stopwatch, a tick, a coin, a calendar): the SVG is copied
to assets/svg/NAME.svg and gets a manifest entry like a traced asset, sized from its viewBox (or width/height).
Use the palette's hex colours and #141418 outlines so it matches the traced art."""
import argparse
import os
import re
import shutil

from mx import manifest

ANCHORS = {"center": [0.5, 0.5], "feet": [0.5, 1.0]}


def size(svg_text):
    """(w, h) from the viewBox, else from the width/height attributes."""
    vb = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"', svg_text)
    if vb:
        return round(float(vb.group(1))), round(float(vb.group(2)))
    w, h = (re.search(rf'{k}="([\d.]+)', svg_text) for k in ("width", "height"))
    if not (w and h):
        raise SystemExit("the SVG needs a viewBox or width and height")
    return round(float(w.group(1))), round(float(h.group(1)))


def add(project, name, src, anchor="center"):
    text = open(src).read()
    w, h = size(text)
    os.makedirs(os.path.join(project, "assets", "svg"), exist_ok=True)
    rel = f"assets/svg/{name}.svg"
    if os.path.abspath(src) != os.path.abspath(os.path.join(project, rel)):
        shutil.copy(src, os.path.join(project, rel))
    man = manifest.load(project)
    man["assets"][name] = {"file": rel, "w": w, "h": h, "anchor": ANCHORS[anchor], "holes": []}
    manifest.save(project, man)
    return man["assets"][name]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("name"); ap.add_argument("svg")
    ap.add_argument("--anchor", choices=sorted(ANCHORS), default="center")
    a = ap.parse_args(argv)
    e = add(a.project, a.name, a.svg, a.anchor)
    print(f"{a.name}: {e['w']}x{e['h']}, anchor {a.anchor}")


if __name__ == "__main__":
    main()
