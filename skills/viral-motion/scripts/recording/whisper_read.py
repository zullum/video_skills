"""Read whisper-cli -ml 1 -sow -ojf JSON into heard words [{text, start, end, p}].

mode "seg": word times = the -ml 1 segment offsets (whisper's timestamp-token heuristics).
mode "dtw": start = DTW time (t_dtw) of the word's first token + DTW_SHIFT; end = next word's
            start (max 1.2 s). Falls back to "seg" times if no t_dtw is present.
Bytes are decoded with surrogateescape, so a token holding half of a UTF-8 letter
(e.g. one byte of "č") survives and rejoins its other half.
"""
import json

SPECIAL = ("[_", "<|")
DTW_SHIFT = -0.12   # measured: DTW onsets after a pause are 120-170 ms late (median, 2 voices, 36 points)


def load(path):
    raw = open(path, "rb").read().decode("utf-8", "surrogateescape")
    return json.loads(raw)


def _fix(s):
    return s.encode("utf-8", "surrogateescape").decode("utf-8", "replace")


def heard_words(path, mode="seg"):
    data = load(path)
    words = []
    for seg in data.get("transcription", []):
        toks = [t for t in seg.get("tokens", []) if not t["text"].startswith(SPECIAL)]
        text = _fix("".join(t["text"] for t in toks)).strip()
        if not any(ch.isalnum() for ch in text):
            continue
        ps = [t.get("p", 0.0) for t in toks if t["text"].strip()]
        dtw = [t.get("t_dtw", -1) for t in toks if t.get("t_dtw", -1) is not None]
        words.append({"text": text, "start": seg["offsets"]["from"] / 1000,
                      "end": seg["offsets"]["to"] / 1000, "p": round(min(ps) if ps else 0.0, 3),
                      "p_mean": round(sum(ps) / len(ps), 3) if ps else 0.0,
                      "dtw": dtw[0] / 100 if dtw and dtw[0] >= 0 else None})
    if mode == "dtw" and all(w["dtw"] is not None for w in words):
        for k, w in enumerate(words):   # words run on until the next onset (pauses: snap.py)
            nxt = (words[k + 1]["dtw"] if k + 1 < len(words) else w["dtw"] + 1.2) + DTW_SHIFT
            w["start"] = max(0.0, w["dtw"] + DTW_SHIFT)
            w["end"] = max(w["start"] + 0.05, min(nxt, w["start"] + 1.2))
    return [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in w.items() if k != "dtw"}
            for w in words]


def transcript(path):
    return " ".join(_fix(s["text"]).strip() for s in load(path).get("transcription", []))


if __name__ == "__main__":
    import sys
    for w in heard_words(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "seg"):
        print(f"{w['start']:7.2f} {w['end']:7.2f}  p={w['p']:.2f}  {w['text']}")
