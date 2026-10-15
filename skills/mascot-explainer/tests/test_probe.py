import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

SKILL = Path(__file__).parents[1]
PROBES = [{"shot": "sp", "t": 0.5, "kind": "px", "x": 5, "y": 5, "color": "bgDeep"},
          {"shot": "sp", "t": 0.5, "kind": "area", "rect": [20, 0, 20, 20], "color": "text", "min": 0.9},
          {"shot": "sp", "t": 0.5, "kind": "noarea", "rect": [0, 0, 40, 20], "color": "#00B140"},
          {"shot": "other", "t": 0.2, "kind": "px", "x": 0, "y": 0, "color": "#000000"}]   # not built: skipped


def project(tmp_path, probes):
    (tmp_path / "audio").mkdir(parents=True)
    (tmp_path / "audio" / "sfx_cues.json").write_text(json.dumps({"slots": {"sp": 0}}))
    (tmp_path / "style.json").write_text(json.dumps({"palette": {"bgDeep": "#0B2E35", "text": "#FFFFFF"}}))
    (tmp_path / "probes.json").write_text(json.dumps(probes))
    im = Image.new("RGB", (40, 20), "#0B2E35"); im.paste((255, 255, 255), (20, 0, 40, 20))
    (tmp_path / "snap").mkdir(); im.save(tmp_path / "snap" / "frame-00-at-0.5s.png")
    return tmp_path


def probe(*args):
    return subprocess.run([sys.executable, "scripts/probe.py", *map(str, args)], capture_output=True, text=True, cwd=SKILL)


def test_times(tmp_path):
    p = project(tmp_path, PROBES)
    assert probe("times", p, p / "probes.json").stdout.strip() == "0.5"


def test_check_passes(tmp_path):
    p = project(tmp_path, PROBES)
    r = probe("check", p, p / "probes.json", p / "snap")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.count("PASS") == 3


def test_check_fails_with_shot_and_time(tmp_path):
    p = project(tmp_path, [dict(PROBES[0], color="#FF0000")] + PROBES[1:])
    r = probe("check", p, p / "probes.json", p / "snap")
    assert r.returncode == 1 and "FAIL sp t=0.5" in r.stdout
