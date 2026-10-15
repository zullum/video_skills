"""Words and their start times from a whisper.cpp -ojf -ml 1 JSON (one word per segment)."""
import json

from mx.beats import norm


def words(path, offset=0.0):
    out = []
    for seg in json.load(open(path))["transcription"]:
        w = norm(seg["text"])
        if w and not seg["text"].strip().startswith("["):
            out.append({"w": w, "t": round(offset + seg["offsets"]["from"] / 1000, 3)})
    return out
