"""Beat times and their sounds. A beat's "at" becomes seconds from the shot start; every beat that makes a
sound becomes motion events (build_sfx.py kinds), so picture and sound come from the same numbers."""
import re

WORD = re.compile(r"^word:(?P<w>.+?)(?:#(?P<n>\d+))?(?P<off>[+-](?:\d+\.?\d*|\.\d+))?$")
END = re.compile(r"^end(?P<off>-(?:\d+\.?\d*|\.\d+))?$")
ACTION_SFX = {
    **dict.fromkeys(["pop", "show", "fill", "insets", "think", "icons", "place", "item"], "pop"),
    **dict.fromkeys(["highlight", "ignite"], "shimmer"), "coins": "chime",
    **dict.fromkeys(["slam", "burst", "flash"], "impact"), "freeze": "stamp",
    **dict.fromkeys(["zoom", "zoomInto", "fly", "launch", "flip", "split"], "whoosh"),
    **dict.fromkeys(["tag", "cite", "build", "arrow"], "tick"), "callout": "snap", "type": "blip"}
LISTS = ("items", "rows", "cols", "heads")
TRANSITIONS = {"whip": {"fx": "whoosh", "gain_db": -15, "peak": True, "args": {"dur": 0.5}},
               "flash": {"fx": "impact", "gain_db": -15}, "pop": {"fx": "pop", "gain_db": -19}}
MAX_EVENTS = 8


def norm(w):
    return re.sub(r"[^a-z0-9'\-]", "", w.lower()).strip("-'")


def resolve_at(at, dur, words, shot_id):
    if isinstance(at, (int, float)):
        t = float(at)
    elif END.match(at):
        t = dur + float(END.match(at).group("off") or 0)
    elif WORD.match(at):
        m = WORD.match(at)
        w, n = norm(m.group("w")), int(m.group("n") or 1)
        hits = [x["t"] for x in words if x["w"] == w]
        if len(hits) < n:
            heard = ", ".join(dict.fromkeys(x["w"] for x in words))
            raise ValueError(f"{shot_id}: '{w}' is not in the narration; heard: {heard}"
                             + (f" ({len(hits)} time(s), #{n} asked)" if hits else ""))
        t = hits[n - 1] + float(m.group("off") or 0)
    else:
        raise ValueError(f"{shot_id}: can't read at={at!r} (seconds, 'end-0.5' or 'word:<w>[#n][+-s]')")
    return round(min(max(t, 0.0), dur), 3)


def events_for(beat):
    kind = ACTION_SFX.get(beat["do"])
    if not kind:
        return []
    a, t = beat.get("args") or {}, beat["t"]
    if beat["do"] in ("zoom", "zoomInto"):
        return [{"t": round(max(0.0, t + a.get("dur", 0.6) - 0.3), 3), "kind": "whoosh", "note": beat["do"]}]
    if beat["do"] == "item" and a.get("in") == "fly":
        return [{"t": t, "kind": "whoosh", "note": "item"}]
    n = next((len(a[k]) for k in LISTS if isinstance(a.get(k), list)), a.get("count", a.get("n")))
    if not n or n == 1:
        return [{"t": t, "kind": kind, "note": beat["do"]}]
    st, k = a.get("stagger", 0.12), min(n, MAX_EVENTS)
    step = st * (n - 1) / (k - 1)
    return [{"t": round(t + i * step, 3), "kind": kind, "note": f"{beat['do']} {i + 1}/{k}"} for i in range(k)]


def resolve_shot(shot, dur, words, next_in, size):
    sid = shot.get("id", "?")
    bs = [{"t": resolve_at(b["at"], dur, words, sid), "do": b["do"], "args": b.get("args") or {}}
          for b in shot.get("beats") or []]
    bs.sort(key=lambda b: b["t"])
    out = next_in if next_in in ("whip", "flash") else None
    if next_in == "zoomIn" and not any(b["do"] in ("zoom", "zoomInto") for b in bs):
        bs.append({"t": round(max(dur - 0.5, 0), 3), "do": "zoomInto",
                   "args": {"x": size[0] // 2, "y": size[1] // 2, "dur": 0.5}})
    return {"scene": shot["scene"], "params": shot.get("params") or {}, "beats": bs,
            "in": shot.get("in") or "cut", "out": out}


def transition_cues(shots, starts, ids):
    return [dict(TRANSITIONS[s["in"]], t=st, label=f"{i} in:{s['in']}")
            for s, st, i in zip(shots, starts, ids) if s.get("in") in TRANSITIONS]
