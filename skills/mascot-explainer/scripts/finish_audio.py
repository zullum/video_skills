"""Put the project's simulated mix into a rendered MP4 and check the delivery gate.
  scripts/py scripts/finish_audio.py RENDER.mp4 MIX.wav OUT.mp4
MIX.wav is mix_check.py's --out (the renderer's own mix, rebuilt from the <audio> tags). HyperFrames 0.8.141 in normal
(non-debug) mode can add short glitches to the AAC track and then lower the whole track to keep them under -1 dBTP
("Audio lowered by 4.0 dB" in the render log). The video stream is copied untouched; the audio is encoded from the
clean mix. Exit 1 when the result misses -14 LUFS +-1 or a -1 dBTP true peak."""
import re
import subprocess
import sys


def loudness(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    pick = lambda key: float(re.search(rf"{key}:\s+(-?[\d.]+|-inf)", summary).group(1).replace("-inf", "-99"))
    return pick("I"), pick("Peak")


def main(render, mix, out):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", render, "-i", mix, "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", out],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + r.stderr[-800:])
    i, tp = loudness(out)
    ok = -15.0 <= i <= -13.0 and tp <= -1.0
    print(f"{out}: I={i:.1f} LUFS  TP={tp:.1f} dBTP  {'PASS' if ok else 'FAIL (gate -14 LUFS +-1, TP <= -1)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
