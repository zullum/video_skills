from pathlib import Path

import pytest

from mx import beats, whisper

W = [{"w": "push-ups", "t": 0.26}, {"w": "rows", "t": 1.23}, {"w": "rows", "t": 2.0}]
FIX = Path(__file__).parent / "fixtures" / "whisper.json"


def test_numbers_end_and_clamp():
    assert beats.resolve_at(0.5, 3, [], "s1") == 0.5
    assert beats.resolve_at("end-0.6", 3, [], "s1") == pytest.approx(2.4)
    assert beats.resolve_at("end", 3, [], "s1") == 3
    assert beats.resolve_at(5, 3, [], "s1") == 3


def test_words():
    assert beats.resolve_at("word:rows", 3, W, "s1") == 1.23
    assert beats.resolve_at("word:rows#2", 3, W, "s1") == 2.0
    assert beats.resolve_at("word:Push-ups+0.1", 3, W, "s1") == pytest.approx(0.36)
    assert beats.resolve_at("word:rows-0.2", 3, W, "s1") == pytest.approx(1.03)


def test_missing_word_names_shot_and_heard_words():
    with pytest.raises(ValueError, match=r"s1: 'squats' is not in the narration; heard: push-ups, rows"):
        beats.resolve_at("word:squats", 3, W, "s1")


def test_events():
    assert [e["t"] for e in beats.events_for({"t": 1, "do": "pop", "args": {"items": [0, 1, 2]}})] == [1, 1.12, 1.24]
    many = beats.events_for({"t": 1, "do": "fill", "args": {"count": 24, "stagger": 0.04}})
    assert len(many) == 8 and many[-1]["t"] == pytest.approx(1.92)
    assert beats.events_for({"t": 2, "do": "zoom", "args": {"i": 0}}) == [{"t": 2.3, "kind": "whoosh", "note": "zoom"}]
    assert beats.events_for({"t": 1, "do": "draw", "args": {}}) == []
    assert beats.events_for({"t": 1, "do": "slam", "args": {}}) == [{"t": 1, "kind": "impact", "note": "slam"}]


def test_resolve_shot_out_and_auto_zoom():
    shot = {"scene": "bubbles", "params": {}, "beats": [{"at": "end-0.2", "do": "pop"}, {"at": 0.1, "do": "pop"}]}
    r = beats.resolve_shot(shot, 3, [], "whip", (1920, 1080))
    assert r["out"] == "whip" and [b["t"] for b in r["beats"]] == [0.1, 2.8] and r["in"] == "cut"
    z = beats.resolve_shot(shot, 3, [], "zoomIn", (1920, 1080))["beats"][-1]
    assert z == {"t": 2.5, "do": "zoomInto", "args": {"x": 960, "y": 540, "dur": 0.5}}
    zoomed = dict(shot, beats=[{"at": 2, "do": "zoom", "args": {"i": 0}}])
    assert [b["do"] for b in beats.resolve_shot(zoomed, 3, [], "zoomIn", (1920, 1080))["beats"]] == ["zoom"]


def test_transition_cues():
    shots = [{"in": "cut"}, {"in": "whip"}, {"in": "flash"}]
    cues = beats.transition_cues(shots, [0, 2.0, 4.5], ["a", "b", "c"])
    assert cues[0] == {"t": 2.0, "fx": "whoosh", "gain_db": -10, "peak": True, "args": {"dur": 0.5}, "label": "b in:whip"}
    assert cues[1]["fx"] == "impact" and cues[1]["t"] == 4.5


def test_whisper_words():
    assert whisper.words(str(FIX), 0.2)[:2] == [{"w": "push-ups", "t": 0.26}, {"w": "rows", "t": 1.43}]
