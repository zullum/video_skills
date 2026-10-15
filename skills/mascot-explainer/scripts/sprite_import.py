"""Bring a sliced sprite into a project.   scripts/py scripts/sprite_import.py FRAMES_DIR PROJECT NAME
FRAMES_DIR is sprite-video's slice.py output made with --clip (f00.svg..., frames.json). The SVGs are copied to
PROJECT/assets/sprites/NAME/ and assets/manifest.json gets sprites[NAME] = {dir, cell, floor, frames}."""
import json
import os
import shutil
import sys

from mx import manifest


def main(frames_dir, project, name):
    fr = json.load(open(os.path.join(frames_dir, "frames.json")))
    for f in fr["frames"]:
        if '<clipPath id="fig">' not in open(os.path.join(frames_dir, f["file"])).read():
            sys.exit(f"{name}: {f['file']} was sliced without --clip; re-run slice.py with --clip")
    rel = f"assets/sprites/{name}"
    dest = os.path.join(project, rel)
    os.makedirs(dest, exist_ok=True)
    for f in fr["frames"]:
        shutil.copy(os.path.join(frames_dir, f["file"]), dest)
    m = manifest.load(project)
    m["sprites"][name] = {"dir": rel, "cell": fr["cell"], "floor": fr.get("floor"),
                          "frames": [{k: f[k] for k in ("file", "x", "y", "w", "h")} for f in fr["frames"]]}
    manifest.save(project, m)
    print(f"{name}: {len(fr['frames'])} frames -> {rel}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
