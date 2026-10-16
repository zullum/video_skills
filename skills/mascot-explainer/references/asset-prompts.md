# Asset prompts (Nano Banana, through scripts/gen_asset.py)

Every call: `SIZE=2K ASPECT=<a> scripts/py scripts/gen_asset.py PROJECT gen/<name>.png "<prompt>" [refs…]` (the Gemini
web app by default, `PROVIDER=api` for the paid API; see the last sections). It prints the price, refuses past `gen/budget.json` "limit", and never regenerates a file that exists (delete it to
retry). Replace `{CHARACTER}` with `style.json` "character", `{CHROMA}` with "chroma" and the colours with the
palette. After the character sheet, pass `gen/character.png` as the FIRST reference of every call.

The style block (`{STYLE}`), pasted into every prompt:
> Flat vector cartoon in a clean explainer style. Thick, even black outlines (#141418), the same line weight
> everywhere. Flat fills with at most one darker shade; muscles drawn as black ink lines. No gradients, no textures,
> no glow, no shadows, no floor, no text, no frame. The background is one solid flat colour {CHROMA} everywhere.
> Nothing touches the image edge.

## 1. Character sheet (1 call, 2K, 16:9)
> Character model sheet of {CHARACTER}. Top row: the same character four times, full body, standing relaxed with
> arms slightly away from the body: front view, three-quarter view, side view facing right, back view. Bottom row:
> three head-and-shoulder close-ups: calm, focused effort with pressed lips, happy. Skin {skin}, shorts {shorts},
> wristbands {sleeve}. Leave wide empty space between all figures. {STYLE}

Check: same proportions in all views, no extra props, the background one flat colour. It is a reference, not an asset.

## 2. Pose sheet (1 call per 6 poses, 2K, 3:2) → `asset_sheet.py … --grid 3x2 --names …`
> Using exactly the character in the reference image (same proportions, colours and outlines), draw six separate
> poses in a 3 by 2 grid, one per cell, each centred in its cell with empty space around it and nothing crossing
> into another cell: 1. {pose 1} 2. {pose 2} … 6. {pose 6}. No grid lines. {STYLE}

Poses that cover the catalog: waist-up front with hands on hips (textSlam backdrops, powerUp); waist-up raising
one finger; full body seen from behind, standing (cardWall, windowRoom fg); sitting on the floor looking at a
phone; an astronaut helmet and suit seen over the shoulder from behind, three-quarter (windowRoom fg); full body
front standing, arms crossed (stairs top). One pose per exercise for bubbles: the start pose of the move.

## 3. Prop sheet (1 call, 2K, 1:1) → `asset_sheet.py … --grid 3x3 --names …`
> Nine separate props in a 3 by 3 grid for the same cartoon world, one per cell, centred with empty space around
> it: 1. {prop} … 9. {prop}. Colours from this palette only: {panel}, {bgLight}, {accent}, white, {ink}. No grid
> lines. {STYLE}

Useful props: a white plyometric box, a rocket with a blank round emblem pointing up, a satellite with solar panels,
a jam jar with a fruit label, a plain standing human silhouette in {bgLight} with no face (crowd), a cartoon hand
holding a smartphone from below whose screen is one solid {CHROMA} rectangle with no interface (phone: the screen
becomes a hole), a dumbbell, gymnastic rings, a pair of parallettes. Use `--anchor` per name: `feet` for things that
stand, `center` for things that float (rocket, satellite).

## 4. Sprite base pose (1 call, 2K, aspect of the grid) → sprite-video template
> Using exactly the character in the reference image, {view} view, full body, at the {start} of a {exercise}
> ({one line of form: e.g. hands under the shoulders, body straight}). Centred, nothing cropped, {STYLE}

Then build the grid template with `<sprite-video>/scripts/template.py` (the base in every cell plus red guides) and
generate the sheet with `<sprite-video>/references/prompts.md` → "All-cells grid" or "Guided in-betweens",
passing the template first and the base second. 24 cells (6×4) at 4K for a smooth loop of a small figure; 8-9
cells (4×2, 3×3) at 2K for a whole-body move. Slice with `slice.py --clip` (+ `--ground` for standing moves), then
`sprite_import.py`.

## Gemini web app (the default provider)
The prompts below were written for the API and work in the Gemini web app with three changes. Ask for a NEW image and say what the reference is
for: "Using exactly the character in the attached reference image (...), create a brand-new image with exactly ONE
figure: ... Do not reproduce the reference sheet." (an agent-side test redrew the whole reference sheet without it).
At most 3 references per call. Only 1:1, 16:9, 9:16, 4:3 and 3:4 exist (gen_asset asks for the nearest and says so):
lay out pose and prop grids for 4:3 or 16:9, and build sprite templates at the ratio that is asked for. Tested on Dr.
Gains: one figure, exact skin colour, 2400x1792 at 4:3 and 2752x1536 at 16:9, no visible watermark, ~40 s per image.
Sprite sheets: start every sheet at the start of the move and say "cell 1 is the top position ... every cell is a
little lower than the one before"; a "frames 13 to 24" sheet came back with its first row redrawn from the top, twice.
The template is the first reference, the base pose the second. The red the app draws is a little duller than the
API's (headband 181,45,63 vs 204,34,60): fine for a sprite, but keep all sprite sheets of a move from the same provider.

## What the demo taught
- Grid sheets: the model may draw grid lines anyway (harmless: `--grid` keeps a margin) and crops full-body poses
  at the cell edge (3 of 6 in the demo). Cropped poses work at the bottom edge of the frame (cardWall, powerUp);
  for a full-body pose standing on something, slice the character sheet itself (`asset_sheet.py gen/character.png P
  --names …` without `--grid`), which costs nothing.
- Dark character colours (navy shorts) are traced as fills, not ink, through `--ink-keep` (asset_sheet reads them from
  `style.json` by default; give `slice.py --ink-keep "#23305A"` for sprites).
- A 24-cell side-view push-up came out right first time with a 4K sheet and the template's erase reaching the
  floor (otherwise the rotated hands show twice).

## What to check, and when to pay for a retry

Retry only when a rule is broken: a different character (proportions, colours, a sleeve that shouldn't be there),
a cell whose figure touches its neighbour or the cell edge, text or a grid drawn on the sheet, a non-flat
background, red guide marks left on a sprite sheet. Small drawing wobbles are fixed for free in slicing (drop a cell
with `--drop`, hold frames longer in `rep`). Budget one retry per new sheet.
