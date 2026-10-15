"""Emit a data-automation volume lane that ducks the Track under Narration.

    python duck_lane.py narration.wav --at 7.0 --base 0.5 --duck-db -10 [--track-start 0]
    python duck_lane.py nar/s1.wav@0.35 nar/s2.wav@4.2 --base 0.5      (one Kokoro WAV per line)

Each narration is a WAV plus its data-start (`@start`, else --at); spans from all of them merge into one lane.

Speech spans come from the narration's own energy (20 ms RMS above
--gate dBFS, gaps shorter than --merge s joined). Like HyperFrames' media-use
duckLane(), but the ramp down (attack) finishes AT each span start instead of
beginning there, so the first syllable is never masked; the ramp up (release)
starts at the span end. Lane values are absolute gains: the
renderer ignores data-volume once a volume lane exists, so --base must be the
Track's normal data-volume.
"""
import argparse
import json

import numpy as np
import soundfile as sf


def speech_spans(path, gate_db=-40.0, merge=0.6, win=0.02):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(axis=1)
    hop = int(sr * win)
    frames = x[: len(x) // hop * hop].reshape(-1, hop)
    loud = 20 * np.log10(np.sqrt(np.mean(frames**2, axis=1)) + 1e-12) > gate_db
    spans, start = [], None
    for i, on in enumerate(np.append(loud, False)):
        if on and start is None:
            start = i * win
        elif not on and start is not None:
            spans.append([start, i * win])
            start = None
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < merge:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return merged


def lane(spans, at, base, duck_db, attack=0.15, release=0.4, track_start=0.0):
    ducked = round(base * 10 ** (duck_db / 20), 4)
    pts = [{"t": 0.0, "v": base}]
    for s, e in spans:
        a, b = s + at - track_start, e + at - track_start
        pts += [{"t": round(max(0.0, a - attack), 3), "v": base}, {"t": round(a, 3), "v": ducked},
                {"t": round(b, 3), "v": ducked}, {"t": round(b + release, 3), "v": base}]
    return {"version": 1, "lanes": [{"target": "volume", "points": pts}]}


def all_spans(items, at, gate_db, merge):
    """Spans of every `wav[@start]` item on the composition timeline, sorted and merged."""
    spans = []
    for item in items:
        path, _, start = item.rpartition("@") if "@" in item else (item, "", at)
        spans += [[s + float(start), e + float(start)] for s, e in speech_spans(path, gate_db, merge)]
    merged = []
    for s in sorted(spans):
        if merged and s[0] - merged[-1][1] < merge:
            merged[-1][1] = max(merged[-1][1], s[1])
        else:
            merged.append(s)
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("narration", nargs="+", help="narration.wav or narration.wav@<data-start>")
    ap.add_argument("--at", type=float, default=0.0, help="data-start of items without @, s")
    ap.add_argument("--base", type=float, required=True, help="Track gain outside speech")
    ap.add_argument("--duck-db", type=float, default=-10.0)
    ap.add_argument("--gate", type=float, default=-40.0)
    ap.add_argument("--merge", type=float, default=0.6)
    ap.add_argument("--track-start", type=float, default=0.0)
    args = ap.parse_args()
    spans = all_spans(args.narration, args.at, args.gate, args.merge)
    print(json.dumps(lane(spans, 0.0, args.base, args.duck_db, track_start=args.track_start)))


if __name__ == "__main__":
    main()
