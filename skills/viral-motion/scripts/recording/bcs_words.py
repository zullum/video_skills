"""Word helpers for Bosnian/Croatian/Serbian (Latin) and English, stdlib only.

Feeds audiolib.align, whose own norm_word is English-only (it drops č/ć/š/ž/đ).
"""
import re
import unicodedata

_FOLD = {"đ": "dj", "ð": "dj", "č": "c", "ć": "c", "š": "s", "ž": "z", "ß": "ss"}
_CYR = dict(zip("абвгдђежзијклљмнњопрстћуфхцчџш",
                ["a", "b", "v", "g", "d", "dj", "e", "z", "z", "i", "j", "k", "l", "lj", "m", "n", "nj",
                 "o", "p", "r", "s", "t", "c", "u", "f", "h", "c", "c", "dz", "s"]))
# coarse sound key: voicing pairs and soft/hard affricates collapse (Svaka~Zvaka, Ćevapi~Čevapi),
# ijekavian/ekavian (vjetar~vetar), lj/nj~l/n.
_SOUNDS = [("dj", "c"), ("dz", "c"), ("lj", "l"), ("nj", "n"), ("ije", "e"), ("je", "e"), ("ph", "f"),
           ("th", "t"), ("ck", "k"), ("qu", "kv"), ("w", "v"), ("x", "ks"), ("y", "i"), ("z", "s"),
           ("d", "t"), ("b", "p"), ("g", "k"), ("v", "f"), ("h", "")]


def fold(word):
    """Lowercase ASCII key: diacritics and Serbian Cyrillic folded, punctuation dropped."""
    w = word.lower()
    w = "".join(_CYR.get(ch, _FOLD.get(ch, ch)) for ch in w)
    w = unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9']", "", w).strip("'")


def syllables(word):
    """Vowel groups + syllabic r (prst, vrt, Hrvatska). BCS-exact; English over-counts
    silent final e by one, which only nudges time splits inside merged words."""
    w = fold(word).replace("'", "")
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    n += len(re.findall(r"(?:^|[^aeiouy])r(?=[^aeiouy]|$)", w)) if len(w) > 1 else 0
    return max(1, n)


def phonetic(word):
    w = fold(word).replace("'", "")
    for a, b in _SOUNDS:
        w = w.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", w)


def _lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similarity(a, b):
    """0..1: best of spelling similarity (folded) and sound-key similarity."""
    fa, fb = fold(a), fold(b)
    if not fa or not fb:
        return 0.0
    if fa == fb:
        return 1.0
    pa, pb = phonetic(a), phonetic(b)
    s1 = 1 - _lev(fa, fb) / max(len(fa), len(fb))
    s2 = 1 - _lev(pa, pb) / max(len(pa), len(pb), 1)
    return max(0.0, s1, s2)


def script_words(text):
    """Approved script -> [{text, norm, line}]; one non-empty line = one script line."""
    words, line = [], -1
    for raw in text.splitlines():
        toks = [t for t in raw.split() if fold(t)]
        if not toks:
            continue
        line += 1
        words += [{"text": t, "norm": fold(t), "line": line} for t in toks]
    return words
