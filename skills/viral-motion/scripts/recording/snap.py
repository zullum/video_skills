"""Snap aligned word times to real pauses found in the energy envelope.

Whisper's DTW onsets land 0-300 ms late and its words run on until the next onset, so
lines seem to start late and end inside the following pause. Pauses (>= 150 ms of
envelope below threshold) are where Shots are cut and the envelope finds them to ~10-40 ms:
  1. each pause's END (the speech onset after it) moves the nearest word START within
     `reach` onto it;
  2. a word whose span contains the START of a pause is cut there (the word ended).
Words not next to a pause keep whisper's times.
"""
from bcs_words import syllables


def _heard(w):
    return w.get("src", "exact") in ("exact", "fuzzy", "subst")


def snap_words(words, gaps, reach=0.25):
    """words: [{start, end}] in order (mutated + returned); gaps: [(start, end)] pauses."""
    used = set()
    for g0, g1 in gaps:
        cands = [(abs(w["start"] - g1), k) for k, w in enumerate(words)
                 if k not in used and w["start"] > g0 - 0.1 and _heard(w)]
        if cands:
            d, k = min(cands)
            if d <= reach:
                words[k]["start"] = g1
                used.add(k)
    for w in words:
        for g0, _ in gaps:
            if w["start"] < g0 < w["end"]:
                w["end"] = g0
                break
    _unheard_into_speech(words, gaps)
    _monotonic(words)
    return words


def _unheard_into_speech(words, gaps):
    """An unheard word left inside a pause (whisper dropped a short line-initial word such
    as "A" and folded it into the next one) takes a syllable share of the next heard word."""
    for k, w in enumerate(words):
        if _heard(w) or (k and not _heard(words[k - 1])):
            continue
        g = next((g for g in gaps if g[0] <= w["start"] <= g[1] + 0.1), None)
        j = next((j for j in range(k + 1, len(words)) if _heard(words[j])), None)
        if g is None or j is None or j - k > 2 or words[j]["start"] > g[1] + 0.05:
            continue  # only 1-2 dropped words; a longer unheard run is a skipped line
        t0, t1 = g[1], words[j]["end"]
        syl = [syllables(words[i]["text"]) for i in range(k, j + 1)]
        acc = t0
        for i, sy in zip(range(k, j + 1), syl):
            words[i]["start"], words[i]["end"] = round(acc, 3), round(acc + (t1 - t0) * sy / sum(syl), 3)
            acc = words[i]["end"]


def _monotonic(words, min_dur=0.04):
    """Keep start < end and no overlap after snapping."""
    for k, w in enumerate(words):
        if k and w["start"] < words[k - 1]["start"] + min_dur:      # never invert word order
            w["start"] = round(words[k - 1]["start"] + min_dur, 3)
        if k and w["start"] < words[k - 1]["end"]:
            words[k - 1]["end"] = max(words[k - 1]["start"] + min_dur, w["start"])
        if w["end"] < w["start"] + min_dur:
            w["end"] = round(w["start"] + min_dur, 3)
