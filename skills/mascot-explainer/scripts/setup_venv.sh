#!/usr/bin/env bash
# Creates the skill's own Python 3.12 venv (Homebrew's 3.14 has no wheels for the tracers). Needs uv.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
command -v uv >/dev/null || { echo "install uv first: brew install uv" >&2; exit 2; }
uv venv -q --python 3.12 "$SKILL/.venv"
uv pip install -q --python "$SKILL/.venv/bin/python" -r "$SKILL/requirements.txt"
"$SKILL/.venv/bin/python" -c "import numpy, scipy, PIL, vtracer, potrace, pytest; print('venv ok')"
