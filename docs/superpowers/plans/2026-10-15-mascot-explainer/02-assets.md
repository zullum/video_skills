# 02 Assets (Tasks 3-5)

All paths below are relative to `skills/mascot-explainer/`. Tests run with `scripts/py -m pytest tests -q`.

### Task 3: Budgeted Nano Banana wrapper

**Files:** Create `scripts/gen_asset.py`, `scripts/mx/__init__.py` (empty), `scripts/mx/manifest.py`;
Test `tests/test_gen_asset.py`

**Interfaces:**
- Consumes: `deps.locate("sv")` → `<sv>/scripts/gen.py` (args `OUT PROMPT [refs…]`, env `SIZE`, `ASPECT`).
- Produces: `gen_asset.run(project, out, prompt, refs, size="2K", aspect="16:9", gen_cmd=None) -> int`
  (0 ok/cached, 3 over budget, else gen.py's code); CLI `scripts/py scripts/gen_asset.py PROJECT OUT "prompt" [refs…]`
  with env `SIZE`, `ASPECT`. Ledger `PROJECT/gen/budget.json` = `{"limit": 1.5, "spent", "calls": [{"file","size","price","prompt"}]}`.
- Produces: `mx.manifest.load(project) -> {"assets": {}, "sprites": {}}`, `mx.manifest.save(project, m)`
  (`PROJECT/assets/manifest.json`, indent 1, keys sorted).

- [ ] **Step 1: Failing tests** `tests/test_gen_asset.py`

```python
import json, sys, gen_asset
WRITE = [sys.executable, "-c", "import sys; open(sys.argv[1], 'wb').write(b'png')"]
BOOM = [sys.executable, "-c", "import sys; sys.exit(7)"]

def spent(p): return json.load(open(p / "gen" / "budget.json"))["spent"]

def test_call_is_recorded(tmp_path):
    assert gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=WRITE) == 0
    assert spent(tmp_path) == 0.101

def test_existing_output_is_never_paid_twice(tmp_path):
    (tmp_path / "a.png").write_bytes(b"old")
    assert gen_asset.run(str(tmp_path), str(tmp_path / "a.png"), "x", [], gen_cmd=BOOM) == 0
    assert not (tmp_path / "gen" / "budget.json").exists()

def test_refuses_past_the_limit(tmp_path):
    (tmp_path / "gen").mkdir()
    (tmp_path / "gen" / "budget.json").write_text('{"limit": 0.15, "spent": 0.101, "calls": []}')
    assert gen_asset.run(str(tmp_path), str(tmp_path / "b.png"), "x", [], gen_cmd=WRITE) == 3
    assert not (tmp_path / "b.png").exists()

def test_failed_call_costs_nothing(tmp_path):
    assert gen_asset.run(str(tmp_path), str(tmp_path / "c.png"), "x", [], gen_cmd=BOOM) == 7
    assert not (tmp_path / "gen" / "budget.json").exists()
```

- [ ] **Step 2: Run, expect FAIL** (`No module named 'gen_asset'`).
- [ ] **Step 3: Implement** `scripts/gen_asset.py`

```python
"""One budgeted Nano Banana call.   scripts/py scripts/gen_asset.py PROJECT OUT.png "prompt" [ref ...]
env SIZE=1K|2K|4K (default 2K), ASPECT (default 16:9). An existing OUT is reused (delete it to regenerate);
a call that would pass gen/budget.json "limit" is refused (exit 3). The key is never printed."""
import json, os, subprocess, sys
import deps
PRICES = {"1K": 0.067, "2K": 0.101, "4K": 0.151}

def _ledger(project):
    p = os.path.join(project, "gen", "budget.json")
    return p, (json.load(open(p)) if os.path.exists(p) else {"limit": 1.5, "spent": 0.0, "calls": []})

def run(project, out, prompt, refs, size="2K", aspect="16:9", gen_cmd=None):
    if os.path.exists(out):
        print(f"cached {out}"); return 0
    path, led = _ledger(project); price = PRICES[size]
    if led["spent"] + price > led["limit"] + 1e-9:
        print(f"budget: ${led['spent']:.3f} of ${led['limit']:.2f} spent, this call costs ${price:.3f}; "
              f"raise \"limit\" in {path} to go on", file=sys.stderr); return 3
    print(f"Nano Banana {size} {aspect}: ${price:.3f} (spent ${led['spent']:.3f} of ${led['limit']:.2f})")
    cmd = gen_cmd or [sys.executable, os.path.join(deps.locate("sv"), "scripts", "gen.py")]
    r = subprocess.run(cmd + [out, prompt] + list(refs), env=dict(os.environ, SIZE=size, ASPECT=aspect))
    if r.returncode or not os.path.exists(out):
        return r.returncode or 1
    led["spent"] = round(led["spent"] + price, 3)
    led["calls"].append({"file": os.path.relpath(out, project), "size": size, "price": price, "prompt": prompt[:160]})
    os.makedirs(os.path.dirname(path), exist_ok=True); json.dump(led, open(path, "w"), indent=1)
    return 0

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    sys.exit(run(a[0], a[1], a[2], a[3:], os.environ.get("SIZE", "2K"), os.environ.get("ASPECT", "16:9")))
```

`scripts/mx/manifest.py`: `load` returns the JSON with both keys defaulted; `save` makes `assets/` and writes.
- [ ] **Step 4: Run, expect PASS** (4 passed). **Step 5: Commit** `mascot-explainer: budgeted Nano Banana wrapper`.

### Task 4: asset_sheet.py (multi-asset sheet → one clipped SVG per asset)

**Files:** Create `scripts/asset_sheet.py` (CLI), `scripts/mx/sheet.py` (pure functions); Test `tests/test_asset_sheet.py`

**Interfaces:**
- Consumes: `trace2.trace(rgb, pal, bg, out, clip=True)` (Task 2), `mx.manifest` (Task 3).
- Produces: `mx.sheet.background(a) -> (r,g,b)` (median of the four 20×20 corners), `mx.sheet.mask(a, bg)`
  (`|a-bg|.sum(2) > 70`, opened once), `mx.sheet.find_assets(mask, grid=None, min_frac=0.002) -> [(x0,y0,x1,y1)]`
  in reading order, `mx.sheet.holes(mask_crop) -> [[x,y,w,h]]` (fractions, largest first, ≥0.5 % of the box, max 3),
  `mx.sheet.anchor(mask_crop, kind) -> [ax, ay]` (`feet`: x = mean x of the lowest 5 % of rows, y = 1.0;
  `center`: [0.5, 0.5]), `mx.sheet.palette(a, bg) -> PIL "P" image` (slice.py's: ink, white, bg + 14 median-cut).
- CLI: `scripts/py scripts/asset_sheet.py SHEET PROJECT --names a,b,c [--grid 3x3] [--anchor feet|center|a=center,…]`
  → `PROJECT/assets/svg/<name>.svg` + manifest `assets[name] = {"file": "assets/svg/<name>.svg", "w", "h", "anchor", "holes"}`.

Detection: with `--grid CxR` every non-empty cell (10 px margin) is one asset (all its pieces, e.g. a rocket and its
flame); without it, connected components of `binary_closing(mask, 3)` larger than `min_frac` of the sheet. Reading
order: sort by top y, start a new row when a top is more than half the median height below the row's first top,
then sort each row by x. If the count differs from `--names`, exit before writing anything with
`found N assets, --names has M (boxes: …); use --grid or fix the sheet`. Each crop gets 8 px padding, pixels of
other assets inside the crop are set to bg, and the crop is traced with `clip=True`.

- [ ] **Step 1: Failing tests** `tests/test_asset_sheet.py`

```python
import json, numpy as np, pytest, subprocess, sys
from PIL import Image, ImageDraw
from mx import sheet
G = (0, 177, 64); ORANGE = (255, 122, 89); INK = (20, 20, 24)

def make_sheet(path, centers=((150, 150), (450, 150), (750, 150)), size=(900, 300)):
    im = Image.new("RGB", size, G); d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate(centers):
        d.ellipse([x - 90, y - 90, x + 90, y + 90], fill=ORANGE, outline=INK, width=8)
        if i == 1: d.ellipse([x - 30, y - 30, x + 30, y + 30], fill=G, outline=INK, width=8)
    im.save(path); return path

def run(sheet_png, project, names, *extra):
    return subprocess.run([sys.executable, "scripts/asset_sheet.py", str(sheet_png), str(project), "--names", names, *extra],
                          capture_output=True, text=True)

def test_reading_order_across_rows():
    a = np.array(Image.open(make_sheet("/tmp/mx_rows.png", ((600, 120), (100, 120), (300, 420)), (900, 560)))).astype(int)
    boxes = sheet.find_assets(sheet.mask(a, sheet.background(a)))
    assert [round((b[0] + b[2]) / 2, -2) for b in boxes] == [100, 600, 300]

def test_writes_svgs_manifest_anchor_and_hole(tmp_path):
    r = run(make_sheet(tmp_path / "s.png"), tmp_path, "a,b,c"); assert r.returncode == 0, r.stderr
    m = json.load(open(tmp_path / "assets" / "manifest.json"))["assets"]
    assert set(m) == {"a", "b", "c"} and (tmp_path / "assets" / "svg" / "b.svg").exists()
    assert m["a"]["anchor"][1] == 1.0 and abs(m["a"]["anchor"][0] - 0.5) < 0.05
    assert m["b"]["holes"] and abs(m["b"]["holes"][0][0] + m["b"]["holes"][0][2] / 2 - 0.5) < 0.05
    assert m["a"]["holes"] == []

def test_name_count_mismatch_writes_nothing(tmp_path):
    r = run(make_sheet(tmp_path / "s.png"), tmp_path, "a,b")
    assert r.returncode != 0 and "found 3 assets, --names has 2" in r.stderr
    assert not (tmp_path / "assets").exists()

def test_grid_mode(tmp_path):
    assert run(make_sheet(tmp_path / "s.png"), tmp_path, "a,b,c", "--grid", "3x1").returncode == 0
```

(Run from `skills/mascot-explainer/` so `scripts/asset_sheet.py` resolves; `conftest.py` already adds `scripts/` to
the path for `mx`.)
- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement** `mx/sheet.py` then `asset_sheet.py` per the interface
  (argparse; `--anchor` either one kind for all or `name=kind` pairs; trace2 imported via `deps.locate("sv")`).
- [ ] **Step 4: Run, expect PASS** (4 passed). **Step 5: Commit** `mascot-explainer: asset sheet slicer`.

### Task 5: sprite_import.py (sliced sprite → project)

**Files:** Create `scripts/sprite_import.py`; Test `tests/test_sprite_import.py`

**Interfaces:**
- Consumes: a `slice.py --clip` output dir (`f00.svg…`, `frames.json` = `{cell, bg, floor, frames: [{file,x,y,w,h,…}]}`).
- Produces: CLI `scripts/py scripts/sprite_import.py FRAMES_DIR PROJECT NAME` → copies the SVGs to
  `PROJECT/assets/sprites/NAME/` and sets manifest `sprites[NAME] = {"dir": "assets/sprites/NAME", "cell", "floor",
  "frames": [{"file","x","y","w","h"}]}`. Refuses (exit, nothing copied) when any frame SVG lacks `<clipPath id="fig">`:
  `NAME: f03.svg was sliced without --clip; re-run slice.py with --clip`.

- [ ] **Step 1: Failing tests:** fixture dir with `frames.json` (2 frames) and two SVG strings containing
  `<clipPath id="fig">` → manifest entry equals the expected dict and both files copied; same fixture with one SVG
  missing the clipPath → non-zero exit, message above, no `assets/sprites/NAME` dir.
- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement** (≈40 lines, `shutil.copy`, `mx.manifest`).
- [ ] **Step 4: Run, expect PASS.** **Step 5: Commit** `mascot-explainer: sprite import`.
