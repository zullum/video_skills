# 01 Foundation (Tasks 1-2)

### Task 1: Skill skeleton, venv, dependency lookup, check

**Files:**
- Create: `skills/mascot-explainer/{.gitignore,requirements.txt}`
- Create: `skills/mascot-explainer/scripts/{setup_venv.sh,py,deps.py,check.sh}`
- Create: `skills/mascot-explainer/tests/{conftest.py,test_deps.py}`
- Create: symlink `.claude/skills/mascot-explainer -> ../../skills/mascot-explainer`

**Interfaces:**
- Produces: `deps.locate(name, home=None, skill_dir=None) -> str` (name `sv`|`vm`|full name; raises `SystemExit`
  naming the folders searched); CLI `scripts/py scripts/deps.py sv|vm` prints the path.
  `scripts/py <args>` runs `.venv/bin/python`. `tests/conftest.py` puts `scripts/` on `sys.path`.

- [ ] **Step 1: Write the venv files**

`.gitignore`: `.venv/` and `__pycache__/`. `requirements.txt`: `numpy scipy pillow vtracer potracer pytest`
(one per line). `scripts/setup_venv.sh`:

```bash
#!/usr/bin/env bash
# Creates the skill's own Python 3.12 venv (Homebrew's 3.14 has no wheels for the tracers). Needs uv.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
command -v uv >/dev/null || { echo "install uv first: brew install uv" >&2; exit 2; }
uv venv -q --python 3.12 "$SKILL/.venv"
uv pip install -q --python "$SKILL/.venv/bin/python" -r "$SKILL/requirements.txt"
"$SKILL/.venv/bin/python" -c "import numpy, scipy, PIL, vtracer, potrace, pytest; print('venv ok')"
```

`scripts/py`:

```sh
#!/bin/sh
# Runs the skill's Python 3.12 venv (scripts/setup_venv.sh creates it).
D="$(cd "$(dirname "$0")/.." && pwd)"
[ -x "$D/.venv/bin/python" ] || { echo "no venv: bash $D/scripts/setup_venv.sh" >&2; exit 2; }
exec "$D/.venv/bin/python" "$@"
```

Run: `chmod +x skills/mascot-explainer/scripts/*.sh skills/mascot-explainer/scripts/py && bash skills/mascot-explainer/scripts/setup_venv.sh`
Expected: `venv ok`

- [ ] **Step 2: Write the failing test** `tests/test_deps.py` (+ `tests/conftest.py` with
  `sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))`)

```python
import os, pytest, deps

def mk(path):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").close()

def test_sibling_with_marker_wins(tmp_path):
    skills = tmp_path / "skills"; me = skills / "mascot-explainer"; me.mkdir(parents=True)
    mk(str(skills / "sprite-video" / "scripts" / "trace2.py"))
    mk(str(tmp_path / "home" / ".claude" / "skills" / "sprite-video" / "scripts" / "trace2.py"))
    assert deps.locate("sv", home=str(tmp_path / "home"), skill_dir=str(me)) == os.path.realpath(skills / "sprite-video")

def test_falls_back_to_home_when_sibling_lacks_marker(tmp_path):
    skills = tmp_path / "skills"; me = skills / "mascot-explainer"; me.mkdir(parents=True)
    (skills / "viral-motion").mkdir()                       # repo copy without .venv
    home_vm = tmp_path / "home" / ".claude" / "skills" / "viral-motion"
    mk(str(home_vm / ".venv" / "bin" / "python"))
    assert deps.locate("vm", home=str(tmp_path / "home"), skill_dir=str(me)) == os.path.realpath(home_vm)

def test_missing_names_the_search_paths(tmp_path):
    me = tmp_path / "skills" / "mascot-explainer"; me.mkdir(parents=True)
    with pytest.raises(SystemExit, match="viral-motion not found"):
        deps.locate("vm", home=str(tmp_path / "home"), skill_dir=str(me))
```

- [ ] **Step 3: Run, expect FAIL** — `cd skills/mascot-explainer && scripts/py -m pytest tests/test_deps.py -q` (no `deps`)

