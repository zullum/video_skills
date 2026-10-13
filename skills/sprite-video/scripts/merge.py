# usage: python3 merge.py OUTDIR [--ref=DIR_A] DIR_B:0-2 DIR_C:1-5 DIR_A:8-23 ...
# Joins frames from several sliced sheets (e.g. a main grid plus an extra in-between sheet) into one
# folder for the player, in the order given. The first folder is the reference: frames from other
# sheets are scaled by the ratio of cell heights (all templates fit the base to the cell height the
# same way; --ref picks the reference, default the first folder), and near-background fills are recoloured to the reference background so no box shows.
# Run colorfix.py on an extra sheet BEFORE slicing it if its colours drifted. If the sheets were sliced
# with --anchor, put the main sheet first so everything is aligned on its head.
import sys, os, re, json, shutil

def rng(s):
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-"); out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return out

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
args = sys.argv[2:]; refdir = None
if args and args[0].startswith("--ref="): refdir = args.pop(0)[6:]
specs = [(p.rpartition(":")[0], rng(p.rpartition(":")[2])) for p in args]
ref = json.load(open(f"{refdir or specs[0][0]}/frames.json")); RH, BG = ref["cell"][1], ref["bg"]
RA = ref.get("anchor")      # sheets sliced with --anchor are also shifted onto the reference head
bgx = "%02X%02X%02X" % tuple(BG); frames = []
for d, idx in specs:
    D = json.load(open(f"{d}/frames.json")); s = RH / D["cell"][1]; ox = oy = 0
    if RA and D.get("anchor"): ox, oy = RA[0] - D["anchor"][0] * s, RA[1] - D["anchor"][1] * s
    for i in idx:
        f = dict(D["frames"][i]); name = f"f{len(frames):02d}.svg"
        svg = open(f"{d}/{f['file']}").read()
        def fix(m):
            c = [int(m.group(1)[k:k + 2], 16) for k in (0, 2, 4)]
            return f'fill="#{bgx}"' if min(c) > 195 and sum(abs(c[k] - BG[k]) for k in range(3)) < 28 else m.group(0)
        open(f"{out}/{name}", "w").write(re.sub(r'fill="#([0-9A-Fa-f]{6})"', fix, svg))
        f.update(file=name, from_=f"{d}:{i}", x=f["x"] * s + ox, y=f["y"] * s + oy, s=s * f.get("s", 1))
        frames.append(f)
res = dict(cell=ref["cell"], bg=BG, floor=ref.get("floor"), frames=frames)
json.dump(res, open(f"{out}/frames.json", "w"), indent=1)
open(f"{out}/frames.js", "w").write("window.FR=" + json.dumps(res) + ";")
print(len(frames), "frames ->", out)
