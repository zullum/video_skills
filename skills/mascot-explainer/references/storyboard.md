# Storyboard: shots.json

The storyboard is the only timeline. Python resolves every beat to seconds from the narration, writes the
HyperFrames project, and derives the sound effects from the same beats, so picture and sound never drift.

```json
{"style": "style.json", "voice": "af_heart", "speed": 1.0, "shots": [
  {"id": "s01", "say": "Push-ups. Squats. Two sets each.", "scene": "bubbles", "params": {}, "beats": [], "in": "cut"},
  {"id": "s02", "dur": 2.0, "scene": "textSlam", "params": {"text": "TWO SETS"}, "beats": [{"at": 0.3, "do": "slam"}]}]}
```

| field | meaning |
|---|---|
| `id` | unique, short (`s01`); also the sub-composition id |
| `say` | the narration line of this shot (Kokoro voice, or line i of the user's recording) |
| `dur` | length of a silent shot; with `say` it is a minimum |
| `hold` | extra seconds after the line (a visual beat to land) |
| `scene`, `params` | which template and how it is set up (`scene-catalog*.md`) |
| `beats` | `{"at", "do", "args"}`: what happens when |
| `in` | how the shot starts: `cut`, `pop`, `zoomIn`, `whip`, `flash` |

A voiced shot lasts `lead (0.2 s) + spoken length + tail (0.3 s) + hold`. Words come from whisper on the line itself.

## `at`
- `1.2`: seconds from the shot start · `"end"`, `"end-0.6"`: from its end
- `"word:squats"`: when that word starts · `"word:rows#2"`: its 2nd occurrence · `"word:floor+0.15"` / `-0.1`: offset
- Words are lowercase, punctuation stripped, hyphens kept (`push-ups`). Numbers may come back as digits or words:
  if a beat fails, the error lists what whisper heard; use that spelling.

## Pacing (measured on the reference)
- A new visual beat every 2-5 s; a cut on most line ends; inside a line, the key word lands an action.
- Something moves at all times: the idle push, bobbing bubbles, twinkling sparkles. No frame is still for 2 s.
- Motifs return: the same three exercise bubbles open the video, come back in the schedule, in the window, and close it.
- Lists → one pop per item on the item's word. Contrasts → split screen or highlight + dim. Big claims → textSlam.
- One exercise demo per exercise: zoom into its bubble, then the frame-by-frame loop with callout and tag.
- ≤ 18 spoken words per shot; split a longer line into two shots.

## Narration pattern → template

| the line is… | use |
|---|---|
| a list of options, "all those choices" | `bubbles` (pop per item, `swarm` for "too many") |
| a schedule, days, "three times a week" | `days` (+ `tag`) |
| a time, a duration, "it's quick" | `flyBy` with a `badge` |
| a study, a number from research | `shelf` + `crowd` + `cite` |
| a term, a rule, a claim | `textSlam` (`slam` on the word) |
| apps, feeds, "you saved 15 videos" | `phone` (`scroll`, `icons`), `cardWall` |
| doubt, overthinking | `windowRoom` with the figure looking at a `swarm` |
| how to do an exercise | `exerciseDemo` (`callout`, `arrow`, `tag`, `insets`) |
| progression, "harder over time" | `seqRows`, `stairs` |
| energy, a turn, "go do it" | `powerUp` (`ignite`, `burst`) · a pause or aside → `freeze` |
| a guide, a book, "it's all written down" | `document` |

## Running it
```bash
scripts/py scripts/timing.py P              # narration + word times (cached per line)
scripts/py scripts/build.py P --no-sfx      # fast loop while you iterate on pictures
scripts/py scripts/build.py P               # final: SFX stem + ducked music
```
Edit `say`, `hold` or `voice` → run timing.py again (only changed lines are re-voiced).
