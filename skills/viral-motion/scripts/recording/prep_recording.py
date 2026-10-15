"""Recording intake + cleanup (ffmpeg does all processing; numpy only finds the trim points).

python prep_recording.py <input.m4a|mp3|wav|aiff|...> <outdir> [--no-denoise]
       [--pre 0.4] [--post 0.6] [--lufs -16] [--tp -1.5]
Writes: <outdir>/source.<ext> (untouched copy), clean.wav (48k stereo s24, the mix stem),
        whisper16k.wav (16k mono s16, derived FROM clean.wav so times match), prep.json.
"""
import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from audio_env import load_mono, speech_bounds

FF = ["ffmpeg", "-hide_banner", "-nostats", "-y"]


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def ebur128(path):
    """Integrated LUFS, LRA and true peak (dBTP) measured by ffmpeg's ebur128 filter."""
    err = run(FF + ["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    summ = err[err.rfind("Summary:"):]
    get = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", summ).group(1))
    return {"lufs": get("I"), "lra": get("LRA"), "tp": get("Peak")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("outdir")
    ap.add_argument("--no-denoise", action="store_true")
    ap.add_argument("--pre", type=float, default=0.4, help="silence kept before first speech")
    ap.add_argument("--post", type=float, default=0.6, help="silence kept after last speech")
    ap.add_argument("--lufs", type=float, default=-16.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    a = ap.parse_args()
    src, out = Path(a.input).resolve(), Path(a.outdir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    timing, t0 = {}, time.time()

    keep = out / ("source" + src.suffix.lower())
    if src.resolve() != keep.resolve():
        shutil.copy2(src, keep)                                   # original is never modified
    work = out / "work_mono48k.wav"
    run(FF + ["-i", str(keep), "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_f32le", str(work)])
    timing["decode"] = time.time() - t0

    t1 = time.time()
    x, sr = load_mono(work)
    b = speech_bounds(x, sr)
    dur_in = len(x) / sr
    start, end = max(0.0, b["start"] - a.pre), min(dur_in, b["end"] + a.post)
    before = ebur128(keep)
    timing["analyse"] = time.time() - t1

    t2 = time.time()
    nf = min(-20, max(-80, round(b["noise_db"])))
    chain = [f"atrim=start={start:.3f}:end={end:.3f}", "asetpts=PTS-STARTPTS", "highpass=f=80"]
    if not a.no_denoise:
        chain.append(f"afftdn=nr=10:nf={nf}:tn=1")
    # a soft compressor before loudnorm: at -16 LUFS the raw voice peaked at -1.5 dBFS (14.5 dB crest), so with the
    # Score and SFX underneath the mix gate failed on peaks (+0.7 dBTP). Compressed, the voice peaks near -5 dBFS.
    chain.append("acompressor=threshold=0.063:ratio=3:attack=5:release=120:makeup=2")
    chain += ["afade=t=in:d=0.05", f"afade=t=out:st={end - start - 0.15:.3f}:d=0.15",
              "pan=stereo|c0=c0|c1=c0"]                            # stereo BEFORE loudness
    pre = ",".join(chain)
    ln = f"loudnorm=I={a.lufs}:TP={a.tp}:LRA=11"
    err = run(FF + ["-i", str(work), "-af", f"{pre},{ln}:print_format=json", "-f", "null", "-"]).stderr
    m = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    ln2 = (f"{ln}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
           f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
    clean = out / "clean.wav"
    err = run(FF + ["-i", str(work), "-af", f"{pre},{ln2}", "-ar", "48000", "-c:a", "pcm_s24le",
                    str(clean)]).stderr
    m2 = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    timing["clean"] = time.time() - t2

    t3 = time.time()
    run(FF + ["-i", str(clean), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(out / "whisper16k.wav")])
    after = ebur128(clean)
    xc, _ = load_mono(clean)
    timing["export_measure"] = time.time() - t3
    work.unlink()

    info = {"source": str(keep), "clean_wav": str(clean), "whisper_wav": str(out / "whisper16k.wav"),
            "source_duration": round(dur_in, 3), "trim_start": round(start, 3), "trim_end": round(end, 3),
            "duration": round(len(xc) / sr, 3), "denoise": not a.no_denoise, "afftdn_nf": nf,
            "chain": f"{pre},{ln2.split(':print_format')[0]}",
            "loudnorm_type": m2.get("normalization_type"),
            "before": dict(before, noise_db=b["noise_db"]),
            "after": dict(after, noise_db=speech_bounds(xc, sr)["noise_db"]),
            "seconds": {k: round(v, 2) for k, v in timing.items()}}
    json.dump(info, open(out / "prep.json", "w"), indent=1)
    print(json.dumps({k: info[k] for k in ("trim_start", "trim_end", "duration", "loudnorm_type",
                                           "before", "after", "seconds")}))


if __name__ == "__main__":
    main()
