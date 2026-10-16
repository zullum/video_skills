"""fal_gen.py: GPT Image 2.5 sizes within fal's limits and the request body (no network)."""
import base64

import fal_gen


def test_sizes_fit_fals_limits():
    assert fal_gen.dims("4K", "16:9") == (3840, 2160)                 # exactly the 8.3 MP cap
    assert fal_gen.dims("HD", "16:9") == (1920, 1072)                 # 1080 is no multiple of 16
    assert fal_gen.dims("4K", "1:1") == (2880, 2880)
    w, h = fal_gen.dims("4K", "3:2")
    assert w * h <= fal_gen.MAX_PX and w % 16 == 0 and h % 16 == 0 and abs(w / h - 1.5) < 0.01
    w, h = fal_gen.dims("1K", "16:9")                                  # 1024x576 is under the minimum
    assert w * h >= fal_gen.MIN_PX and w % 16 == 0 and h % 16 == 0


def test_references_go_inline_and_pick_the_edit_endpoint(tmp_path):
    ref = tmp_path / "r.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    url, body = fal_gen.request("prompt", [str(ref)], "4K", "16:9", "medium", "openai/gpt-image-2.5/flare")
    assert url.endswith("/openai/gpt-image-2.5/flare/edit")
    assert body["image_urls"] == ["data:image/png;base64," + base64.b64encode(ref.read_bytes()).decode()]
    assert body["image_size"] == {"width": 3840, "height": 2160} and body["quality"] == "medium"
    url, body = fal_gen.request("prompt", [], "2K", "1:1", "medium", "openai/gpt-image-2.5/flare")
    assert url.endswith("/text-to-image") and "image_urls" not in body
