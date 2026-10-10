"""Derive Shot boundaries from line timings (voice-led cutting).

Rule: a Shot starts `lead` s before its line's first word (the cut lands just ahead of the
voice) and ends where the next Shot starts; the first Shot starts at 0 and the last ends at
the end of the clean Recording. Shots longer than max_len are split at the best word gap
inside the line (longest pause, preferring punctuation, near the middle); Shots shorter than
min_len are merged into the next one. Both are reported in flags.
"""

PUNCT = ",;:.!?…–—"


def _cuts(lines, lead):
    """One cut per line: (time, [line ids], first word index or 0)."""
    return [{"t": max(0.0, ln["start"] - lead), "line_ids": [ln["i"]], "word": 0} for ln in lines]


def _best_split(line, t0, t1, lead, min_len):
    """Word index k (cut before word k) giving two parts >= min_len, or None."""
    ws, best, score = line["words"], None, float("-inf")
    for k in range(1, len(ws)):
        cut = ws[k]["start"] - lead
        if cut - t0 < min_len or t1 - cut < min_len:
            continue
        gap = ws[k]["start"] - ws[k - 1]["end"]
        s = gap + (0.3 if ws[k - 1]["text"][-1:] in PUNCT else 0.0) - 0.1 * abs(cut - (t0 + t1) / 2)
        if s > score:
            best, score = k, s
    return best


def derive_shots(lines, duration, lead=0.3, max_len=5.0, min_len=1.2):
    flags = []
    by_i = {ln["i"]: ln for ln in lines}
    cuts = _cuts(lines, lead)
    if cuts:
        cuts[0]["t"] = 0.0
    # split long Shots (repeat: a split half may still be too long)
    changed = True
    while changed:
        changed = False
        for n, c in enumerate(cuts):
            t1 = cuts[n + 1]["t"] if n + 1 < len(cuts) else duration
            if t1 - c["t"] <= max_len or len(c["line_ids"]) != 1:
                continue
            line = by_i[c["line_ids"][0]]
            k = _best_split(line, c["t"], t1, lead, min_len)
            if k is None or k <= c["word"]:
                if not c.get("flagged"):
                    flags.append(f"line {line['i']} needs a {t1 - c['t']:.1f}s Shot (> {max_len}s) and has no clean split")
                    c["flagged"] = True
                continue
            cut = {"t": round(line["words"][k]["start"] - lead, 3), "line_ids": [line["i"]], "word": k,
                   "note": f"split before '{line['words'][k]['text']}'"}
            cuts.insert(n + 1, cut)
            flags.append(f"line {line['i']} split into 2 Shots at '{line['words'][k]['text']}' ({cut['t']:.2f}s)")
            changed = True
            break
    # merge short Shots into the next one
    n = 0
    while n < len(cuts) - 1:
        if cuts[n + 1]["t"] - cuts[n]["t"] < min_len:
            gone = cuts.pop(n + 1)
            cuts[n]["line_ids"] = sorted(set(cuts[n]["line_ids"] + gone["line_ids"]))
            flags.append(f"lines {cuts[n]['line_ids']} merged into one Shot (< {min_len}s)")
        else:
            n += 1
    shots = []
    for n, c in enumerate(cuts):
        end = cuts[n + 1]["t"] if n + 1 < len(cuts) else duration
        shot = {"i": n, "start": round(c["t"], 3), "end": round(end, 3), "line_ids": c["line_ids"]}
        if c.get("note"):
            shot["note"] = c["note"]
        shots.append(shot)
    return shots, flags
