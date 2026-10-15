import pytest

import timing

SH = [{"id": "s1", "say": "Two sets."}, {"id": "s2", "dur": 3}]


def test_layout():
    t = timing.layout(SH, {"s1": 1.6}, {"s1": [{"w": "two", "t": 0.1}]})
    a, b = t["shots"]
    assert a["dur"] == pytest.approx(2.1) and a["words"] == [{"w": "two", "t": pytest.approx(0.3)}]
    assert a["voice"] == "assets/audio/narration/s1.wav" and a["lead"] == 0.2 and a["speech"] == 1.6
    assert b["start"] == pytest.approx(2.1) and t["duration"] == pytest.approx(5.1) and b["voice"] is None


def test_hold_and_min_dur():
    t = timing.layout([{"id": "s1", "say": "x", "hold": 1, "dur": 1}], {"s1": 1.0}, {"s1": []})
    assert t["shots"][0]["dur"] == pytest.approx(2.5)
    t = timing.layout([{"id": "s1", "say": "x", "dur": 4}], {"s1": 1.0}, {"s1": []})
    assert t["shots"][0]["dur"] == pytest.approx(4)


def test_missing_dur_names_shot():
    with pytest.raises(SystemExit, match="s2"):
        timing.layout([{"id": "s2"}], {}, {})


def test_silent_mode_ignores_say():
    t = timing.layout([{"id": "s1", "say": "x", "dur": 2}], {}, {}, silent=True)
    assert t["shots"][0]["voice"] is None and t["shots"][0]["dur"] == 2
