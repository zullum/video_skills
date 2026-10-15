"""A/V sync of a render against the simulated mix, by cross-correlation (works when av_check's onset matcher can't:
a dense Score and a Recording hide quiet cues).

  python sync_check.py <video.mp4> <mix_sim.wav> --at 6.3 15.0 22.8     # mix_sim.wav from mix_check.py --out

For each time, takes +-0.6 s of the simulated mix and finds the shift (ms) at which it best matches the MP4's audio.
0 ms = the renderer placed every <audio> where the HTML says. More than 1 frame (33 ms) is out of sync.
"""
import argparse
import subprocess
import sys

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("sim"); ap.add_argument("--at", type=float, nargs="+", required=True)
a = ap.parse_args()
SR = 16000


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


r, m = load(a.video), load(a.sim)
ok = True
for t in a.at:
    lo, hi, pad = int((t - 0.6) * SR), int((t + 0.6) * SR), 3200
    x = m[lo:hi]
    if lo < pad or len(x) < 1000 or float(np.abs(x).max()) < 1e-4:
        print(f"{t:.3f}s: nothing to correlate"); continue
    c = np.correlate(r[lo - pad:hi + pad], x, mode="valid")
    ms = (int(np.argmax(c)) - pad) / SR * 1000
    bad = abs(ms) > 33
    ok &= not bad
    print(f"{t:.3f}s: offset {ms:+.0f} ms {'OUT OF SYNC' if bad else 'ok'}")
sys.exit(0 if ok else 1)
