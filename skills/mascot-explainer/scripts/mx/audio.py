"""<audio> tags of the project: narration per shot, the music bed ducked under it, the SFX stem."""
# Event gains for build_sfx.py in a voice-led explainer: about 10 dB under the narration (viral-motion's own
# defaults, e.g. impact -6, are for films without wall-to-wall voice). style.json "sfx_kinds" overrides any.
SFX_KINDS = {"pop": ["pop", -19, {}], "whoosh": ["whoosh", -17, {"dur": 0.45}], "shimmer": ["shimmer", -16, {}],
             "impact": ["impact", -14, {}], "stamp": ["impact", -15, {"dur": 1.2}], "tick": ["tick", -21, {}],
             "snap": ["snap", -17, {}], "chime": ["chime", -18, {}], "blip": ["blip", -22, {}]}
import json
import os
import subprocess
import sys


def _vm(vm, *parts):
    return [os.path.join(vm, "scripts", "py"), os.path.join(vm, "scripts", *parts)]


def narration(timing):
    return [f'<audio id="nar-{s["id"]}" src="{s["voice"]}" data-start="{s["start"] + s["lead"]:.3f}" '
            f'data-duration="{s["speech"]:.3f}" data-track-index="9" data-volume="1"></audio>'
            for s in timing["shots"] if s.get("voice")]


def music(project, timing, vm, base):
    if not vm or not os.path.exists(os.path.join(project, "assets", "audio", "music.wav")):
        return []
    spoken = [f'{os.path.join(project, s["voice"])}@{s["start"] + s["lead"]:.3f}' for s in timing["shots"] if s.get("voice")]
    lane = ""
    if spoken:
        r = subprocess.run(_vm(vm, "sfx", "duck_lane.py") + spoken + ["--base", str(base)], capture_output=True, text=True)
        if r.returncode:
            sys.exit("duck_lane failed:\n" + r.stderr[-800:])
        out = r.stdout
        lane = f" data-automation='{json.dumps(json.loads(out))}'"
    return [f'<audio id="music" src="assets/audio/music.wav" data-start="0" data-duration="{timing["duration"]:.3f}" '
            f'data-track-index="10" data-volume="{base}"{lane}></audio>']


def build_sfx(project, vm):
    r = subprocess.run(_vm(vm, "sfx", "build_sfx.py") + [project], capture_output=True, text=True)
    if r.returncode:
        sys.exit("build_sfx failed:\n" + r.stderr[-800:])


def sfx(project, timing, vol):
    if not os.path.exists(os.path.join(project, "assets", "audio", "sfx.wav")):
        return []
    return [f'<audio id="sfx-main" src="assets/audio/sfx.wav" data-start="0" data-duration="{timing["duration"]:.3f}" '
            f'data-track-index="11" data-volume="{vol}"></audio>']


def tags(project, timing, vm, mix, with_sfx=True):
    stem = sfx(project, timing, mix.get("sfx", 0.35))
    if stem and not with_sfx:                       # an old stem would be out of sync with edited beats
        print("note: SFX left out (--no-sfx); build without --no-sfx before rendering", file=sys.stderr)
        stem = []
    return narration(timing) + music(project, timing, vm, mix.get("music", 0.7)) + stem
