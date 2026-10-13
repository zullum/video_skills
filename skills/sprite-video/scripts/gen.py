# usage: python3 gen.py OUT.png "prompt" [ref1.png ref2.png ...]
#   env: SIZE=1K|2K|4K (default 2K), ASPECT=16:9|21:9|5:4|1:1|... (default 16:9),
#        MODEL (default gemini-3.1-flash-image), GEMINI_API_KEY (optional, see below)
# One Nano Banana (Gemini image) call. Reference images go in as inline parts, the first image part
# of the answer is written to OUT.
# Key: if GEMINI_API_KEY (or GOOGLE_API_KEY) is set it is sent as the x-goog-api-key header; if not,
# the request goes out without a key (for environments whose proxy injects it). The key is never printed.
import base64, json, os, sys, urllib.request, urllib.error

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__ or "usage: gen.py OUT.png PROMPT [refs...]")
    out, prompt, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
    model = os.environ.get("MODEL", "gemini-3.1-flash-image")
    mime = lambda p: "image/jpeg" if p.lower().endswith((".jpg", ".jpeg")) else "image/png"
    parts = [{"text": prompt}] + [
        {"inline_data": {"mime_type": mime(r), "data": base64.b64encode(open(r, "rb").read()).decode()}} for r in refs]
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"],
                                 "imageConfig": {"aspectRatio": os.environ.get("ASPECT", "16:9"),
                                                 "imageSize": os.environ.get("SIZE", "2K")}}}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        headers["x-goog-api-key"] = key
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(), headers=headers)
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:600].decode(errors='replace')}")
    for p in resp["candidates"][0]["content"]["parts"]:
        d = p.get("inlineData") or p.get("inline_data")
        if d:
            open(out, "wb").write(base64.b64decode(d["data"]))
            print("wrote", out)
            return
    sys.exit("no image in answer: " + json.dumps(resp)[:800])

if __name__ == "__main__":
    main()
