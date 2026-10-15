"""Every shots.json example in references/scene-catalog*.md must build (with fake word times and dummy assets)."""
import json
import re
from pathlib import Path

import pytest

import build
from mx.beats import norm

SKILL = Path(__file__).parents[1]
BLOCKS = [b for f in sorted((SKILL / "references").glob("scene-catalog*.md"))
          for b in re.findall(r"```json\n(.*?)```", f.read_text(), re.S)]


def fake_timing(shot):
    words = [norm(w) for w in shot.get("say", "").split() if norm(w)]
    dur = 0.2 + 0.3 * len(words) + 0.5 if words else shot.get("dur", 2)
    return {"id": shot["id"], "start": 0, "dur": dur, "lead": 0.2, "speech": dur - 0.5, "voice": None,
            "words": [{"w": w, "t": round(0.2 + 0.3 * i, 3)} for i, w in enumerate(words)]}


@pytest.mark.parametrize("block", BLOCKS, ids=[json.loads(b)["id"] for b in BLOCKS])
def test_catalog_example_builds(tmp_path, block):
    shot = json.loads(block)
    used = [shot.get("params") or {}] + [b.get("args") or {} for b in shot.get("beats") or []]
    man = {"assets": {n: {"file": "x.svg", "w": 100, "h": 100, "anchor": [0.5, 1], "holes": []}
                      for k in ("asset", "hand", "item") for n in build._walk(used, k)},
           "sprites": {n: {"dir": "x", "cell": [100, 100], "floor": None, "frames": []} for n in build._walk(used, "sprite")}}
    (tmp_path / "assets").mkdir(); (tmp_path / "audio").mkdir()
    (tmp_path / "assets" / "manifest.json").write_text(json.dumps(man))
    (tmp_path / "style.json").write_text((SKILL / "tests" / "gallery" / "style.json").read_text())
    (tmp_path / "shots.json").write_text(json.dumps({"shots": [shot]}))
    (tmp_path / "audio" / "timing.json").write_text(json.dumps({"duration": 1, "shots": [fake_timing(shot)]}))
    build.main(str(tmp_path), sfx=False)
    assert (tmp_path / "compositions" / f"{shot['id']}.html").exists()


def test_catalog_has_examples():
    assert len(BLOCKS) >= 14
