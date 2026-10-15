# 03 Timing and build (Tasks 6-8)

Paths relative to `skills/mascot-explainer/`. Tests: `scripts/py -m pytest tests -q`.

### Task 6: Beat resolution, SFX events, whisper words

**Files:** Create `scripts/mx/beats.py`, `scripts/mx/whisper.py`, `tests/fixtures/whisper.json`; Test `tests/test_beats.py`

**Interfaces:**
- Produces: `beats.norm(word) -> str` (lowercase, keep `a-z0-9'-`, strip edge `'-`);
  `beats.resolve_at(at, dur, words, shot_id) -> float` (clamped to `[0, dur]`; `ValueError` for a missing word:
  `"<id>: '<w>' is not in the narration; heard: a, b, c"`); `beats.events_for(beat) -> [{"t","kind","note"}]`;
  `beats.resolve_shot(shot, dur, words, next_in, size) -> {"scene","params","beats":[{"t","do","args"}],"in","out"}`;
  `beats.transition_cues(resolved, starts) -> [sfx_cues.json cue]`; `whisper.words(path, offset=0.0) -> [{"w","t"}]`.

Rules:
- `at`: number; `"end"` / `"end-0.6"`; `"word:<w>"`, `"word:<w>#2"` (2nd occurrence), `"word:<w>+0.15"` / `"-0.1"`
  (regex `^word:(?P<w>.+?)(?:#(?P<n>\d+))?(?P<off>[+-](?:\d+\.?\d*|\.\d+))?$`; `push-ups` stays one word).
- `ACTION_SFX = {pop,show,fill,insets,think,icons,place: "pop"; highlight,ignite: "shimmer"; coins: "chime";
  slam,burst,flash: "impact"; freeze: "stamp"; zoom,zoomInto,fly,launch,flip,split: "whoosh"; tag,cite,build,arrow: "tick";
  callout: "snap"; type: "blip"}`; other verbs make no sound.
- A beat whose args hold a list under `items|rows|cols|heads` (or an int `count`) makes one event per element at
  `t + i*stagger` (`stagger` default 0.12), at most 8 spread over the same span. `zoom`/`zoomInto` make one whoosh at
  `t + dur - 0.3` (`dur` default 0.6).
- `resolve_shot`: beats sorted by `t`; `out = next_in` when it is `whip` or `flash`; when `next_in == "zoomIn"` and no
  beat is `zoom`/`zoomInto`, append `{"t": dur-0.5, "do": "zoomInto", "args": {"x": W/2, "y": H/2, "dur": 0.5}}`.
- `transition_cues`: `whip` → `{"fx":"whoosh","gain_db":-10,"peak":true,"args":{"dur":0.5}}` at the cut;
  `flash` → `impact` −8; `pop` → `pop` −14; each with `"t"` = shot start and `"label": "<id> in:<kind>"`.

- [ ] **Step 1: Failing tests** `tests/test_beats.py` (+ fixture: `{"transcription": [{"text": "", "offsets":
  {"from": 0, "to": 60}}, {"text": " Push-ups,", "offsets": {"from": 60, "to": 1230}}, {"text": " rows,", …1230…},
  {"text": " rows.", …2000…}]}`)

