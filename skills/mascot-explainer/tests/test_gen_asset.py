import json
import sys

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
    assert not (tmp_path / "gen" / "budget.json").exists()


def test_manifest_defaults_and_round_trip(tmp_path):
    assert manifest.load(str(tmp_path)) == {"assets": {}, "sprites": {}}
    manifest.save(str(tmp_path), {"assets": {"a": {"w": 1}}, "sprites": {}})
    assert manifest.load(str(tmp_path))["assets"] == {"a": {"w": 1}}


def test_a_call_made_meanwhile_is_not_lost(tmp_path):
    # Another gen_asset run records its call while ours is generating: both must stay in the ledger.
    other = ("import json, sys; p = sys.argv[1].rsplit('/', 1)[0] + '/gen/budget.json'; "
             "json.dump({'limit': 1.5, 'spent': 0.101, 'calls': [{'file': 'other.png', 'size': '2K', 'price': 0.101}]}, open(p, 'w')); "
             "open(sys.argv[1], 'wb').write(b'png')")
    (tmp_path / "gen").mkdir()
    assert gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=[sys.executable, "-c", other]) == 0
    led = json.load(open(tmp_path / "gen" / "budget.json"))
    assert [c["file"] for c in led["calls"]] == ["other.png", "a.png"] and led["spent"] == 0.202
