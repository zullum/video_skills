import json
import sys
from pathlib import Path

import gen_asset
from mx import manifest

WRITE = [sys.executable, "-c", "import sys; open(sys.argv[1], 'wb').write(b'png')"]
BOOM = [sys.executable, "-c", "import sys; sys.exit(7)"]


def spent(p):
    return json.load(open(p / "gen" / "budget.json"))["spent"]


def test_call_is_recorded(tmp_path):
    assert gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=WRITE) == 0
    assert spent(tmp_path) == 0.101


def test_existing_output_is_never_paid_twice(tmp_path):
    (tmp_path / "a.png").write_bytes(b"old")
    assert gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=BOOM) == 0
    assert not (tmp_path / "gen" / "budget.json").exists()


def test_refuses_past_the_limit(tmp_path):
    (tmp_path / "gen").mkdir()
    (tmp_path / "gen" / "budget.json").write_text('{"limit": 0.15, "spent": 0.101, "calls": []}')
    assert gen_asset.run(str(tmp_path), str(tmp_path / "b.png"), "x", [], gen_cmd=WRITE) == 3
    assert not (tmp_path / "b.png").exists()


def test_failed_call_costs_nothing(tmp_path):
    assert gen_asset.run(str(tmp_path), str(tmp_path / "c.png"), "x", [], gen_cmd=BOOM) == 7
    led = json.load(open(tmp_path / "gen" / "budget.json"))
    assert led["spent"] == 0 and led["calls"] == []


def test_manifest_defaults_and_round_trip(tmp_path):
    assert manifest.load(str(tmp_path)) == {"assets": {}, "sprites": {}}
    manifest.save(str(tmp_path), {"assets": {"a": {"w": 1}}, "sprites": {}})
    assert manifest.load(str(tmp_path))["assets"] == {"a": {"w": 1}}


def test_a_call_made_meanwhile_is_not_lost(tmp_path):
    # Another gen_asset run books its call (under the same lock) while ours is generating: both stay in the ledger.
    scripts = str(Path(__file__).parents[1] / "scripts")
    other = ("import sys; sys.path.insert(0, %r); import gen_asset; p = sys.argv[1].rsplit('/', 1)[0] + '/gen/budget.json'; "
             "gen_asset._locked(p, lambda led: (led['calls'].append({'file': 'other.png', 'size': '2K', 'price': 0.101}), "
             "led.__setitem__('spent', round(led['spent'] + 0.101, 3)))); open(sys.argv[1], 'wb').write(b'png')") % scripts
    (tmp_path / "gen").mkdir()
    assert gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=[sys.executable, "-c", other]) == 0
    led = json.load(open(tmp_path / "gen" / "budget.json"))
    assert sorted(c["file"] for c in led["calls"]) == ["a.png", "other.png"] and led["spent"] == 0.202


SLOW = [sys.executable, "-c", "import sys, time; time.sleep(0.6); open(sys.argv[1], 'wb').write(b'png')"]


def test_parallel_calls_never_pass_the_limit(tmp_path):
    import threading
    (tmp_path / "gen").mkdir()
    (tmp_path / "gen" / "budget.json").write_text('{"limit": 0.15, "spent": 0.0, "calls": []}')
    codes = []
    ts = [threading.Thread(target=lambda n=n: codes.append(gen_asset.run(str(tmp_path), str(tmp_path / f"{n}.png"), "x", [], gen_cmd=SLOW)))
          for n in ("a", "b")]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert sorted(codes) == [0, 3] and spent(tmp_path) == 0.101


def test_same_output_in_parallel_is_paid_once(tmp_path):
    import threading
    codes = []
    ts = [threading.Thread(target=lambda: codes.append(gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=SLOW)))
          for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert sorted(codes) == [0, 4] and spent(tmp_path) == 0.101


def test_relative_paths_resolve_against_the_project(tmp_path, monkeypatch):
    proj, other = tmp_path / "proj", tmp_path / "elsewhere"; proj.mkdir(); other.mkdir()
    monkeypatch.chdir(other)
    assert gen_asset.run(str(proj), "gen/c.png", "x", [], gen_cmd=WRITE) == 0
    assert (proj / "gen" / "c.png").exists() and not (other / "gen").exists()
    assert json.load(open(proj / "gen" / "budget.json"))["calls"][0]["file"] == "gen/c.png"
