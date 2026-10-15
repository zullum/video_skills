"""Gallery fixture: a synthetic chroma sheet with a ring (orange, ink outline, see-through hole) traced into the
project as asset "ring" by asset_sheet.py, so the selftest checks a real traced asset on another background."""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import asset_sheet  # noqa: E402

G, INK = (0, 177, 64), (20, 20, 24)


def main(project):
    os.makedirs(os.path.join(project, "gen"), exist_ok=True)
    png = os.path.join(project, "gen", "ring_sheet.png")
    im = Image.new("RGB", (400, 400), G)
    d = ImageDraw.Draw(im)
    d.ellipse([60, 60, 340, 340], fill=(255, 122, 89), outline=INK, width=10)
    d.ellipse([150, 150, 250, 250], fill=G, outline=INK, width=10)
    im.save(png)
    asset_sheet.main([png, project, "--names", "ring", "--anchor", "center"])


if __name__ == "__main__":
    main(sys.argv[1])
