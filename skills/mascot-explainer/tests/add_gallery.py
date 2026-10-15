"""Dev helper: append gallery shots and probes (two JSON files) to tests/gallery, replacing shots with the same id.
   cd skills/mascot-explainer && scripts/py tests/add_gallery.py shots.json probes.json"""
import json, sys
G = "tests/gallery/"
shots, probes = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
S = json.load(open(G + "shots.json")); ids = {s["id"] for s in shots}
S["shots"] = [s for s in S["shots"] if s["id"] not in ids] + shots
P = [p for p in json.load(open(G + "probes.json")) if p["shot"] not in ids] + probes
def dump(obj, path, key=None):
    rows = obj[key] if key else obj
    body = ",\n".join("  " + json.dumps(r) for r in rows)
    open(path, "w").write(('{"style": "style.json", "shots": [\n' + body + "\n]}\n") if key else ("[\n" + body + "\n]\n"))
dump(S, G + "shots.json", "shots"); dump(P, G + "probes.json")
print(len(S["shots"]), "shots,", len(P), "probes")
