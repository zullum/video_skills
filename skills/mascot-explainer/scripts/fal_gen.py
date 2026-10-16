"""One image from OpenAI's GPT Image 2.5 on fal.ai.   python fal_gen.py OUT.png "prompt" [ref.png ...]
env: FAL_AI_API_KEY (or FAL_KEY), SIZE=1K|HD|2K|4K (longest edge 1024/1920/2048/3840, default 4K), ASPECT (default
16:9), QUALITY low|medium|high|xhigh|max (default medium: ~$0.026 at 3840x2160; low at 1920x1080 ~$0.0045; each
reference adds ~$0.01), FAL_MODEL (default
openai/gpt-image-2.5/flare; .../sunburst costs the same with sharper detail). With references it calls the model's
/edit (up to 16, sent inline as data URIs), without them /text-to-image. gen_asset.py runs it by default.
The key is never printed."""
import base64
import json
import math
import os
import sys
import urllib.error
import urllib.request

EDGE = {"1K": 1024, "HD": 1920, "2K": 2048, "4K": 3840}
MAX_PX, MIN_PX = 8_294_400, 655_360                  # fal's limits: 3840x2160 at most, both sides multiples of 16


def dims(size, aspect):
    """Width and height for SIZE at ASPECT: the longest edge, then fitted into fal's pixel range."""
    a, b = (float(v) for v in aspect.split(":"))
    edge = EDGE[size]
    w, h = (edge, edge * b / a) if a >= b else (edge * a / b, edge)
    if w * h > MAX_PX:
        s = math.sqrt(MAX_PX / (w * h))
        return int(w * s) // 16 * 16, int(h * s) // 16 * 16
    if w * h < MIN_PX:
        s = math.sqrt(MIN_PX / (w * h))
        return math.ceil(w * s / 16) * 16, math.ceil(h * s / 16) * 16
    return int(w) // 16 * 16, int(h) // 16 * 16


def request(prompt, refs, size, aspect, quality, model):
    """The fal.run URL and JSON body of one call."""
    w, h = dims(size, aspect)
    body = {"prompt": prompt, "image_size": {"width": w, "height": h}, "quality": quality,
            "output_format": "png", "num_images": 1}
    if refs:
        mime = lambda p: "image/jpeg" if p.lower().endswith((".jpg", ".jpeg")) else "image/png"
        body["image_urls"] = [f"data:{mime(r)};base64," + base64.b64encode(open(r, "rb").read()).decode() for r in refs]
    return f"https://fal.run/{model}/{'edit' if refs else 'text-to-image'}", body


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out, prompt, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
    key = os.environ.get("FAL_AI_API_KEY") or os.environ.get("FAL_KEY")
    if not key:
        sys.exit("no FAL_AI_API_KEY (or FAL_KEY) in the environment: export it in ~/.zshrc")
    url, body = request(prompt, refs, os.environ.get("SIZE", "4K"), os.environ.get("ASPECT", "16:9"),
                        os.environ.get("QUALITY", "medium"), os.environ.get("FAL_MODEL", "openai/gpt-image-2.5/flare"))
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=900))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:600].decode(errors='replace')}")
    images = resp.get("images") or []
    if not images:
        sys.exit("no image in answer: " + json.dumps(resp)[:600])
    with urllib.request.urlopen(images[0]["url"], timeout=300) as r, open(out, "wb") as f:
        f.write(r.read())
    print("wrote", out, f"({body['image_size']['width']}x{body['image_size']['height']}, {body['quality']})")


if __name__ == "__main__":
    main()
