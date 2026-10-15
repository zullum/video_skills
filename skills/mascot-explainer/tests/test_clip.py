import importlib
import sys

import numpy as np
from PIL import Image, ImageDraw

import deps

sys.path.insert(0, deps.locate("sv") + "/scripts")
trace2 = importlib.import_module("trace2")
BG = (0, 177, 64)


def ring_image():
    im = Image.new("RGB", (240, 240), BG); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 220, 220], fill=(255, 122, 89), outline=(20, 20, 24), width=8)
    d.ellipse([90, 90, 150, 150], fill=BG, outline=(20, 20, 24), width=8)   # a hole
    return np.array(im)


def palette():
    p = Image.new("P", (1, 1)); p.putpalette([18, 18, 22, 255, 255, 255, *BG, 255, 122, 89] + [0] * 756)
    return p


def test_clip_wraps_fills_and_keeps_the_hole(tmp_path):
    out = tmp_path / "a.svg"; trace2.trace(ring_image(), palette(), BG, str(out), clip=True)
    s = out.read_text()
    assert '<clipPath id="fig">' in s and 'clip-path="url(#fig)"' in s
    clip = s[s.index('<clipPath'):s.index('</clipPath>')]
    assert clip.count("M") >= 2                       # outer outline + the hole


def test_default_has_no_clip(tmp_path):
    out = tmp_path / "b.svg"; trace2.trace(ring_image(), palette(), BG, str(out))
    assert "clipPath" not in out.read_text()
