"""Narration timing.   scripts/py scripts/timing.py PROJECT [--lead 0.2] [--tail 0.3] [--no-voice] [--recording FILE]
Every shot with "say" gets a Kokoro line (cached by text, voice and speed), normalized to a stereo 48 kHz WAV in
assets/audio/narration/<id>.wav, and whisper word times. With --recording (recording.json from viral-motion's
recording pipeline, the user's own voice) line i of the recording is the i-th shot with "say". Shots without
"say" need "dur". Writes audio/timing.json; word times are local to the shot (lead included)."""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import deps
from mx import whisper
from mx.beats import norm

# The voice leads an explainer (the music is ducked under it nearly all the time), so it carries the mix's
# loudness: -13.5 LUFS. Kokoro speech peaks ~13 dB above its loudness; a broadcast-style limiter brings that to
# ~8 dB, so every line lands at -13.5 with its peaks near -6 dBFS and the mix passes -14 LUFS / -1 dBTP.
CHAIN = ("pan=stereo|c0=c0|c1=c0,acompressor=threshold=0.05:ratio=4:attack=2:release=80:makeup=3,"
         "alimiter=limit=0.3:attack=1:release=40:level=disabled,loudnorm=I=-13.5:TP=-3:LRA=11")


def layout(shots, speech, words, lead=0.2, tail=0.3, silent=False):
    out, start = [], 0.0
    for s in shots:
        sid = s["id"]
        if s.get("say") and not silent:
            dur = max(lead + speech[sid] + tail + s.get("hold", 0), s.get("dur", 0))
            row = {"lead": lead, "speech": speech[sid], "voice": f"assets/audio/narration/{sid}.wav",
                   "words": [{"w": w["w"], "t": round(lead + w["t"], 3)} for w in words.get(sid, [])]}
        elif "dur" in s:
            dur, row = float(s["dur"]), {"lead": 0.0, "speech": 0.0, "voice": None, "words": []}
        else:
            raise SystemExit(f'{sid}: no "say" and no "dur"')
        dur = round(dur, 3)
        out.append(dict(id=sid, start=round(start, 3), dur=dur, **row))
        start += dur
    return {"duration": round(start, 3), "shots": out}


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed ({r.returncode}): {' '.join(cmd[:4])} ...\n{r.stderr[-800:]}")
    return r.stdout


def _paths(P, sid):
    nar = os.path.join(P, "audio", "narration")
    os.makedirs(nar, exist_ok=True)
    os.makedirs(os.path.join(P, "assets", "audio", "narration"), exist_ok=True)
    return nar, os.path.join(P, "assets", "audio", "narration", f"{sid}.wav")


def cache_key(text, voice, speed):
    return hashlib.sha1(f"{text}|{voice}|{speed}|{CHAIN}".encode()).hexdigest()


def from_kokoro(P, shot, voice, speed, vm):
    sid, text = shot["id"], shot["say"]
    nar, dst = _paths(P, sid)
    cache, key = os.path.join(nar, f"{sid}.json"), cache_key(text, voice, speed)
    if os.path.exists(cache) and os.path.exists(dst):
        c = json.load(open(cache))
        if c["key"] == key:
            print(f"cached {sid}")
            return c["speech"], c["words"]
    raw, w16, prefix = (os.path.join(nar, f"{sid}{x}") for x in (".raw.wav", ".16k.wav", ".w"))
    info = json.loads(_run([os.path.join(vm, "scripts", "hf"), "tts", text, "-v", voice, "-s", str(speed),
                            "-o", raw, "--json"]).strip().splitlines()[-1])
    _run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", CHAIN, "-ar", "48000", "-c:a", "pcm_s24le", dst])
    _run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-ar", "16000", "-ac", "1", w16])
    _run(["bash", os.path.join(vm, "scripts", "recording", "run_whisper.sh"), "turbo", w16, prefix,
          "-l", "en", "--prompt", text])
    sp, ws = float(info["durationSeconds"]), whisper.words(prefix + ".json")
    json.dump({"key": key, "speech": sp, "words": ws}, open(cache, "w"), indent=1)
    print(f"{sid}: {sp:.2f} s, {len(ws)} words")
    return sp, ws


def from_recording(P, shot, line, rec_path):
    sid = shot["id"]
    if line.get("missing"):
        sys.exit(f"{sid}: its line was not found in the recording: {line['text']!r}")
    _, dst = _paths(P, sid)
    a, b = float(line["start"]), float(line["end"])
    clean = os.path.join(os.path.dirname(os.path.abspath(rec_path)), "clean.wav")
    _run(["ffmpeg", "-v", "error", "-y", "-i", clean, "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
          "-ar", "48000", "-c:a", "pcm_s24le", dst])
    ws = [{"w": norm(w["text"]), "t": round(float(w["start"]) - a, 3)} for w in line["words"] if norm(w["text"])]
    return round(b - a, 3), ws


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--lead", type=float, default=0.2)
    ap.add_argument("--tail", type=float, default=0.3); ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--recording")
    A = ap.parse_args(argv)
    P = A.project
    spec = json.load(open(os.path.join(P, "shots.json")))
    shots, speech, words = spec["shots"], {}, {}
    if not A.no_voice:
        said = [s for s in shots if s.get("say")]
        rec = json.load(open(A.recording)) if A.recording else None
        if rec and len(rec["lines"]) < len(said):
            sys.exit(f"the recording has {len(rec['lines'])} lines, shots.json {len(said)} spoken shots")
        vm = None if rec else deps.locate("vm")
        for k, s in enumerate(said):
            speech[s["id"]], words[s["id"]] = (from_recording(P, s, rec["lines"][k], A.recording) if rec else
                                               from_kokoro(P, s, spec.get("voice", "af_heart"),
                                                           float(spec.get("speed", 1.0)), vm))
    t = layout(shots, speech, words, A.lead, A.tail, silent=A.no_voice)
    os.makedirs(os.path.join(P, "audio"), exist_ok=True)
    json.dump(t, open(os.path.join(P, "audio", "timing.json"), "w"), indent=1)
    print(f"{len(shots)} shots, {t['duration']:.2f} s -> audio/timing.json")


if __name__ == "__main__":
    main()
