import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).parents[1]


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True)


def make(tmp_path, tone_db):
    ff("-f", "lavfi", "-i", "color=c=black:s=320x180:d=3", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
       "-t", "3", "-c:v", "libx264", "-c:a", "aac", "-shortest", tmp_path / "in.mp4")
    ff("-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration=3,volume={tone_db}dB,pan=stereo|c0=c0|c1=c0",
       tmp_path / "mix.wav")


def run(tmp_path):
    return subprocess.run([sys.executable, "scripts/finish_audio.py", str(tmp_path / "in.mp4"), str(tmp_path / "mix.wav"),
                           str(tmp_path / "out.mp4")], capture_output=True, text=True, cwd=SKILL)


def test_puts_the_mix_in_and_passes_the_gate(tmp_path):
    make(tmp_path, 4)                         # ffmpeg sine is 1/8 full scale; +4 dB in stereo lands near -14.8 LUFS
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout and (tmp_path / "out.mp4").exists()


def test_fails_when_the_mix_misses_the_gate(tmp_path):
    make(tmp_path, -6)
    r = run(tmp_path)
    assert r.returncode == 1 and "FAIL" in r.stdout
