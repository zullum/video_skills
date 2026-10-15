"""<audio> tags of the project: narration per shot, the music bed ducked under it, the SFX stem."""
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
        out = subprocess.run(_vm(vm, "sfx", "duck_lane.py") + spoken + ["--base", str(base)],
                             capture_output=True, text=True, check=True).stdout
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


def tags(project, timing, vm, mix):
    return narration(timing) + music(project, timing, vm, mix.get("music", 0.5)) + sfx(project, timing, mix.get("sfx", 0.6))