```python
import pytest
from mx import beats, whisper
W = [{"w": "push-ups", "t": 0.26}, {"w": "rows", "t": 1.23}, {"w": "rows", "t": 2.0}]

def test_numbers_end_and_clamp():
    assert beats.resolve_at(0.5, 3, [], "s1") == 0.5
    assert beats.resolve_at("end-0.6", 3, [], "s1") == pytest.approx(2.4)
    assert beats.resolve_at(5, 3, [], "s1") == 3

def test_words():
    assert beats.resolve_at("word:rows", 3, W, "s1") == 1.23
    assert beats.resolve_at("word:rows#2", 3, W, "s1") == 2.0
    assert beats.resolve_at("word:Push-ups+0.1", 3, W, "s1") == pytest.approx(0.36)

def test_missing_word_names_shot_and_heard_words():
    with pytest.raises(ValueError, match=r"s1: 'squats' is not in the narration; heard: push-ups, rows"):
        beats.resolve_at("word:squats", 3, W, "s1")

def test_events():
    assert [e["t"] for e in beats.events_for({"t": 1, "do": "pop", "args": {"items": [0, 1, 2]}})] == [1, 1.12, 1.24]
    many = beats.events_for({"t": 1, "do": "fill", "args": {"count": 24, "stagger": 0.04}})
    assert len(many) == 8 and many[-1]["t"] == pytest.approx(1.92)
    assert beats.events_for({"t": 2, "do": "zoom", "args": {"i": 0}}) == [{"t": 2.3, "kind": "whoosh", "note": "zoom"}]
    assert beats.events_for({"t": 1, "do": "draw", "args": {}}) == []

def test_resolve_shot_out_and_auto_zoom():
    shot = {"scene": "bubbles", "params": {}, "beats": [{"at": "end-0.2", "do": "pop"}, {"at": 0.1, "do": "pop"}]}
    r = beats.resolve_shot(shot, 3, [], "whip", (1920, 1080))
    assert r["out"] == "whip" and [b["t"] for b in r["beats"]] == [0.1, 2.8]
    z = beats.resolve_shot(shot, 3, [], "zoomIn", (1920, 1080))["beats"][-1]
    assert z == {"t": 2.5, "do": "zoomInto", "args": {"x": 960, "y": 540, "dur": 0.5}}

def test_whisper_words(tmp_path):
    assert whisper.words("tests/fixtures/whisper.json", 0.2)[:2] == [{"w": "push-ups", "t": 0.26}, {"w": "rows", "t": 1.43}]
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement** both modules to the rules above.
- [ ] **Step 4: Run, expect PASS.** **Step 5: Commit** `mascot-explainer: beat resolution and sfx events`.

### Task 7: timing.py (narration → audio/timing.json)

**Files:** Create `scripts/timing.py`; Test `tests/test_timing.py`

**Interfaces:**
- Consumes: `<vm>/scripts/hf tts "<say>" -v <voice> -s <speed> -o <raw.wav> --json` (stdout JSON, `durationSeconds`),
  `<vm>/scripts/recording/run_whisper.sh turbo <16k.wav> <prefix> -l en` (writes `<prefix>.json`), `mx.whisper.words`.
- Produces: `timing.layout(shots, speech, words, lead=0.2, tail=0.3) -> timing dict` (pure);
  CLI `scripts/py scripts/timing.py PROJECT [--lead 0.2] [--tail 0.3] [--no-voice]` → `audio/timing.json`,
  `assets/audio/narration/<id>.wav` (stereo 48 kHz, viral-motion's chain:
  `pan=stereo|c0=c0|c1=c0,acompressor=threshold=0.063:ratio=3:attack=5:release=120:makeup=2,loudnorm=I=-16:TP=-3:LRA=11`),
  cache `audio/narration/<id>.json = {"key": sha1(say|voice|speed), "speech", "words"}` (a hit skips TTS and whisper).
- Rules: a shot with `say` lasts `max(lead + speech + tail + hold, dur or 0)`; its words are offset by `lead`;
  a shot without `say` needs `dur` (`SystemExit("<id>: no \"say\" and no \"dur\"")`); `--no-voice` treats every shot
  as silent and needs `dur` everywhere; `--recording P/audio/recording.json` (the user's own voice, output of
  `<vm>/scripts/recording/pipeline.sh`; read its format in `<vm>/references/recording.md` first) maps line i to the
  i-th shot with `say`, takes speech length and word times from it and cuts `clean.wav` per line with ffmpeg.

- [ ] **Step 1: Failing tests**

```python
import pytest, timing
SH = [{"id": "s1", "say": "Two sets."}, {"id": "s2", "dur": 3}]

