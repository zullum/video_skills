"""Map the approved script onto whisper's heard words; write recording.json.

python align_script.py --script script.txt --whisper whisper.json --prep prep.json --out recording.json
                       [--mode dtw|seg] [--no-snap] [--lead 0.3] [--max-shot 5.0] [--min-shot 1.2]
                       [--lang hr --detected en --detected-p 0.99]

Alignment = the music pipeline's aligner (script_align.py: audiolib.align + timing.py fill rules,
adapted to BCS spelling), then pause snapping (snap.py), then Shots (shots.py).
Exit 3 = hard fail (recording.json is still written): whisper is sure the Recording is in another language
than the script, or under 70% of the script words are heard clearly.
"""
import argparse
import json
from pathlib import Path

import bcs_words
from audio_env import envelope, levels, load_mono, silent_gaps
from script_align import HEARD, align_times
from shots import derive_shots
from snap import snap_words
from whisper_read import heard_words

CONF = {"interp": 0.3, "token-fill": 0.2, "onset-fill": 0.15, "even-fill": 0.1, "missing": 0.0}
HARD_FAIL = 0.7   # under this share of script words heard clearly, only a new Recording fixes it
BCS = {"hr", "bs", "sr", "sl", "mk"}   # whisper's language ID mixes these up on Bosnian/Croatian/Serbian


def wrong_language(lang, detected, p):
    """Whisper is sure (p >= 0.5) the Recording is not in the script's language. Needed because a forced
    -l en on BCS speech TRANSLATES it, and a faithful translation can pass the heard-share gate."""
    return bool(detected) and p >= 0.5 and detected not in (BCS if lang in BCS else {lang})


def align_words(script_text, whisper_json, prep, mode="dtw", snap=True):
    """Every spoken script word gets start/end, src, heard text and a confidence 0..1."""
    known = bcs_words.script_words(script_text)
    words, extra = align_times(known, heard_words(whisper_json, mode), prep["whisper_wav"], prep["duration"])
    for w in words:
        w["confidence"] = (round(bcs_words.similarity(w["text"], w["heard"]) * w["p"], 2)
                           if w["src"] in HEARD else CONF[w["src"]])
    if snap:
        x, sr = load_mono(prep["clean_wav"])
        db = envelope(x, sr)
        snap_words([w for w in words if w["start"] is not None], silent_gaps(db, levels(db)["thr_db"]))
    return words, extra


def to_lines(words, script_text):
    texts = [ln.strip() for ln in script_text.splitlines() if bcs_words.fold(ln)]
    lines = []
    for i, text in enumerate(texts):
        ws = [w for w in words if w["line"] == i]
        timed = [w for w in ws if w["start"] is not None]
        r = lambda t: None if t is None else round(t, 3)  # noqa: E731
        lines.append({"i": i, "text": text, "start": r(timed[0]["start"]) if timed else None,
                      "end": r(timed[-1]["end"]) if timed else None, "missing": not timed,
                      "words": [{"text": w["text"], "start": r(w["start"]), "end": r(w["end"]), "heard": w["heard"],
                                 "src": w["src"], "confidence": w["confidence"]} for w in ws]})
    return lines


def heard_share(lines):
    words = [w for ln in lines for w in ln["words"]]
    return sum(w["confidence"] >= 0.5 for w in words) / max(1, len(words))


def quality_flags(lines, extra):
    flags = [f"line {ln['i']} NOT FOUND in the Recording (skipped?): re-record it or drop it from the script"
             for ln in lines if ln["missing"]]
    good = heard_share(lines)
    if good < HARD_FAIL:
        flags.insert(0, f"ONLY {good:.0%} of script words heard clearly: wrong language (-l), different text, "
                        "music/noise, or a whisper loop. Check before cutting Shots.")
    flags += [f"line {ln['i']} '{w['text']}' {w['src']} (heard '{w['heard']}', conf {w['confidence']})"
              for ln in lines for w in ln["words"] if w["confidence"] < 0.35 and not ln["missing"]]
    flags += [f"unscripted speech '{h['text']}' at {h['start']:.2f}s (filler/ad-lib/retake?)" for h in extra]
    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--whisper", required=True, help="whisper-cli -ml 1 -sow -ojf JSON")
    ap.add_argument("--prep", required=True, help="prep.json from prep_recording.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="dtw", choices=["dtw", "seg"])
    ap.add_argument("--no-snap", action="store_true")
    ap.add_argument("--lead", type=float, default=0.3)
    ap.add_argument("--max-shot", type=float, default=5.0)
    ap.add_argument("--min-shot", type=float, default=1.2)
    ap.add_argument("--lang", default="", help="the script's language, as passed to whisper -l")
    ap.add_argument("--detected", default="", help="whisper -dl language of the Recording")
    ap.add_argument("--detected-p", type=float, default=0.0)
    a = ap.parse_args()
    script = open(a.script, encoding="utf-8").read()
    prep = json.load(open(a.prep))
    words, extra = align_words(script, a.whisper, prep, a.mode, not a.no_snap)
    lines = to_lines(words, script)
    shots, shot_flags = derive_shots([ln for ln in lines if not ln["missing"]], prep["duration"],
                                     a.lead, a.max_shot, a.min_shot)
    rec = {"source": prep["source"], "clean_wav": prep["clean_wav"], "duration": prep["duration"],
           "lufs": prep["after"]["lufs"], "tp": prep["after"]["tp"], "trim_start": prep["trim_start"],
           "timing": {"whisper": Path(a.whisper).name, "mode": a.mode, "snapped": not a.no_snap},
           "language": {"script": a.lang, "heard": a.detected, "p": a.detected_p},
           "heard_share": round(heard_share(lines), 2), "lines": lines, "shots": shots,
           "flags": quality_flags(lines, extra) + shot_flags}
    wrong = wrong_language(a.lang, a.detected, a.detected_p)
    if wrong:
        rec["flags"].insert(0, f"the Recording sounds like '{a.detected}' (p {a.detected_p:.2f}) but -l is '{a.lang}': "
                               "if the script is in that language, ask for a Recording in it; else rerun with the right -l")
    rec["hard_fail"] = wrong or rec["heard_share"] < HARD_FAIL
    json.dump(rec, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for ln in lines:
        span = "  missing  " if ln["missing"] else f"{ln['start']:5.2f}-{ln['end']:5.2f}"
        print(f"L{ln['i']} {span}  " + " ".join(
            f"{w['text']}@{w['start']:.2f}" + ("" if w["src"] == "exact" else "*")
            for w in ln["words"] if w["start"] is not None))
    for s in shots:
        print(f"Shot {s['i']}: {s['start']:5.2f}-{s['end']:5.2f} lines {s['line_ids']} {s.get('note', '')}")
    for f in rec["flags"]:
        print("FLAG", f)
    if rec["hard_fail"]:
        print("HARD FAIL: " + (rec["flags"][0] if wrong else
                               f"only {rec['heard_share']:.0%} of the script heard clearly (need {HARD_FAIL:.0%})"))
        raise SystemExit(3)


if __name__ == "__main__":
    main()
