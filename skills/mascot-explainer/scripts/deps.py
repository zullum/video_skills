"""Find the sibling skills mascot-explainer uses.   python deps.py sv|vm   -> prints the folder
A skill is found next to this one (repo or install folder) first, then in ~/.claude/skills; it counts only
if its marker file exists (viral-motion needs its own venv for Kokoro, which the repo copy does not have)."""
import os
import sys

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
