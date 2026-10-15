"""Which scenes and actions exist, read from the header line every lib JS file starts with:
  lib/scenes/<x>.js   // @scene <name> @actions a,b,c        lib/toon-core.js   // @actions a,b (any scene)"""
import glob
import os
import re

SCENE = re.compile(r"^//\s*@scene\s+(\S+)\s+@actions\s+(\S*)", re.M)
GENERIC = re.compile(r"^//\s*@actions\s+(\S*)", re.M)


def load(lib_dir, extra=None):
    scenes = {}
    for d in [os.path.join(lib_dir, "scenes")] + ([extra] if extra else []):
        for f in sorted(glob.glob(os.path.join(d, "*.js"))):
            for name, acts in SCENE.findall(open(f).read()):
                scenes[name] = [a for a in acts.split(",") if a]
    core = os.path.join(lib_dir, "toon-core.js")
    m = GENERIC.search(open(core).read()) if os.path.exists(core) else None
    return {"scenes": scenes, "generic": [a for a in m.group(1).split(",") if a] if m else []}
