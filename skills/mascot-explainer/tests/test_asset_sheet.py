import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from mx import sheet

SKILL = Path(__file__).parents[1]
G = (0, 177, 64); ORANGE = (255, 122, 89); INK = (20, 20, 24)


def make_sheet(path, centers=((150, 150), (450, 150), (750, 150)), size=(900, 300)):
    im = Image.new("RGB", size, G); d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate(centers):
        d.ellipse([x - 90, y - 90, x + 90, y + 90], fill=ORANGE, outline=INK, width=8)
        if i == 1:
            d.ellipse([x - 30, y - 30, x + 30, y + 30], fill=G, outline=INK, width=8)
    im.save(path)
    return path


def run(sheet_png, project, names, *extra):
    return subprocess.run([sys.executable, "scripts/asset_sheet.py", str(sheet_png), str(project), "--names", names, *extra],
                          capture_output=True, text=True, cwd=SKILL)


def test_reading_order_across_rows(tmp_path):
    png = make_sheet(tmp_path / "rows.png", ((600, 120), (100, 120), (300, 420)), (900, 560))
    a = np.array(Image.open(png)).astype(int)
    boxes = sheet.find_assets(sheet.mask(a, sheet.background(a)))
    assert [round((b[0] + b[2]) / 2, -2) for b in boxes] == [100, 600, 300]


def test_writes_svgs_manifest_anchor_and_hole(tmp_path):
    r = run(make_sheet(tmp_path / "s.png"), tmp_path, "a,b,c")
    assert r.returncode == 0, r.stderr
    m = json.load(open(tmp_path / "assets" / "manifest.json"))["assets"]
    assert set(m) == {"a", "b", "c"} and (tmp_path / "assets" / "svg" / "b.svg").exists()
    assert m["a"]["file"] == "assets/svg/a.svg"
    assert 0.9 < m["a"]["anchor"][1] < 1.0 and abs(m["a"]["anchor"][0] - 0.5) < 0.05   # feet = bottom of the ink
    assert m["b"]["holes"] and abs(m["b"]["holes"][0][0] + m["b"]["holes"][0][2] / 2 - 0.5) < 0.05
    assert m["a"]["holes"] == []
    assert 'clip-path="url(#fig)"' in (tmp_path / "assets" / "svg" / "a.svg").read_text()


def test_name_count_mismatch_writes_nothing(tmp_path):
    r = run(make_sheet(tmp_path / "s.png"), tmp_path, "a,b")
    assert r.returncode != 0 and "found 3 assets, --names has 2" in r.stderr
    assert not (tmp_path / "assets").exists()


def test_grid_mode_and_per_name_anchor(tmp_path):
    r = run(make_sheet(tmp_path / "s.png"), tmp_path, "a,b,c", "--grid", "3x1", "--anchor", "b=center")
    assert r.returncode == 0, r.stderr
    m = json.load(open(tmp_path / "assets" / "manifest.json"))["assets"]
    assert m["b"]["anchor"] == [0.5, 0.5] and m["a"]["anchor"][1] > 0.9
