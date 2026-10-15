import json

import pytest

import build
from mx import html, registry


def project(tmp_path, shots, manifest=None):
    tmp_path.mkdir(parents=True)
    (tmp_path / "style.json").write_text(json.dumps({"size": [1920, 1080], "fps": 30, "palette": {"bgDeep": "#0B2E35"}}))
    (tmp_path / "shots.json").write_text(json.dumps({"shots": shots}))
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "manifest.json").write_text(json.dumps(manifest or {"assets": {"blob": {}}, "sprites": {}}))
    return tmp_path


def lib(tmp_path):
    d = tmp_path / "lib"; (d / "scenes").mkdir(parents=True); (d / "fonts").mkdir()
    (d / "scenes" / "demo.js").write_text("// @scene demo @actions pop,zoom\n")
    (d / "toon-core.js").write_text("// @actions push\n")
    return d


def test_builds_project(tmp_path):
    p = project(tmp_path / "p", [{"id": "s01", "dur": 2, "scene": "demo", "params": {"asset": "blob"},
                                  "beats": [{"at": 0.2, "do": "pop", "args": {"items": [0, 1]}}], "in": "cut"},
                                 {"id": "s02", "dur": 1, "scene": "demo", "in": "whip"}])
    build.main(str(p), sfx=False, lib_dir=str(lib(tmp_path)))
    idx = (p / "index.html").read_text()
    assert 'data-composition-src="compositions/s02.html" data-start="2.000" data-duration="1.000"' in idx
    assert 'data-duration="3.000"' in idx and "TDisplay" in idx and "assets/js/scenes/demo.js" in idx
    events = json.loads((p / "compositions" / "s01.motion.json").read_text())["events"]
    assert [e["t"] for e in events] == [0.2, 0.32]
    cues = json.loads((p / "audio" / "sfx_cues.json").read_text())
    assert cues["slots"] == {"s01": 0, "s02": 2} and cues["cues"][0]["fx"] == "whoosh" and cues["duration"] == 3
    assert '"out": "whip"' in (p / "compositions" / "s01.html").read_text()
    assert (p / "assets" / "js" / "toon-core.js").exists()


@pytest.mark.parametrize("shot,msg", [
    ({"id": "s01", "dur": 1, "scene": "bubblez"}, "s01: unknown scene 'bubblez'; known: demo"),
    ({"id": "s01", "dur": 1, "scene": "demo", "beats": [{"at": 0, "do": "popp"}]}, "s01: scene 'demo' has no action 'popp'"),
    ({"id": "s01", "dur": 1, "scene": "demo", "params": {"items": [{"asset": "jarr"}]}}, "s01: unknown asset 'jarr'; have: blob"),
    ({"id": "s01", "dur": 1, "scene": "demo", "params": {"sprite": "run"}}, "s01: unknown sprite 'run'; have: ")])
def test_validation(tmp_path, shot, msg):
    p = project(tmp_path / "p", [shot])
    with pytest.raises(SystemExit, match=msg):
        build.main(str(p), sfx=False, lib_dir=str(lib(tmp_path)))
    assert not (p / "index.html").exists()


def test_generic_actions_are_allowed(tmp_path):
    p = project(tmp_path / "p", [{"id": "s01", "dur": 1, "scene": "demo", "beats": [{"at": 0, "do": "push"}]}])
    build.main(str(p), sfx=False, lib_dir=str(lib(tmp_path)))


def test_project_scene_extends_registry(tmp_path):
    extra = tmp_path / "extra"; extra.mkdir()
    (extra / "oneoff.js").write_text("// @scene oneoff @actions wave\n")
    assert registry.load(str(lib(tmp_path)), str(extra))["scenes"]["oneoff"] == ["wave"]


def test_scene_html_escapes_script_end():
    assert "<\\/script>" in html.scene_html("s01", {"params": {"text": "</script>"}}, 1, (1920, 1080))


def test_sfx_kinds_sit_under_the_voice_and_style_overrides(tmp_path):
    p = project(tmp_path / "p", [{"id": "s01", "dur": 1, "scene": "demo"}])
    st = json.loads((p / "style.json").read_text()); st["sfx_kinds"] = {"pop": ["pop", -20, {}]}
    (p / "style.json").write_text(json.dumps(st))
    build.main(str(p), sfx=False, lib_dir=str(lib(tmp_path)))
    kinds = json.loads((p / "audio" / "sfx_cues.json").read_text())["event_kinds"]
    assert kinds["impact"][1] <= -12 and kinds["pop"] == ["pop", -20, {}]