def test_layout():
    t = timing.layout(SH, {"s1": 1.6}, {"s1": [{"w": "two", "t": 0.1}]})
    a, b = t["shots"]
    assert a["dur"] == pytest.approx(2.1) and a["words"] == [{"w": "two", "t": pytest.approx(0.3)}]
    assert b["start"] == pytest.approx(2.1) and t["duration"] == pytest.approx(5.1) and b["voice"] is None

def test_hold_and_min_dur():
    t = timing.layout([{"id": "s1", "say": "x", "hold": 1, "dur": 1}], {"s1": 1.0}, {"s1": []})
    assert t["shots"][0]["dur"] == pytest.approx(2.5)

def test_missing_dur_names_shot():
    with pytest.raises(SystemExit, match="s2"):
        timing.layout([{"id": "s2"}], {}, {})
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement** `layout`, `voice()` (TTS + ffmpeg + cache), `heard()`
  (ffmpeg 16 kHz mono + run_whisper.sh + `whisper.words`), `main()`. Keep ≤200 lines.
- [ ] **Step 4: Run, expect PASS.** Smoke: a temp project with `shots.json` `{"voice": "af_heart", "shots":
  [{"id": "s1", "say": "Two sets are enough to start.", "scene": "space"}]}` → `timing.json` lists 6 words
  starting with `two`; a second run prints `cached s1`.
- [ ] **Step 5: Commit** `mascot-explainer: narration timing`.

### Task 8: build.py (project files, validation, audio)

**Files:** Create `scripts/build.py`, `scripts/mx/html.py`, `scripts/mx/audio.py`, `scripts/mx/registry.py`;
Test `tests/test_build.py`

**Interfaces:**
- Consumes: Tasks 3, 6, 7; `<vm>/scripts/sfx/build_sfx.py PROJECT` (→ `assets/audio/sfx.wav`),
  `<vm>/scripts/sfx/duck_lane.py file@start … --base 0.5` (stdout = lane JSON).
- Produces: `registry.load(lib_dir, extra=None) -> {"scenes": {name: [actions]}, "generic": [actions]}` (`extra` =
  the project's `assets/js/scenes`, for one-off scenes that build.py's copy never overwrites) parsed from header
  lines `// @scene <name> @actions a,b,c` (`lib/scenes/*.js`) and `// @actions a,b` (`lib/toon-core.js`);
  `build.main(project, only=None, sfx=True, lib_dir=SKILL/lib)`; CLI `scripts/py scripts/build.py PROJECT
  [--only s01,s02] [--no-sfx]`; `html.scene_html(id, shot, dur, size) -> str`;
  `html.index_html(style, manifest, slots, audio_tags, scripts) -> str` (`slots = [(id, start, dur)]`);
  `audio.tags(project, timing, vm) -> [str]`.
- Validation before writing anything (each a `SystemExit` naming the shot): unknown scene (`"s01: unknown scene
  'bubblez'; known: …"`), unknown action (`"s01: scene 'bubbles' has no action 'popp'; it has: …"`), unknown asset
  or sprite in params (any key `asset`/`sprite` anywhere in params: `"s01: unknown asset 'jarr'; have: …"`).
- Written: `index.html` (GSAP 3.14.2 CDN, `assets/js/toon-core.js`, `toon-shapes.js`, `toon-sprite.js`,
  `scenes/*.js`, inline `TOON.init(style, manifest)`, `@font-face` `TDisplay` = `assets/fonts/BarlowCondensed-ExtraBoldItalic.woff2`
  (800 italic) and `TLabel` = `assets/fonts/Barlow-Bold.woff2` (700), a hidden `data-layout-ignore` font preloader,
  one host per shot `class="host clip"` track 1, audio tags, main timeline); `compositions/<id>.html` (the
  `<template>` shape from the spike: style + `#root` + `#<id>-stage` + `window.__timelines["<id>"] = TOON.run(…)`,
  JSON with `</` escaped); `compositions/<id>.motion.json`; `audio/sfx_cues.json` (`duration`, `slots`,
  transition cues); copies `lib/*.js`, `lib/scenes/` → `assets/js/`, `lib/fonts/` → `assets/fonts/`.
