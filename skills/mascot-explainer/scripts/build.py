"""Build the HyperFrames project.   scripts/py scripts/build.py PROJECT [--only s01,s02] [--no-sfx]
Reads style.json, shots.json, audio/timing.json (else every shot's "dur", silent) and assets/manifest.json;
checks every scene, action, asset and sprite name first; then writes index.html, compositions/<id>.html and
<id>.motion.json, audio/sfx_cues.json, copies lib/ into assets/js + assets/fonts, builds the SFX stem
(viral-motion build_sfx.py) and ducks the music bed (assets/audio/music.wav, if present) under the narration."""
import argparse
import glob
import json
import os
import shutil
import sys

import deps
import timing as timing_mod
from mx import audio, beats, html, manifest as manifest_mod, registry

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = (("asset", "assets"), ("hand", "assets"), ("item", "assets"), ("sprite", "sprites"))


def _walk(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and isinstance(v, str):
                yield v
            else:
                yield from _walk(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, key)


def validate(shots, reg, man):
    for s in shots:
        sid, sc = s["id"], s.get("scene")
        if sc not in reg["scenes"]:
            sys.exit(f"{sid}: unknown scene '{sc}'; known: {', '.join(sorted(reg['scenes']))}")
        acts = reg["scenes"][sc] + reg["generic"]
        for b in s.get("beats") or []:
            if b["do"] not in acts:
                sys.exit(f"{sid}: scene '{sc}' has no action '{b['do']}'; it has: {', '.join(acts)}")
        used = [s.get("params") or {}] + [b.get("args") or {} for b in s.get("beats") or []]
        for key, kind in REFS:
            for name in _walk(used, key):
                if name not in man[kind]:
                    sys.exit(f"{sid}: unknown {kind[:-1]} '{name}'; have: {', '.join(sorted(man[kind]))}")


def shot_times(P, shots):
    path = os.path.join(P, "audio", "timing.json")
    if not os.path.exists(path):
        return timing_mod.layout(shots, {}, {}, silent=True)
    rows = {r["id"]: r for r in json.load(open(path))["shots"]}
    missing = [s["id"] for s in shots if s["id"] not in rows]
    if missing:
        sys.exit(f"{', '.join(missing)} not in audio/timing.json: run timing.py again")
    out, start = [], 0.0
    for s in shots:
        r = dict(rows[s["id"]], start=round(start, 3))
        if not r["voice"] and "dur" in s:
            r["dur"] = float(s["dur"])                     # a silent shot follows shots.json
        out.append(r)
        start += r["dur"]
    return {"duration": round(start, 3), "shots": out}


def copy_lib(lib_dir, P):
    js = os.path.join(P, "assets", "js")
    os.makedirs(os.path.join(js, "scenes"), exist_ok=True)
    for f in glob.glob(os.path.join(lib_dir, "*.js")):
        shutil.copy(f, js)
    for f in glob.glob(os.path.join(lib_dir, "scenes", "*.js")):
        shutil.copy(f, os.path.join(js, "scenes"))
    if os.path.isdir(os.path.join(lib_dir, "fonts")):
        shutil.copytree(os.path.join(lib_dir, "fonts"), os.path.join(P, "assets", "fonts"), dirs_exist_ok=True)
    rest = sorted(os.path.basename(f) for f in glob.glob(os.path.join(js, "*.js")) if not f.endswith("toon-core.js"))
    return (["assets/js/toon-core.js"] if os.path.exists(os.path.join(js, "toon-core.js")) else []) + \
        [f"assets/js/{f}" for f in rest] + \
        sorted(f"assets/js/scenes/{os.path.basename(f)}" for f in glob.glob(os.path.join(js, "scenes", "*.js")))


def main(project, only=None, sfx=True, lib_dir=None):
    P, lib_dir = project, lib_dir or os.path.join(SKILL, "lib")
    style = json.load(open(os.path.join(P, "style.json")))
    shots = json.load(open(os.path.join(P, "shots.json")))["shots"]
    if only:
        shots = [s for s in shots if s["id"] in only] or sys.exit(f"--only matched no shot: {only}")
    man = manifest_mod.load(P)
    validate(shots, registry.load(lib_dir, os.path.join(P, "assets", "js", "scenes")), man)
    t = shot_times(P, shots)
    size, ids = tuple(style["size"]), [s["id"] for s in shots]
    resolved = []
    for k, (s, row) in enumerate(zip(shots, t["shots"])):
        nxt = shots[k + 1].get("in") if k + 1 < len(shots) else None
        try:
            resolved.append(beats.resolve_shot(s, row["dur"], row["words"], nxt, size))
        except ValueError as e:
            sys.exit(str(e))
    scripts = copy_lib(lib_dir, P)
    comp = os.path.join(P, "compositions")
    os.makedirs(comp, exist_ok=True)
    for f in glob.glob(os.path.join(comp, "*.motion.json")):
        os.remove(f)                                         # a dropped shot makes no sound
    for sid, row, r in zip(ids, t["shots"], resolved):
        open(os.path.join(comp, f"{sid}.html"), "w").write(html.scene_html(sid, r, row["dur"], size))
        events = [e for b in r["beats"] for e in beats.events_for(b)]
        json.dump({"events": events}, open(os.path.join(comp, f"{sid}.motion.json"), "w"), indent=1)
    slots = [(sid, row["start"], row["dur"]) for sid, row in zip(ids, t["shots"])]
    os.makedirs(os.path.join(P, "audio"), exist_ok=True)
    cues = {"duration": t["duration"], "slots": {i: st for i, st, _ in slots},
            "cues": beats.transition_cues(resolved, [st for _, st, _ in slots], ids),
            "event_kinds": dict(audio.SFX_KINDS, **style.get("sfx_kinds", {}))}
    json.dump(cues, open(os.path.join(P, "audio", "sfx_cues.json"), "w"), indent=1)
    vm = deps.locate("vm") if sfx else None
    if vm:
        audio.build_sfx(P, vm)
    tags = audio.tags(P, t, vm, style.get("mix", {}))
    open(os.path.join(P, "index.html"), "w").write(html.index_html(style, man, slots, tags, scripts))
    print(f"{len(shots)} shots, {t['duration']:.2f} s, {len(tags)} audio tags -> {os.path.join(P, 'index.html')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--only"); ap.add_argument("--no-sfx", action="store_true")
    A = ap.parse_args()
    main(A.project, only=A.only.split(",") if A.only else None, sfx=not A.no_sfx)
