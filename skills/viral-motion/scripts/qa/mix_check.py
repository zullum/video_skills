"""Predict the loudness of a HyperFrames render from its <audio> stems.

    python mix_check.py proof/index.html [--target -14] [--out mix_sim.wav]

Reproduces the renderer's audio path (hyperframes 0.8.141, engine audioMixer):
each <audio id> is cut to [data-media-start, +duration], mono is copied to both
channels, gain is data-volume or, when a data-automation volume lane exists,
the lane's absolute values linearly interpolated (data-volume is then ignored),
linear clip-edge fades are applied, the clip is delayed to data-start, and all
clips are summed at unity with no limiter. Then it measures the sum with ffmpeg
ebur128 and prints the trim that would put it on the target.
"""
import argparse
import html.parser
import json
import pathlib
import re
import subprocess

import numpy as np
import soundfile as sf

SR = 48000


class AudioTags(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "audio" and a.get("id") and a.get("src"):
            self.tags.append(a)


def decode(path, media_start, dur):
    """ffmpeg -> float32 stereo 48 kHz; mono becomes L=R=mono like the renderer."""
    cmd = ["ffmpeg", "-v", "error", "-ss", str(media_start)]
    cmd += ["-t", str(dur)] if dur else []
    cmd += ["-i", str(path), "-af", "pan=stereo|c0=c0|c1=c1" if channels(path) > 1 else "pan=stereo|c0=c0|c1=c0",
            "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def channels(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                          "stream=channels", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return int(out.stdout.strip() or 2)


def gain_curve(tag, n):
    t = np.arange(n) / SR
    lane = None
    if tag.get("data-automation"):
        lanes = json.loads(tag["data-automation"]).get("lanes", [])
        lane = next((l for l in lanes if l.get("target") == "volume"), None)
    if lane and lane["points"]:
        pts = lane["points"]
        g = np.interp(t, [p["t"] for p in pts], [p["v"] for p in pts])
    else:
        g = np.full(n, float(tag.get("data-volume", 1)))
    fi, fo, dur = float(tag.get("data-fade-in", 0)), float(tag.get("data-fade-out", 0)), n / SR
    if fi > 0:
        g *= np.clip(t / fi, 0, 1)
    if fo > 0:
        g *= np.clip((dur - t) / fo, 0, 1)
    return np.clip(g, 0, 3.98)[:, None]


def simulate(index_html):
    base = pathlib.Path(index_html).parent
    parser = AudioTags()
    parser.feed(pathlib.Path(index_html).read_text())
    root = re.search(r'data-composition-id="[^"]+"[^>]*data-duration="([\d.]+)"', pathlib.Path(index_html).read_text())
    total = float(root.group(1))
    mix = np.zeros((int(round(total * SR)), 2))
    for tag in parser.tags:
        start = float(tag.get("data-start", 0))
        dur = float(tag["data-duration"]) if tag.get("data-duration") else None
        x = decode(base / tag["src"], float(tag.get("data-media-start", 0)), dur)
        x = x * gain_curve(tag, len(x))
        s = int(round(start * SR))
        end = min(len(mix), s + len(x))
        mix[s:end] += x[: end - s]
    return mix, parser.tags


def ebur128(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                          "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    pick = lambda key: float(re.search(rf"{key}:\s+(-?[\d.]+|-inf)", summary).group(1))
    return {"I": pick("I"), "LRA": pick("LRA"), "TP": pick("Peak")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("index_html")
    ap.add_argument("--target", type=float, default=-14.0)
    ap.add_argument("--ceiling", type=float, default=-1.0, help="max true peak, dBTP")
    ap.add_argument("--window", type=float, default=1.0, help="allowed LU off target")
    ap.add_argument("--out", default="mix_sim.wav")
    args = ap.parse_args()
    mix, tags = simulate(args.index_html)
    sf.write(args.out, mix.astype(np.float32), SR, subtype="FLOAT")
    m = ebur128(args.out)
    trim = min(args.target - m["I"], args.ceiling - m["TP"])  # never trim past the ceiling
    final_i = m["I"] + trim
    ok = abs(final_i - args.target) <= args.window
    print(f"stems: {', '.join(t['id'] for t in tags)}")
    print(f"mix: I={m['I']:.1f} LUFS  TP={m['TP']:.1f} dBTP  LRA={m['LRA']:.1f} LU")
    print(f"trim {trim:+.1f} dB on every stem -> I={final_i:.1f}, TP={m['TP'] + trim:.1f}: "
          + ("PASS" if ok else "FAIL (peaks block the target: lower the hottest stem or pre-mix with a limiter)"))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
