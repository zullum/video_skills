"""The project's asset manifest: assets/manifest.json = {"assets": {...}, "sprites": {...}}."""
import json
import os


def path(project):
    return os.path.join(project, "assets", "manifest.json")


def load(project):
    m = json.load(open(path(project))) if os.path.exists(path(project)) else {}
    m.setdefault("assets", {})
    m.setdefault("sprites", {})
    return m


def save(project, m):
    os.makedirs(os.path.dirname(path(project)), exist_ok=True)
    json.dump(m, open(path(project), "w"), indent=1, sort_keys=True)
