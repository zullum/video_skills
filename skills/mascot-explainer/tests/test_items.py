"""Small items: the item sheet (one call for up to 24), hand-written SVG assets, and the generic "item" beat."""
import json
import sys
from pathlib import Path

import item_sheet
import svg_asset
from mx import beats, registry

SKILL = Path(__file__).parents[1]
STYLE = json.loads((SKILL / "tests" / "gallery" / "style.json").read_text())
# A fake image call: five discs in a 3x2 grid on the chroma, like a model's answer for five items.
FIVE = [sys.executable, "-c", "import sys; from PIL import Image, ImageDraw; im = Image.new('RGB', (1200, 800), (0, 177, 64)); "
        "d = ImageDraw.Draw(im); [d.ellipse([c * 400 + 120, r * 400 + 120, c * 400 + 280, r * 400 + 280], fill=(255, 122, 89), "
        "outline=(20, 20, 24), width=8) for r, c in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]]; im.save(sys.argv[1])"]


def items(n):
    return [{"name": f"thing{i}", "what": f"a small thing number {i}"} for i in range(n)]


def test_the_grid_fits_the_item_count():
    # the model fills the sheet with exactly N things in its own rows, so few empty cells and near-square cells
    assert [item_sheet.grid(n) for n in (1, 3, 4, 5, 6, 7, 8, 12, 13, 24)] == \
        [(1, 1), (3, 1), (2, 2), (3, 2), (3, 2), (4, 2), (4, 2), (4, 3), (5, 3), (6, 4)]
    assert [len(c) for c in item_sheet.chunks(items(30))] == [24, 6]


def test_the_prompt_numbers_every_item_on_the_chroma():
    p = item_sheet.prompt(items(5), STYLE)
    assert "3 by 2 grid" in p and "1. a small thing number 0" in p and "5. a small thing number 4" in p
    assert STYLE["chroma"] in p and "No text" in p and item_sheet.DARK in p        # dark things stay fills, not ink


def test_a_sheet_becomes_named_centred_svgs(tmp_path):
    (tmp_path / "style.json").write_text(json.dumps(STYLE))
    names = item_sheet.make(str(tmp_path), items(5), "items", gen_cmd=FIVE)
    m = json.load(open(tmp_path / "assets" / "manifest.json"))["assets"]
    assert names == [f"thing{i}" for i in range(5)] and set(m) == set(names)
    assert all(m[n]["anchor"] == [0.5, 0.5] for n in names) and (tmp_path / "assets" / "svg" / "thing4.svg").exists()
    call = json.load(open(tmp_path / "gen" / "budget.json"))["calls"][0]
    assert call["file"] == "gen/items.png" and call["size"] == "4K" and call["quality"] == "low"


def test_a_hand_written_svg_joins_the_manifest(tmp_path):
    src = tmp_path / "clock.svg"
    src.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120"><circle cx="100" cy="60" r="50"/></svg>')
    svg_asset.add(str(tmp_path), "clock", str(src))
    svg_asset.add(str(tmp_path), "stool", str(src), anchor="feet")
    m = json.load(open(tmp_path / "assets" / "manifest.json"))["assets"]
    assert m["clock"] == {"file": "assets/svg/clock.svg", "w": 200, "h": 120, "anchor": [0.5, 0.5], "holes": []}
    assert m["stool"]["anchor"] == [0.5, 1.0] and (tmp_path / "assets" / "svg" / "stool.svg").exists()


def test_the_item_beat_works_in_every_scene_and_sounds():
    assert "item" in registry.load(str(SKILL / "lib"))["generic"]
    pop = beats.events_for({"do": "item", "t": 1.0, "args": {"asset": "clock"}})
    fly = beats.events_for({"do": "item", "t": 1.0, "args": {"asset": "clock", "in": "fly"}})
    assert [e["kind"] for e in pop] == ["pop"] and [e["kind"] for e in fly] == ["whoosh"]
