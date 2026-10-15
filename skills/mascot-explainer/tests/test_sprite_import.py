import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).parents[1]
CLIPPED = '<svg xmlns="http://www.w3.org/2000/svg"><defs><clipPath id="fig"><path d="M0,0Z"/></clipPath></defs></svg>'


def frames_dir(tmp_path, svgs):
    d = tmp_path / "frames"; d.mkdir()
    frames = [{"file": f"f{i:02d}.svg", "src": i, "x": 10.0 + i, "y": 20.0, "w": 100, "h": 120, "anc": None, "gnd": None}
              for i in range(len(svgs))]
    (d / "frames.json").write_text(json.dumps({"cell": [200.0, 180.0], "bg": [0, 177, 64], "floor": [170.0, 174.0],
                                               "anchor": None, "frames": frames}))
    for i, s in enumerate(svgs):
        (d / f"f{i:02d}.svg").write_text(s)
    return d


def run(d, project, name):
    return subprocess.run([sys.executable, "scripts/sprite_import.py", str(d), str(project), name],
                          capture_output=True, text=True, cwd=SKILL)


def test_imports_frames_and_registers_sprite(tmp_path):
    r = run(frames_dir(tmp_path, [CLIPPED, CLIPPED]), tmp_path / "p", "pushup")
    assert r.returncode == 0, r.stderr
    sp = json.load(open(tmp_path / "p" / "assets" / "manifest.json"))["sprites"]["pushup"]
    assert sp == {"dir": "assets/sprites/pushup", "cell": [200.0, 180.0], "floor": [170.0, 174.0],
                  "frames": [{"file": "f00.svg", "x": 10.0, "y": 20.0, "w": 100, "h": 120},
                             {"file": "f01.svg", "x": 11.0, "y": 20.0, "w": 100, "h": 120}]}
    assert (tmp_path / "p" / "assets" / "sprites" / "pushup" / "f01.svg").exists()


def test_refuses_frames_sliced_without_clip(tmp_path):
    r = run(frames_dir(tmp_path, [CLIPPED, "<svg></svg>"]), tmp_path / "p", "pushup")
    assert r.returncode != 0 and "pushup: f01.svg was sliced without --clip" in r.stderr
    assert not (tmp_path / "p" / "assets" / "sprites" / "pushup").exists()
