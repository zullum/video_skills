"""One cached image call.   scripts/py scripts/gen_asset.py PROJECT OUT.png "prompt" [ref ...]
env KIND picks the defaults, all OpenAI GPT Image 2.5 on fal.ai (scripts/fal_gen.py, FAL_AI_API_KEY): still (the
default: character, poses, props, sprite base poses) is low quality at Full HD (~$0.0045), sprite (an animation
sprite sheet) medium quality at 4K (~$0.026); each reference adds ~$0.01. SIZE=1K|HD|2K|4K, QUALITY and ASPECT
(default 16:9) override them. PROVIDER=gemini-web draws in the Gemini web app of the user's logged-in Chrome on CDP
9003 instead ($0, ~2K, only the app's aspect ratios, the JPEG stored as a PNG); PROVIDER=api pays for Nano Banana.
No key is ever printed. Relative OUT and refs are inside PROJECT. An existing OUT is reused (delete
it to regenerate); a call that would pass gen/budget.json "limit" is refused (exit 3); a second call for the same OUT
while one runs exits 4; an unknown KIND or PROVIDER exits 2. Every call is booked in the ledger under a lock before it runs."""
import fcntl
import json
import math
import os
import subprocess
import sys

import deps

PRICES = {"1K": 0.067, "2K": 0.101, "4K": 0.151}
MODEL = "gemini-3.1-flash-image"                     # pinned: the prices above are this model's
FAL_PRICES = {"low": {"1K": 0.004, "HD": 0.0045, "2K": 0.0062, "4K": 0.0111},       # GPT Image 2.5 Flare on fal,
              "medium": {"1K": 0.009, "HD": 0.0103, "2K": 0.0143, "4K": 0.026},     # per image (the ledger's
              "high": {"1K": 0.0361, "HD": 0.0396, "2K": 0.0553, "4K": 0.1001}}     # estimates)
FAL_REF = 0.01                                        # each reference image
PROVIDERS = ("fal", "gemini-web", "api")
KINDS = {"still": ("fal", "HD", "low"), "sprite": ("fal", "4K", "medium")}   # provider, size, quality per kind
WEB_ASPECTS = ("1:1", "16:9", "9:16", "4:3", "3:4")  # the Gemini app's aspect-ratio menu
WEB_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_web.cjs")
FAL_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fal_gen.py")


def web_aspect(aspect):
    """The app's ratio nearest to `aspect` (by log ratio): 3:2 -> 4:3, 2:3 -> 3:4, 21:9 -> 16:9."""
    r = lambda a: math.log(float(a.split(":")[0]) / float(a.split(":")[1]))
    return min(WEB_ASPECTS, key=lambda w: abs(r(w) - r(aspect)))


def _as_png(path):
    """The web app downloads JPEGs: store the image as a real PNG under its .png name."""
    if open(path, "rb").read(2) == b"\xff\xd8":
        from PIL import Image
        Image.open(path).convert("RGB").save(path, "PNG")


def _warn_small(path):
    """The web app usually sends ~2K but now and then 1K (1376x768 at 16:9): too small for a 12-cell sprite sheet."""
    from PIL import Image
    try:
        w, h = Image.open(path).size
    except OSError:                                   # not an image PIL reads: nothing to warn about
        return
    if max(w, h) < 2000:
        print(f"warning: the Gemini app sent {w}x{h}, not ~2K; delete {os.path.basename(path)} and run again if detail matters")


def _locked(path, fn):
    """Run fn(ledger) under an exclusive lock and write the ledger back; parallel calls see each other."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        led = json.load(open(path)) if os.path.exists(path) else {"limit": 1.5, "spent": 0.0, "calls": []}
        result = fn(led)
        json.dump(led, open(path, "w"), indent=1)
        return result


def run(project, out, prompt, refs, size=None, aspect="16:9", gen_cmd=None, provider=None, kind=None):
    kind = kind or os.environ.get("KIND", "still")
    if kind not in KINDS:
        print(f"unknown KIND {kind!r}; one of {', '.join(KINDS)}", file=sys.stderr)
        return 2
    provider = provider or os.environ.get("PROVIDER") or KINDS[kind][0]
    size = size or (KINDS[kind][1] if provider == "fal" else "4K" if kind == "sprite" else "2K")   # api has no HD
    quality = os.environ.get("QUALITY") or KINDS[kind][2]
    if provider not in PROVIDERS:
        print(f"unknown PROVIDER {provider!r}; one of {', '.join(PROVIDERS)}", file=sys.stderr)
        return 2
    web = provider == "gemini-web"
    inside = lambda p: p if os.path.isabs(p) else os.path.join(project, p)  # relative = inside the project
    out, refs = inside(out), [inside(r) for r in refs]
    if os.path.exists(out):
        print(f"cached {out}")
        return 0
    if web and web_aspect(aspect) != aspect:
        print(f"the Gemini app has no {aspect}: asking for {web_aspect(aspect)}")
    aspect = web_aspect(aspect) if web else aspect
    path, rel = os.path.join(project, "gen", "budget.json"), os.path.relpath(out, project)
    price = 0.0 if web else (round(FAL_PRICES.get(quality, FAL_PRICES["high"])[size] + FAL_REF * len(refs), 4)
                             if provider == "fal" else PRICES[size])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        os.close(os.open(out + ".pending", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        print(f"{rel} is being generated by another call; wait for it", file=sys.stderr)
        return 4
    try:
        def reserve(led):                               # the money is booked before the call, under the lock
            if led["spent"] + price > led["limit"] + 1e-9:
                return led["spent"], led["limit"]
            led["spent"] = round(led["spent"] + price, 3)
            led["calls"].append({"file": rel, "size": size, "quality": quality, "price": price, "provider": provider,
                                 "prompt": prompt[:160], "status": "pending"})
            return None
        refused = _locked(path, reserve)
        if refused:
            print(f"budget: ${refused[0]:.3f} of ${refused[1]:.2f} spent, this call costs ${price:.3f}; "
                  f"raise \"limit\" in {path} to go on", file=sys.stderr)
            return 3
        label = {"gemini-web": "Gemini web", "fal": "GPT Image 2.5 (fal)", "api": "Nano Banana"}[provider]
        print(f"{label} {aspect}: $0" if web else f"{label} {size} {quality} {aspect}: ${price:.4f} reserved")
        cmd = gen_cmd or {"gemini-web": ["node", WEB_SCRIPT], "fal": [sys.executable, FAL_SCRIPT],
                          "api": [sys.executable, os.path.join(deps.locate("sv"), "scripts", "gen.py")]}[provider]
        r = subprocess.run(cmd + [out, prompt] + refs,
                           env=dict(os.environ, SIZE=size, ASPECT=aspect, QUALITY=quality, MODEL=MODEL))
        ok = r.returncode == 0 and os.path.exists(out)
        if ok:
            _as_png(out)
            if web:
                _warn_small(out)

        def settle(led):                                # keep the booking, or refund a call that made nothing
            for c in led["calls"]:
                if c["file"] == rel and c.get("status") == "pending":
                    if ok:
                        del c["status"]
                    else:
                        led["calls"].remove(c)
                        led["spent"] = round(led["spent"] - price, 3)
                    break
        _locked(path, settle)
        return 0 if ok else (r.returncode or 1)
    finally:
        os.remove(out + ".pending")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    sys.exit(run(a[0], a[1], a[2], a[3:], os.environ.get("SIZE"), os.environ.get("ASPECT", "16:9")))
