import critic_frames

TIMING = {"duration": 5, "shots": [{"id": "s1", "start": 0, "dur": 2.0, "words": []}, {"id": "s2", "start": 2.0, "dur": 3.0, "words": []}]}
SHOTS = [{"id": "s1", "say": "One.", "scene": "x", "beats": [{"at": 0.5, "do": "pop"}]}, {"id": "s2", "dur": 3, "scene": "x"}]


def test_frames_cover_start_middle_end_and_beats():
    fr = critic_frames.frames(TIMING, SHOTS)
    assert [round(t, 2) for sid, t, _ in fr if sid == "s1"] == [0.25, 0.65, 1.0, 1.75]
    assert [round(t, 2) for sid, t, _ in fr if sid == "s2"] == [2.25, 3.5, 4.75]
    assert [lab for sid, _, lab in fr][:4] == ["start", "pop", "mid", "end"]
