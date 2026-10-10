"""Script words -> times. ADAPTED from the music pipeline (SKILL/scripts/music):
  - audiolib.align (Needleman-Wunsch, 1:1 with substitutions) is IMPORTED; it only
    gets BCS-folded words (its own norm_word drops č/ć/š/ž/đ: "džem" -> "dem").
  - timing.py's fill rules (in-line interpolation, token-fill / onset-fill of unheard lines,
    "unsung" lines left out, end = next start or +1.2 s) are re-implemented here for speech.
  - timing.py step 3 (snap to the strongest vocal onset) is replaced by pause snapping (snap.py),
    which measured better on speech.
Word src: exact / fuzzy / subst (heard) | interp | token-fill | onset-fill | even-fill | missing.
"""
import sys
from pathlib import Path

sys.path.insert(1, str(Path(__file__).resolve().parents[1] / "music"))   # SKILL/scripts/music
import audiolib as A  # noqa: E402

import bcs_words  # noqa: E402

HEARD = ("exact", "fuzzy", "subst")


def _interp_inside_lines(flat, T, SRC):
    """timing.py step 1: unheard words between heard ones, by character share."""
    for li in sorted({f["line"] for f in flat}):
        idx = [k for k, f in enumerate(flat) if f["line"] == li]
        known = [k for k in idx if T[k] is not None]
        for k in (idx if known else []):
            if T[k] is not None:
                continue
            prev = max([q for q in known if q < k], default=None)
            nxt = min([q for q in known if q > k], default=None)
            if prev is not None and nxt is not None:
                span = sum(len(flat[q]["text"]) for q in range(prev, nxt))
                done = sum(len(flat[q]["text"]) for q in range(prev, k))
                T[k] = T[prev] + (T[nxt] - T[prev]) * done / max(span, 1)
            elif prev is not None:
                T[k] = T[prev] + 0.25 * (k - prev)
            else:
                T[k] = T[nxt] - 0.25 * (nxt - k)
            SRC[k] = "interp"


def _fill_unheard_lines(flat, T, SRC, heard, al, onsets, end):
    """timing.py step 2: a run of wholly unheard lines takes the recogniser's leftover tokens
    in its gap (token-fill), else the voiced phrases' onsets (onset-fill / even-fill), else
    stays missing (the speaker skipped it)."""
    on_t, on_s, phrases = onsets
    lines = sorted({f["line"] for f in flat})
    has = {li: any(T[k] is not None for k, f in enumerate(flat) if f["line"] == li) for li in lines}
    used = {j for j, _ in al if j is not None}
    n = 0
    while n < len(lines):
        if has[lines[n]]:
            n += 1
            continue
        run = [lines[n]]
        while n + len(run) < len(lines) and not has[lines[n + len(run)]]:
            run.append(lines[n + len(run)])
        ks = [k for k, f in enumerate(flat) if f["line"] in run]
        before = [T[k] for k in range(ks[0]) if T[k] is not None]
        after = [T[k] for k in range(ks[-1] + 1, len(flat)) if T[k] is not None]
        a = before[-1] + 0.15 if before else 0.0
        b = after[0] - 0.08 if after else end
        spare = [h for j, h in enumerate(heard) if j not in used and a <= h["start"] < b]
        if spare and not (not after and len(spare) < len(ks) // 2):
            for i, k in enumerate(ks):
                T[k], SRC[k] = spare[round(i * (len(spare) - 1) / max(len(ks) - 1, 1))]["start"], "token-fill"
        else:
            ph = [p for p in phrases if a - 0.05 <= p[0] < b]
            while len(ph) > len(run):
                g = [ph[i + 1][0] - ph[i][1] for i in range(len(ph) - 1)]
                i = g.index(min(g))
                ph[i:i + 2] = [(ph[i][0], ph[i + 1][1])]
            if ph and (after or len(ph) == len(run)):
                groups = [[k for k in ks if flat[k]["line"] == r] for r in run] if len(ph) == len(run) else [ks]
                spans = ph if len(ph) == len(run) else [(ph[0][0], ph[-1][1])]
                for grp, (p0, p1) in zip(groups, spans):
                    p0, p1 = max(a, p0), min(b, p1 + 0.2)
                    slot, last = (p1 - p0) / len(grp), p0 - 1.0
                    for i, k in enumerate(grp):
                        sel = [q for q, t in enumerate(on_t)
                               if p0 + slot * (i - 0.35) <= t < p0 + slot * (i + 0.65) and t > last + 0.06]
                        if sel:
                            q = max(sel, key=lambda q: on_s[q])
                            T[k], SRC[k] = float(on_t[q]), "onset-fill"
                        else:
                            T[k], SRC[k] = max(last + 0.08, p0 + slot * i), "even-fill"
                        last = T[k]
        n += len(run)


def align_times(known, heard, clean_wav16k, end):
    """known: [{text, line}]; heard: [{text, start, end, p_mean}] -> words with start/end/src/heard."""
    for h in heard:
        h["norm"] = bcs_words.fold(h["text"])
    al = A.align([bcs_words.fold(k["text"]) for k in known], heard)
    T = [heard[j]["start"] if j is not None else None for j, _ in al]
    SRC = [kind if j is not None else None for j, kind in al]
    _interp_inside_lines(known, T, SRC)
    _fill_unheard_lines(known, T, SRC, heard, al, A.vocal_onsets(clean_wav16k), end)
    words = []
    for k, w in enumerate(known):
        j = al[k][0]
        words.append(dict(w, start=T[k], end=None, src=SRC[k] or "missing",
                          heard=heard[j]["text"] if j is not None else "", p=heard[j]["p_mean"] if j is not None else 0.0))
    for li in sorted({w["line"] for w in words}):       # ends: next start in line; last: +1.2 / next line
        ws = [w for w in words if w["line"] == li and w["start"] is not None]
        for i in range(1, len(ws)):                      # timing.py: keep onsets >= 80 ms apart
            if ws[i]["start"] <= ws[i - 1]["start"] + 0.06:
                ws[i]["start"] = ws[i - 1]["start"] + 0.08
        nxt = min([w["start"] for w in words if w["line"] > li and w["start"] is not None], default=end)
        for i, w in enumerate(ws):
            w["end"] = ws[i + 1]["start"] if i + 1 < len(ws) else min(nxt, w["start"] + 1.2)
    return words, [h for j, h in enumerate(heard) if j not in {a for a, _ in al if a is not None}]