- [ ] **Step 4: Implement `scripts/deps.py`**

```python
"""Find the sibling skills mascot-explainer uses.   python deps.py sv|vm   -> prints the folder
A skill is found next to this one (repo or install folder) first, then in ~/.claude/skills; it counts only
if its marker file exists (viral-motion needs its own venv for Kokoro, which the repo copy does not have)."""
import os, sys
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKERS = {"sprite-video": "scripts/trace2.py", "viral-motion": ".venv/bin/python"}
ALIASES = {"sv": "sprite-video", "vm": "viral-motion"}

def candidates(name, home=None, skill_dir=None):
    home, skill_dir = home or os.path.expanduser("~"), skill_dir or SKILL
    return [os.path.join(os.path.dirname(skill_dir), name), os.path.join(home, ".claude", "skills", name)]

def locate(name, home=None, skill_dir=None):
    name = ALIASES.get(name, name)
    found = candidates(name, home, skill_dir)
    for c in found:
        if os.path.exists(os.path.join(c, MARKERS[name])):
            return os.path.realpath(c)
    raise SystemExit(f"{name} not found (looked in: {', '.join(found)}); "
                     "install it next to mascot-explainer: bash install.sh claude")

if __name__ == "__main__":
    print(locate(sys.argv[1]))
```

- [ ] **Step 5: Run tests, expect PASS** (3 passed). Then `scripts/py scripts/deps.py sv` prints
  `…/video_skills/skills/sprite-video` and `scripts/py scripts/deps.py vm` prints `~/.claude/skills/viral-motion`.

- [ ] **Step 6: Write `scripts/check.sh`** (installs nothing; one line per requirement, exit 1 on any MISS)

```bash
#!/usr/bin/env bash
# Checks what mascot-explainer needs and prints the fix for each missing piece. Installs nothing.
SKILL="$(cd "$(dirname "$0")/.." && pwd)"; ok=1
row() { if [ "$2" = 0 ]; then echo "  ok    $1"; else echo "  MISS  $1  ->  $3"; ok=0; fi; }
"$SKILL/.venv/bin/python" -c "import numpy,scipy,PIL,vtracer,potrace" 2>/dev/null; row "venv (py3.12 + tracers)" $? "bash $SKILL/scripts/setup_venv.sh"
SV=$("$SKILL/scripts/py" "$SKILL/scripts/deps.py" sv 2>/dev/null); row "sprite-video" $? "bash install.sh claude (video_skills repo)"
VM=$("$SKILL/scripts/py" "$SKILL/scripts/deps.py" vm 2>/dev/null); row "viral-motion + venv" $? "install viral-motion, run its scripts/check.sh"
[ -n "$VM" ] && "$VM/.venv/bin/python" -c "import kokoro_onnx" 2>/dev/null; row "Kokoro voice" $? "bash $VM/scripts/check.sh"
command -v ffmpeg >/dev/null; row "ffmpeg" $? "brew install ffmpeg"
node -e 'process.exit(+process.versions.node.split(".")[0] < 18)' 2>/dev/null; row "node 18+" $? "brew install node"
test -f "$HOME/myprojects/whisper.cpp/models/ggml-large-v3-turbo.bin"; row "whisper large-v3-turbo" $? "see viral-motion README"
[ -n "$VM" ] && "$VM/scripts/hf" --version >/dev/null 2>&1; row "HyperFrames CLI" $? "npm i -g hyperframes"
if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then echo "  ok    Gemini key (asset stage)"
else echo "  note  no GEMINI_API_KEY: the asset stage can't run; code-only scenes still work"; fi
[ $ok = 1 ] && echo "all good" || { echo "fix the MISS lines"; exit 1; }
```

Run: `bash skills/mascot-explainer/scripts/check.sh` → every row `ok`, `all good`.

- [ ] **Step 7: Symlink + commit**

