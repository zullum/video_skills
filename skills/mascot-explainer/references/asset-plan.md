# Asset plan: assets.json

Written right after the script, before any image call: every picture the video needs, so the checkpoint shows what
gets made, how, and for how much. Go through the script line by line and note every object a line names or implies
("fifteen minutes" → a clock, "film yourself" → a camera, "lift heavy" → weight plates), plus what the scenes need.

```json
{"code":    [{"name": "clock", "for": "s03 'fifteen minutes'", "how": "cream face, black ticks, gold hands"}],
 "items":   [{"name": "camera", "what": "a compact photo camera with a big round lens", "for": "s07"},
             {"name": "kettlebell", "what": "a kettlebell", "anchor": "feet", "for": "s15 step 3"}],
 "poses":   [{"name": "hips", "what": "waist-up, both hands on the hips", "for": "s00, s12 insets"}],
 "props":   [{"name": "handphone", "what": "his hand holding a phone, the screen in the chroma colour", "for": "s07"}],
 "sprites": [{"name": "pushup", "frames": 24, "for": "s01, s10-s14, s18"}]}
```

| kind | what goes there | how it is made | cost |
|---|---|---|---|
| `code` | geometric things: clock, stopwatch, tick, cross, arrow, coin, calendar page, speech bubble, heart, star, flag, simple badges | Claude writes the SVG (palette hex colours, `#141418` outlines 6-10 px, a viewBox), then `svg_asset.py P NAME FILE.svg [--anchor feet]` | $0 |
| `items` | small objects too organic or detailed for code: weights, kettlebell, camera, bottle, shoe, food, a laptop, a plant | `item_sheet.py P`: up to 24 per sheet, one call | ~$0.011 a sheet |
| `poses` | the character, 6 per pose sheet | `asset-prompts.md` §2 + `asset_sheet.py` | ~$0.015 a sheet |
| `props` | things tied to the character (his hand with a phone) or to a scene (the crowd silhouette) | `asset-prompts.md` §3 | ~$0.015 a sheet |
| `sprites` | each exercise loop: a base pose, then one sheet | `asset-prompts.md` §4, `KIND=sprite` | ~$0.06 a move |

Rules of thumb:
- Prefer `code` whenever the thing is circles, rectangles and lines: it is free, sharp and recolourable.
- Plan items generously: they make shots richer, and 24 cost the same as 2. Give each item one short concrete
  `what` (colour, view, one detail); no people or hands in items (those are props or poses).
- `"anchor": "feet"` for things that stand on something (a kettlebell on a step, a shoe on the floor); the default
  `center` suits things that pop, fly, float and turn.
- Every name in the plan must be used by a shot (a scene param or an `item` beat, `scene-catalog-2.md`); every asset a
  shot uses must be in the plan.

`item_sheet.py` reads only `items`; the other lists are the checklist for the asset stage and the checkpoint's cost
table. After the asset stage, every name exists in `assets/manifest.json` (or `sprites`).