- Audio tags: narration `<audio id="nar-<id>" … data-start="start+lead" data-duration="speech" data-track-index="9">`;
  music (if `assets/audio/music.wav`) track 10, volume `style.mix.music` (default 0.5), `data-automation` = duck lane
  over all narration; SFX (if `assets/audio/sfx.wav` after build_sfx) `id="sfx-main"` track 11, volume `style.mix.sfx` (0.6). No timing.json → layout from
  `dur` (lead 0, silent).

- [ ] **Step 1: Failing tests** (`tmp_path` project with `style.json` size `[1920,1080]`, palette with `bgDeep`, a
  fake lib dir holding `scenes/demo.js` = `// @scene demo @actions pop,zoom` and `toon-core.js` = `// @actions push`)

```python
import json, pytest, build
from mx import html

def project(tmp_path, shots, manifest=None):
    (tmp_path / "style.json").write_text(json.dumps({"size": [1920, 1080], "fps": 30, "palette": {"bgDeep": "#0B2E35"}}))
    (tmp_path / "shots.json").write_text(json.dumps({"shots": shots}))
    (tmp_path / "assets").mkdir(); (tmp_path / "assets" / "manifest.json").write_text(json.dumps(manifest or {"assets": {"blob": {}}, "sprites": {}}))
    return tmp_path

def lib(tmp_path):
    d = tmp_path / "lib"; (d / "scenes").mkdir(parents=True); (d / "fonts").mkdir()
    (d / "scenes" / "demo.js").write_text("// @scene demo @actions pop,zoom\n"); (d / "toon-core.js").write_text("// @actions push\n")
    return d

def test_builds_project(tmp_path):
    p = project(tmp_path / "p", [{"id": "s01", "dur": 2, "scene": "demo", "params": {"asset": "blob"},
                                  "beats": [{"at": 0.2, "do": "pop", "args": {"items": [0, 1]}}], "in": "cut"},
                                 {"id": "s02", "dur": 1, "scene": "demo", "in": "whip"}])
    build.main(str(p), sfx=False, lib_dir=str(lib(tmp_path)))
    idx = (p / "index.html").read_text()
    assert 'data-composition-src="compositions/s02.html" data-start="2.000" data-duration="1.000"' in idx
    assert 'data-duration="3.000"' in idx and "TDisplay" in idx
    scene = json.loads((p / "compositions" / "s01.motion.json").read_text())["events"]
    assert [e["t"] for e in scene] == [0.2, 0.32]
    cues = json.loads((p / "audio" / "sfx_cues.json").read_text())
    assert cues["slots"] == {"s01": 0, "s02": 2} and cues["cues"][0]["fx"] == "whoosh"
    assert '"out": "whip"' in (p / "compositions" / "s01.html").read_text()

@pytest.mark.parametrize("shot,msg", [
    ({"id": "s01", "dur": 1, "scene": "bubblez"}, "s01: unknown scene 'bubblez'; known: demo"),
    ({"id": "s01", "dur": 1, "scene": "demo", "beats": [{"at": 0, "do": "popp"}]}, "s01: scene 'demo' has no action 'popp'"),
    ({"id": "s01", "dur": 1, "scene": "demo", "params": {"items": [{"asset": "jarr"}]}}, "s01: unknown asset 'jarr'; have: blob")])
def test_validation(tmp_path, shot, msg):
    p = project(tmp_path / "p", [shot])
    with pytest.raises(SystemExit, match=msg): build.main(str(p), sfx=False, lib_dir=str(lib(tmp_path)))
    assert not (p / "index.html").exists()

def test_scene_html_escapes_script_end():
    assert "<\\/script>" in html.scene_html("s01", {"params": {"text": "</script>"}}, 1, (1920, 1080))
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement** `registry.py`, `html.py`, `audio.py`, `build.py`.
- [ ] **Step 4: Run, expect PASS.** **Step 5: Commit** `mascot-explainer: project builder`.
