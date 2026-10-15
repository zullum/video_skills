"""Frames for the Critic.   scripts/py scripts/critic_frames.py PROJECT [--out critique/round-1]
Snapshots every shot at its start, middle and end and 0.15 s after every beat, then tiles them into labelled
sheets (one row per shot, the narration line under it): OUT/sheet-<n>.png. Read them, give them to a fresh Critic."""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

import deps
from mx import beats


def frames(timing, shots):
    rows = {r["id"]: r for r in timing["shots"]}
    out = []
    for s in shots:
        r = rows[s["id"]]
        res = beats.resolve_shot(s, r["dur"], r["words"], None, (1920, 1080))
        pts = [(0.25, "start"), (r["dur"] / 2, "mid"), (r["dur"] - 0.25, "end")]
        pts += [(min(b["t"] + 0.15, r["dur"] - 0.05), b["do"]) for b in res["beats"]]
        out += [(s["id"], round(r["start"] + t, 3), lab) for t, lab in sorted(pts)]
    return out


def sheets(shots, fr, snapdir, outdir, per_sheet=6):
    from PIL import Image, ImageDraw
    files = sorted(glob.glob(os.path.join(snapdir, "frame-*-at-*.png")), key=lambda f: int(re.search(r"frame-(\d+)-", f).group(1)))
    say = {s["id"]: s.get("say", "") for s in shots}
    order = list(dict.fromkeys(sid for sid, _, _ in fr))
    for n in range(0, len(order), per_sheet):
        ids = order[n:n + per_sheet]
        W = Image.new("RGB", (6 * 384, len(ids) * 246), "black"); d = ImageDraw.Draw(W)
        for row, sid in enumerate(ids):
            cells = [(i, lab) for i, (s, _, lab) in enumerate(fr) if s == sid][:6]
            for col, (i, lab) in enumerate(cells):
                W.paste(Image.open(files[i]).convert("RGB").resize((384, 216)), (col * 384, row * 246))
                d.text((col * 384 + 6, row * 246 + 4), f"{sid} {lab}", fill=(255, 230, 0))
            d.text((6, row * 246 + 222), f"{sid}: {say[sid]}", fill=(255, 255, 255))
        W.save(os.path.join(outdir, f"sheet-{n // per_sheet + 1}.png"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--out", default="critique/round-1")
    A = ap.parse_args()
    P, out = A.project, os.path.join(A.project, A.out)
    os.makedirs(out, exist_ok=True)
    shots = json.load(open(os.path.join(P, "shots.json")))["shots"]
    fr = frames(json.load(open(os.path.join(P, "audio", "timing.json"))), shots)
    hf = os.path.join(deps.locate("vm"), "scripts", "hf")
    r = subprocess.run([hf, "snapshot", P, "--at", ",".join(f"{t:g}" for _, t, _ in fr), "--no-end", "-o", os.path.join(out, "snaps")],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-800:])
    sheets(shots, fr, os.path.join(out, "snaps"), out)
    print(f"{len(fr)} frames -> {out}/sheet-*.png")


if __name__ == "__main__":
    main()
