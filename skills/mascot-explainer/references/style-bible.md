# Style bible: style.json

One file decides how every shot looks and sounds. The scenes only use palette roles, so a new bible gives a new
look without touching code.

```json
{"name": "coral-teal", "size": [1920, 1080], "fps": 30,
 "palette": {"bgDeep": "#0E2F38", "bgMid": "#1D5C66", "bgLight": "#7FB8B5", "panel": "#CFE8E4", "ink": "#141418",
             "skin": "#FF8A5B", "shorts": "#23305A", "sleeve": "#FFFFFF", "accent": "#FFD166", "text": "#FFFFFF", "rim": "#FFFFFF"},
 "chroma": "#00B140", "ink": 4, "mix": {"music": 0.5, "sfx": 0.6}, "voice": "af_heart",
 "character": "a bald, muscular, friendly cartoon man with coral-orange skin, white eye slits, a small mouth, navy athletic shorts, white wristbands, barefoot"}
```

| field | what it does |
|---|---|
| `size`, `fps` | the composition (render 4K with `--resolution landscape-4k`; the SVGs stay sharp) |
| `palette.bgDeep/bgMid/bgLight` | the three background tones (`tone: deep|mid|light`) |
| `palette.panel` | bubble discs, window frame, shelf, steps; `bgLight` doubles as the crater/stripe mark |
| `palette.ink` | every outline and dark stroke; keep it near-black (`#141418`) so traced ink matches code ink |
| `palette.skin/shorts/sleeve` | the character's colours, repeated in every asset prompt |
| `palette.accent` | glows, rays, coins, app headers, tags' highlight; one warm colour against the cool backgrounds |
| `palette.text`, `rim` | headline text and the bubble rims (white) |
| `chroma` | the flat background colour of every Nano Banana sheet, keyed out by `asset_sheet.py` / `slice.py` |
| `mix` | music and SFX volumes for build.py (tune until `mix_check.py` passes) |
| `voice` | Kokoro voice (`af_heart` is the best; also `af_bella`) |

## Choosing a palette

- Backgrounds: three tones of ONE hue (dark, mid, light). The reference uses violet; pick another hue so the video
  is clearly yours.
- The character's skin must stand out from all three backgrounds: a warm skin on cool backgrounds (or the reverse).
- One accent, warm and bright, used sparingly (glow, coins, the highlighted thing).
- `chroma` must differ from every colour in the art by more than 70 in summed RGB distance (the sheet test). Green
  `#00B140` works for warm characters and teal/violet palettes; use magenta `#FF00FF` if the art has green.
- Check contrast once: white text on `bgMid` and `bgDeep` must pass (hf check measures it).

## The drawing rules every prompt repeats

Flat vector cartoon. Thick, even black outlines (the same weight on every asset). Flat fills, at most one darker
shade per colour; muscles and folds drawn as ink lines, not shading. No gradients, textures, glow or drop shadows.
Faceless head with white eye slits (and a small mouth for effort). Simple hands with clear fingers. Nothing touching
the image edge. One solid `chroma` background, no floor, no text, no frame.

## The character bible

Write `character` once and paste it into every prompt, word for word. Generate the character sheet first
(`asset-prompts.md`), then pass that sheet as the FIRST reference image of every later call: proportions, colours and
line weight carry over. Keep a note of what the sheet shows (e.g. "wristbands on both arms", "no sleeve") and repeat
it when a pose comes back wrong.

The demo's mascot: coral-orange skin, navy shorts, white wristbands, on deep teal. Never use another channel's
mascot, logo, app or book name, in prompts or on screen.
