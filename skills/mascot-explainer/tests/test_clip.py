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


NAVY = (35, 48, 90)


def shorts_image():
    im = Image.new("RGB", (240, 240), BG); d = ImageDraw.Draw(im)
    d.rectangle([40, 60, 200, 180], fill=NAVY, outline=(20, 20, 24), width=8)
    return np.array(im)


def navy_palette():
    p = Image.new("P", (1, 1)); p.putpalette([18, 18, 22, 255, 255, 255, *BG, *NAVY] + [0] * 756)
    return p


def test_a_kept_dark_fill_is_not_ink(tmp_path):
    out = tmp_path / "s.svg"; trace2.trace(shorts_image(), navy_palette(), BG, str(out), clip=True, ink_keep=[NAVY])
    assert "#23305A" in out.read_text().upper()          # the navy survives as a fill


def test_default_still_inks_dark_colours(tmp_path):
    out = tmp_path / "d.svg"; trace2.trace(shorts_image(), navy_palette(), BG, str(out), clip=True)
    assert "#23305A" not in out.read_text().upper()


def test_ink_and_fill_agree_near_the_threshold(tmp_path):
    im = Image.new("RGB", (240, 240), BG); d = ImageDraw.Draw(im)
    d.rectangle([40, 60, 200, 180], fill=(40, 53, 88), outline=(20, 20, 24), width=8)   # sat 48, like the sheet's navy
    a = np.array(im).astype(int)
    noise = np.random.default_rng(1).integers(-9, 10, a.shape[:2])     # generated sheets are not perfectly flat
    a[70:170, 50:190, 0] += noise[70:170, 50:190]
    p = Image.new("P", (1, 1)); p.putpalette([18, 18, 22, 255, 255, 255, *BG, 40, 53, 88] + [0] * 756)
    out = tmp_path / "n.svg"; trace2.trace(np.clip(a, 0, 255).astype("uint8"), p, BG, str(out), clip=True, ink_keep=[(40, 53, 88)])
    ink = out.read_text().split('fill="#141418"')[1]
    assert ink.count("M") <= 3                                # only the outline (outer + inner edge), no speckles


def test_thin_lines_on_skin_stay_ink(tmp_path):
    im = Image.new("RGB", (240, 240), BG); d = ImageDraw.Draw(im)
    d.rectangle([30, 30, 210, 210], fill=(255, 122, 89), outline=(20, 20, 24), width=8)
    for x in (80, 120, 160):
        d.line([x, 60, x, 180], fill=(20, 20, 24), width=3)            # muscle lines
    im = im.resize((480, 480), Image.BICUBIC).resize((240, 240), Image.BICUBIC)  # anti-aliased like a real sheet
    out = tmp_path / "m.svg"; trace2.trace(np.array(im), palette(), BG, str(out), clip=True, ink_keep=[NAVY])
    ink = out.read_text().split('fill="#141418"')[1]
    assert ink.count("M") >= 5                                         # outline (2) + the three lines
