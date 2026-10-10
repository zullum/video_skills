"""Energy-envelope helpers: speech bounds for trimming, pauses for snapping word times."""
import numpy as np
import soundfile as sf

HOP = 0.01   # 10 ms frames
WIN = 0.02   # 20 ms RMS window


def load_mono(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    return x.mean(axis=1), sr


def envelope(x, sr):
    """Frame levels in dBFS (RMS over WIN, every HOP). Frame k covers time k*HOP."""
    hop, win = int(HOP * sr), int(WIN * sr)
    pad = np.concatenate([x, np.zeros(win, np.float32)])
    n = max(1, (len(x)) // hop)
    idx = np.arange(n)[:, None] * hop + np.arange(win)[None, :]
    return 10 * np.log10(np.mean(pad[idx] ** 2, axis=1) + 1e-12)


def levels(db):
    """Noise floor (10th pct), speech level (95th pct) and a speech threshold between them."""
    noise, speech = float(np.percentile(db, 10)), float(np.percentile(db, 95))
    thr = noise + max(10.0, 0.25 * (speech - noise))
    return {"noise_db": round(noise, 1), "speech_db": round(speech, 1), "thr_db": round(thr, 1)}


def _runs(mask, min_frames):
    """Start/end frame indices of True runs at least min_frames long."""
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    keep = (ends - starts) >= min_frames
    return list(zip(starts[keep], ends[keep]))


def speech_bounds(x, sr):
    """First/last speech time: runs of >= 60 ms above threshold (ignores clicks)."""
    db = envelope(x, sr)
    lv = levels(db)
    runs = _runs(db > lv["thr_db"], 6)
    if not runs:
        return dict(lv, start=0.0, end=len(x) / sr)
    return dict(lv, start=runs[0][0] * HOP, end=runs[-1][1] * HOP + WIN)


def silent_gaps(db, thr, min_len=0.15):
    """Pauses: runs of >= min_len below thr, as (start, end) times (end = next speech onset)."""
    return [(round(a * HOP + WIN / 2, 3), round(b * HOP + WIN / 2, 3))
            for a, b in _runs(db <= thr, int(round(min_len / HOP)))]
