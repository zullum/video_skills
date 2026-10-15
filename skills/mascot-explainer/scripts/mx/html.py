"""HTML of the generated HyperFrames project: index.html and one templated sub-composition per shot."""
import json

GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
FONTS = [("TDisplay", "BarlowCondensed-ExtraBoldItalic.woff2", 800, "italic"), ("TLabel", "Barlow-Bold.woff2", 700, "normal")]
PRELOAD = ('<div class="fontload" data-layout-ignore aria-hidden="true">'
           '<span style="font-family:TDisplay;font-weight:800;font-style:italic">Aa</span>'
           '<span style="font-family:TLabel;font-weight:700">Aa</span></div>')


def _js(obj):
    return json.dumps(obj).replace("</", "<\\/")


def scene_html(sid, shot, dur, size):
    w, h = size
    return f"""<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>#root {{ position: absolute; inset: 0; overflow: hidden; }} #{sid}-stage {{ position: absolute; inset: 0; overflow: hidden; }}</style>
<div id="root" data-composition-id="{sid}" data-width="{w}" data-height="{h}"><div id="{sid}-stage"></div></div>
<script>window.__timelines["{sid}"] = TOON.run("{sid}", {_js(shot)}, {dur});</script>
</template></body></html>
"""


def index_html(style, manifest, slots, audio_tags, scripts):
    w, h = style["size"]
    total = round(sum(d for _, _, d in slots), 3)
    bg = style.get("palette", {}).get("bgDeep", "#000000")
    faces = "\n".join(f'@font-face {{ font-family: "{n}"; src: url("assets/fonts/{f}") format("woff2"); '
                      f'font-weight: {wt}; font-style: {st}; font-display: block; }}' for n, f, wt, st in FONTS)
    tags = "\n".join(f'<script src="{s}"></script>' for s in scripts)
    hosts = "\n".join(f'  <div id="{i}" class="host clip" data-composition-id="{i}" data-composition-src="compositions/{i}.html" '
                      f'data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="1" data-width="{w}" data-height="{h}"></div>'
                      for i, s, d in slots)
    audio = "\n".join("  " + a for a in audio_tags)
    return f"""<!doctype html>
<html lang="en" data-resolution="landscape">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width={w}, height={h}" />
<script src="{GSAP}"></script>
{tags}
<script>TOON.init({_js(style)}, {_js(manifest)});</script>
<style>
{faces}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
.host {{ position: absolute; inset: 0; }}
.fontload {{ position: absolute; left: 0; top: 0; opacity: 0; pointer-events: none; font-size: 20px; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{w}" data-height="{h}">
  {PRELOAD}
{hosts}
{audio}
</div>
<script>window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body>
</html>
"""
