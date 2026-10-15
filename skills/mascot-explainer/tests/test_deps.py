import os

import pytest

import deps


def mk(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def test_sibling_with_marker_wins(tmp_path):
    skills = tmp_path / "skills"; me = skills / "mascot-explainer"; me.mkdir(parents=True)
    mk(str(skills / "sprite-video" / "scripts" / "trace2.py"))
    mk(str(tmp_path / "home" / ".claude" / "skills" / "sprite-video" / "scripts" / "trace2.py"))
    found = deps.locate("sv", home=str(tmp_path / "home"), skill_dir=str(me))
    assert found == os.path.realpath(skills / "sprite-video")


def test_falls_back_to_home_when_sibling_lacks_marker(tmp_path):
    skills = tmp_path / "skills"; me = skills / "mascot-explainer"; me.mkdir(parents=True)
    (skills / "viral-motion").mkdir()                       # repo copy without .venv
    home_vm = tmp_path / "home" / ".claude" / "skills" / "viral-motion"
    mk(str(home_vm / ".venv" / "bin" / "python"))
    assert deps.locate("vm", home=str(tmp_path / "home"), skill_dir=str(me)) == os.path.realpath(home_vm)


def test_missing_names_the_search_paths(tmp_path):
    me = tmp_path / "skills" / "mascot-explainer"; me.mkdir(parents=True)
    with pytest.raises(SystemExit, match="viral-motion not found"):
        deps.locate("vm", home=str(tmp_path / "home"), skill_dir=str(me))
