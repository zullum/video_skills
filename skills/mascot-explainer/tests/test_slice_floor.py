"""sprite-video slice.py --floor on a chroma-green sheet: the floor is found and the figure's ink survives."""
import json
import subprocess
import sys

from PIL import Image, ImageDraw

import deps

G, INK = (8, 166, 74), (20, 20, 24)


def test_floor_on_green_background(tmp_path):
    im = Image.new("RGB", (800, 400), G); d = ImageDraw.Draw(im)
    for c in range(2):
        x = c * 400
        d.rectangle([x + 140, 120, x + 260, 300], fill=(255, 122, 89), outline=INK, width=8)
        d.line([x + 30, 302, x + 370, 302], fill=INK, width=5)            # the floor line
    png = tmp_path / "s.png"; im.save(png)
    r = subprocess.run([sys.executable, deps.locate("sv") + "/scripts/slice.py", str(png), str(tmp_path / "f"),
                        "--cols", "2", "--rows", "1", "--floor", "--clip"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    fl = json.load(open(tmp_path / "f" / "frames.json"))["floor"]
    assert fl and 290 < fl[0] < 310 and fl[1] - fl[0] < 15
    assert 'fill="#141418"' in (tmp_path / "f" / "f00.svg").read_text()
