"""whisper-cli -ojf JSON -> transcript.json ([{text, start, end}]), the word list timing.py and rank_takes.py read.

  python whisper_to_transcript.py whisper.json transcript.json [--lag 0.3]

stems.sh calls it. Each word starts at its DTW time (t_dtw, from whisper-cli -nfa --dtw), else at its token offset.
HyperFrames' transcript import reads token offsets only, which spread the words evenly across a segment ("City" at
0.03 s against a true 2.80 s). --lag subtracts whisper DTW's late bias on sung vocals (median about +0.3 s).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audiolib as A  # noqa: E402


def words_from_whisper(data):
    """Words from whisper.cpp -ojf tokens. A token without a leading space continues the previous word."""
    words = []
    for seg in data.get("transcription", []):
        seg_end = seg["offsets"]["to"] / 1000
        for tok in seg.get("tokens", []):
            text = tok.get("text", "")
            if text.strip().startswith("[_") or not text.strip():
                continue
            dtw = tok.get("t_dtw", -1)
            has_dtw = dtw is not None and dtw >= 0
            if words and not text.startswith(" "):
                words[-1]["text"] += text.strip()
                words[-1]["tok_end"] = tok["offsets"]["to"] / 1000
                continue
            words.append({"text": text.strip(), "start": dtw / 100 if has_dtw else tok["offsets"]["from"] / 1000,
                          "tok_end": tok["offsets"]["to"] / 1000, "dtw": has_dtw, "seg_end": seg_end})
    words = [w for w in words if A.norm_word(w["text"])]
    for k, w in enumerate(words):
        nxt = words[k + 1]["start"] if k + 1 < len(words) else w["seg_end"]
        w["end"] = min(nxt, w["start"] + 1.5) if w["dtw"] else w["tok_end"]
    return words


if __name__ == "__main__":
    args = sys.argv[1:]
    lag = float(args[args.index("--lag") + 1]) if "--lag" in args else 0.0
    words = words_from_whisper(json.load(open(args[0])))
    out = [{"text": w["text"], "start": round(max(0.0, w["start"] - lag), 3), "end": round(max(0.0, w["end"] - lag), 3)}
           for w in words]
    json.dump(out, open(args[1], "w"), indent=1)
    print(f"{len(out)} words -> {args[1]} (lag {lag})")
