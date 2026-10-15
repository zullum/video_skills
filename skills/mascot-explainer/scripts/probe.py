"""Pixel probes on HyperFrames snapshots: the selftest's assertions.
  probe.py times PROJECT PROBES [--only ids]            the global times to snapshot, comma separated
  probe.py check PROJECT PROBES SNAPDIR [--only ids]    PASS/FAIL per probe, exit 1 on any FAIL
A probe: {"shot", "t" (local seconds), "kind": px|notpx|area|noarea, "x","y" or "rect": [x,y,w,h], "color" (hex
or a palette role), "tol" (40, max channel difference), "min" (.05, area), "max" (.002, noarea), "note"}.
Shot starts come from audio/sfx_cues.json "slots" (written by build.py); probes of shots not built are skipped."""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image


def load(project, probes_path, only=None):
    slots = json.load(open(os.path.join(project, "audio", "sfx_cues.json")))["slots"]
    pal = json.load(open(os.path.join(project, "style.json"))).get("palette", {})
    probes = [p for p in json.load(open(probes_path)) if p["shot"] in slots and (not only or p["shot"] in only)]
    for p in probes:
        p["g"] = round(slots[p["shot"]] + p["t"], 3)
    return probes, pal


def times(probes):
    return sorted({p["g"] for p in probes})


def rgb(color, pal):
    c = pal.get(color, color)
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)])


def judge(img, p, pal):
    col, tol = rgb(p["color"], pal), p.get("tol", 40)
    if p["kind"] in ("px", "notpx"):
        px = img[p["y"], p["x"], :3].astype(int)
        hit = int(np.abs(px - col).max()) <= tol
        return (hit if p["kind"] == "px" else not hit), f"pixel {px.tolist()}"
    x, y, w, h = p["rect"]
    frac = float((np.abs(img[y:y + h, x:x + w, :3].astype(int) - col).max(2) <= tol).mean())
    ok = frac >= p.get("min", 0.05) if p["kind"] == "area" else frac <= p.get("max", 0.002)
    return ok, f"{frac:.4f} of the area"


def check(probes, pal, snapdir):
    ts = times(probes)
    files = sorted(glob.glob(os.path.join(snapdir, "frame-*-at-*.png")),
                   key=lambda f: int(re.search(r"frame-(\d+)-at-", f).group(1)))
    if len(files) < len(ts):
        sys.exit(f"{len(files)} snapshots in {snapdir} for {len(ts)} probe times")
    imgs, bad = {}, 0
    for p in probes:
        i = ts.index(p["g"])
        if i not in imgs:
            imgs[i] = np.array(Image.open(files[i]).convert("RGB"))
        ok, why = judge(imgs[i], p, pal)
        print(f"{'PASS' if ok else 'FAIL'} {p['shot']} t={p['t']} {p['kind']} {p.get('note', '')} ({why})")
        bad += not ok
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["times", "check"]); ap.add_argument("project"); ap.add_argument("probes")
    ap.add_argument("snapdir", nargs="?"); ap.add_argument("--only")
    A = ap.parse_args()
    probes, pal = load(A.project, A.probes, A.only.split(",") if A.only else None)
    if A.cmd == "times":
        print(",".join(f"{t:g}" for t in times(probes)))
    else:
        sys.exit(1 if check(probes, pal, A.snapdir) else 0)
