"""Up to 24 small items from one image call.   scripts/py scripts/item_sheet.py PROJECT [--dry]
Reads the "items" of PROJECT/assets.json (the asset plan, references/asset-plan.md): [{"name", "what", "anchor"?}].
Every 24 items become one sheet (gen/items.png, gen/items-2.png ...) at 4K, low quality (~$0.011 for the whole sheet
through gen_asset.py). The prompt asks for a grid with few empty cells (8 -> 4x2, 12 -> 4x3, 24 -> 6x4), but the
model lays out N things in its own rows, so asset_sheet.py cuts them by shape, in reading order, into one SVG per
item with a centred anchor ("anchor": "feet" for things that stand). --dry prints the prompts and the cost and calls nothing.
A sheet whose item count comes out wrong stops in asset_sheet.py: delete gen/items*.png and run again."""
import argparse
import json
import os

import asset_sheet
import gen_asset

DARK = "#3C3C44"                                      # black things are filled with this, never black: the outline stays
STYLE_BLOCK = ("Flat vector cartoon in a clean explainer style. Thick, even black outlines (#141418), the same line "
               "weight everywhere. Flat fills with at most one darker shade. No gradients, no textures, no glow, no "
               "shadows, no floor, no text, no frame. The background is one solid flat colour {chroma} everywhere.")


def grid(n):
    """Columns and rows for n items on a 16:9 sheet: fewest empty cells, then cells closest to square (c/r ~ 16:9)."""
    fits = [(c, r) for c in range(1, 7) for r in range(1, 5) if c * r >= n and c >= r]
    return min(fits, key=lambda g: (g[0] * g[1] - n) + abs(g[0] / g[1] - 16 / 9))


def chunks(items):
    return [items[i:i + 24] for i in range(0, len(items), 24)]


def prompt(items, style):
    c, r = grid(len(items))
    p = style.get("palette", {})
    colours = ", ".join(p[k] for k in ("accent", "panel", "bgLight", "skin") if k in p)
    lines = " ".join(f"{i}. {it['what']}." for i, it in enumerate(items, 1))
    return (f"{len(items)} separate small objects for the same cartoon world, in a {c} by {r} grid, one per cell, read "
            f"left to right and top to bottom, each centred in its cell, about two thirds of the cell in size, with "
            f"wide empty space around it, nothing touching or crossing into another cell"
            + (", the last cells left empty" if len(items) < c * r else "") + f": {lines} "
            f"Flat colours that fit this palette ({colours}, white, #141418), neutral greys and black where the object "
            f"needs them; black or dark objects are filled with dark grey {DARK}, never black, so the black outline stays "
            f"visible. Each object alone: no hands, no people, no labels. No grid lines. No numbers. No text. "
            + STYLE_BLOCK.format(chroma=style.get("chroma", "#00B140")))


def make(project, items, sheet="items", gen_cmd=None):
    """One sheet for up to 24 items -> assets/svg/<name>.svg each; returns the names."""
    style = json.load(open(os.path.join(project, "style.json")))
    out = f"gen/{sheet}.png"
    code = gen_asset.run(project, out, prompt(items, style), [], size="4K", aspect="16:9", gen_cmd=gen_cmd, kind="still")
    if code:
        raise SystemExit(f"{out}: the image call failed (exit {code})")
    names = [it["name"] for it in items]
    anchors = ",".join(f"{it['name']}={it.get('anchor', 'center')}" for it in items)
    keep = ",".join(dict.fromkeys([DARK] + [style.get("palette", {}).get("shorts", DARK)]))
    asset_sheet.main([os.path.join(project, out), project, "--names", ",".join(names), "--anchor", anchors,
                      "--ink-keep", keep])
    return names


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    plan = json.load(open(os.path.join(a.project, "assets.json")))
    sheets = chunks(plan.get("items", []))
    if not sheets:
        raise SystemExit("assets.json has no items")
    for k, part in enumerate(sheets):
        sheet = "items" if k == 0 else f"items-{k + 1}"
        if a.dry:
            style = json.load(open(os.path.join(a.project, "style.json")))
            print(f"gen/{sheet}.png: {len(part)} items, {'x'.join(map(str, grid(len(part))))}, "
                  f"~${gen_asset.FAL_PRICES['low']['4K']}\n{prompt(part, style)}\n")
        else:
            print(f"gen/{sheet}.png:", ", ".join(make(a.project, part, sheet)))


if __name__ == "__main__":
    main()