```bash
ln -s ../../skills/mascot-explainer .claude/skills/mascot-explainer
git add skills/mascot-explainer .claude/skills/mascot-explainer
git -c user.name=Sanel -c user.email=zullumsan@gmail.com commit -m "mascot-explainer: skeleton, venv, dependency lookup, check

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 2: sprite-video `--clip` (transparent outside the figure)

trace2 traces the background as fill shapes, which is fine on sprite-video's matching background but shows a box
on any other colour. Add an opt-in clip: the fill layer is clipped to the figure mask eroded by 2 px (so the clip
edge hides under the ink outline and no background fringe survives); the ink layer stays unclipped on top.
Default behaviour is unchanged.

**Files:**
- Modify: `skills/sprite-video/scripts/trace2.py` (extract `_outline(mask, up)`, add `clip_def`, `trace(..., clip=False)`)
- Modify: `skills/sprite-video/scripts/slice.py` (`--clip` flag → `trace2.trace(..., clip=A.clip)`, usage line)
- Test: `skills/mascot-explainer/tests/test_clip.py`

**Interfaces:**
- Produces: `trace2.trace(rgb, pal, bg, out, clip=False)`; with `clip=True` the SVG holds
  `<defs><clipPath id="fig"><path clip-rule="evenodd" d=…/></clipPath></defs><g clip-path="url(#fig)">fills</g>` then ink.

- [ ] **Step 1: Failing test** `tests/test_clip.py`

```python
import importlib, sys, numpy as np, deps
from PIL import Image, ImageDraw
sys.path.insert(0, deps.locate("sv") + "/scripts"); trace2 = importlib.import_module("trace2")
BG = (0, 177, 64)

def ring_image():
    im = Image.new("RGB", (240, 240), BG); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 220, 220], fill=(255, 122, 89), outline=(20, 20, 24), width=8)
    d.ellipse([90, 90, 150, 150], fill=BG, outline=(20, 20, 24), width=8)   # a hole
    return np.array(im)

def palette():
    p = Image.new("P", (1, 1)); p.putpalette([18, 18, 22, 255, 255, 255, *BG, 255, 122, 89] + [0] * 756); return p

def test_clip_wraps_fills_and_keeps_the_hole(tmp_path):
    out = tmp_path / "a.svg"; trace2.trace(ring_image(), palette(), BG, str(out), clip=True)
    s = out.read_text()
    assert '<clipPath id="fig">' in s and 'clip-path="url(#fig)"' in s
    clip = s[s.index('<clipPath'):s.index('</clipPath>')]
    assert clip.count("M") >= 2                       # outer outline + the hole

def test_default_has_no_clip(tmp_path):
    out = tmp_path / "b.svg"; trace2.trace(ring_image(), palette(), BG, str(out))
    assert "clipPath" not in out.read_text()
```

- [ ] **Step 2: Run, expect FAIL** (`unexpected keyword argument 'clip'`). **Step 3: Implement** in trace2.py: move the potrace-to-path loop of `ink_paths` into
  `_outline(mask, up)` returning the `d` string (`ink_paths` then returns
  `f'<path fill="{INK}" fill-rule="evenodd" d="{_outline(big, up)}"/>'`), and add:

```python
def clip_def(rgb, bg, up=4):
    m = np.abs(rgb[..., :3].astype(int) - np.array(bg)).sum(2) > 70        # same test as slice.py
    m = ndimage.binary_erosion(ndimage.binary_opening(m, iterations=1), iterations=2)
    big = np.array(Image.fromarray((m * 255).astype("uint8")).resize(
        (rgb.shape[1] * up, rgb.shape[0] * up), Image.BICUBIC)) > 127
    return f'<clipPath id="fig"><path clip-rule="evenodd" d="{_outline(big, up)}"/></clipPath>'
```

and in `trace`: `fills = fill_layer(rgb, pal, bg)`; when `clip`:
`fills = f'<defs>{clip_def(rgb, bg)}</defs><g clip-path="url(#fig)">{fills}</g>'`. slice.py: add the flag, pass
`clip=A.clip`, and document `--clip  transparent outside the figure (for scenes on another background)`.

- [ ] **Step 4: Run, expect PASS** (both; whole suite green). **Step 5: Commit** `sprite-video: optional --clip`.
