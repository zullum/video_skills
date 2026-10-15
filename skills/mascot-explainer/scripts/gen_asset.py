"""One budgeted Nano Banana call.   scripts/py scripts/gen_asset.py PROJECT OUT.png "prompt" [ref ...]
env SIZE=1K|2K|4K (default 2K), ASPECT (default 16:9). An existing OUT is reused (delete it to regenerate);
a call that would pass gen/budget.json "limit" is refused (exit 3). The key is never printed."""
import fcntl
import json
import os
import subprocess
import sys

import deps

PRICES = {"1K": 0.067, "2K": 0.101, "4K": 0.151}


def _ledger(project):
    p = os.path.join(project, "gen", "budget.json")
    return p, (json.load(open(p)) if os.path.exists(p) else {"limit": 1.5, "spent": 0.0, "calls": []})


def run(project, out, prompt, refs, size="2K", aspect="16:9", gen_cmd=None):
    if os.path.exists(out):
        print(f"cached {out}")
        return 0
    path, led = _ledger(project)
    price = PRICES[size]
    if led["spent"] + price > led["limit"] + 1e-9:
        print(f"budget: ${led['spent']:.3f} of ${led['limit']:.2f} spent, this call costs ${price:.3f}; "
              f"raise \"limit\" in {path} to go on", file=sys.stderr)
        return 3
    print(f"Nano Banana {size} {aspect}: ${price:.3f} (spent ${led['spent']:.3f} of ${led['limit']:.2f})")
    cmd = gen_cmd or [sys.executable, os.path.join(deps.locate("sv"), "scripts", "gen.py")]
    r = subprocess.run(cmd + [out, prompt] + list(refs), env=dict(os.environ, SIZE=size, ASPECT=aspect))
    if r.returncode or not os.path.exists(out):
        return r.returncode or 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "w") as lock:                   # parallel calls: re-read and write under a lock
        fcntl.flock(lock, fcntl.LOCK_EX)
        _, led = _ledger(project)
        led["spent"] = round(led["spent"] + price, 3)
        led["calls"].append({"file": os.path.relpath(out, project), "size": size, "price": price, "prompt": prompt[:160]})
        json.dump(led, open(path, "w"), indent=1)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    sys.exit(run(a[0], a[1], a[2], a[3:], os.environ.get("SIZE", "2K"), os.environ.get("ASPECT", "16:9")))
