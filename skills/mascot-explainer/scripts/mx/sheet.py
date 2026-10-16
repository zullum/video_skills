"""Pure helpers for asset_sheet.py: find the assets drawn on a flat (chroma) background sheet."""
import numpy as np
from scipy import ndimage


def background(a):
    """Median colour of the four 20x20 corners."""
    h, w, k = a.shape[0], a.shape[1], 20
    corners = [a[:k, :k], a[:k, w - k:], a[h - k:, :k], a[h - k:, w - k:]]
    return tuple(int(v) for v in np.median(np.concatenate([c.reshape(-1, 3) for c in corners]), 0))


def mask(a, bg):
    """True where the sheet is not background (the same test as sprite-video's slice.py)."""
    return ndimage.binary_opening(np.abs(a[..., :3].astype(int) - np.array(bg)).sum(2) > 70, iterations=1)


def reading_order(boxes):
    """Rows top to bottom (a new row when a top is more than half the median height lower), then left to right."""
    if not boxes:
        return []
    half = float(np.median([b[3] - b[1] for b in boxes])) / 2
    rows = []
    for b in sorted(boxes, key=lambda b: b[1]):
        if rows and b[1] - rows[-1][0][1] <= half:
            rows[-1].append(b)
        else:
            rows.append([b])
    return [b for row in rows for b in sorted(row, key=lambda b: b[0])]


def find_assets(m, grid=None, min_frac=0.002):
    """Boxes (x0, y0, x1, y1): one per non-empty grid cell, or one per large connected component."""
    H, W = m.shape
    if grid:
        cols, rows = grid
        cw, ch, out = W / cols, H / rows, []
        for r in range(rows):
            for c in range(cols):
                x0, y0, x1, y1 = int(c * cw) + 10, int(r * ch) + 10, int((c + 1) * cw) - 10, int((r + 1) * ch) - 10
                sub = m[y0:y1, x0:x1]
                if sub.sum() < min_frac * sub.size:
                    continue
                ys, xs = np.where(sub)
                out.append((x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1))
        return out
    lab, n = ndimage.label(ndimage.binary_closing(m, iterations=3))
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    boxes = [(s[1].start, s[0].start, s[1].stop, s[0].stop)
             for i, s in enumerate(ndimage.find_objects(lab)) if sizes[i] >= min_frac * m.size]
    return reading_order(boxes)


def holes(mc, min_frac=0.005, most=3):
    """Enclosed background areas (a phone screen, the gap between arm and body) as [x, y, w, h] fractions."""
    h, w = mc.shape
    lab, _ = ndimage.label(ndimage.binary_fill_holes(mc) & ~mc)
    found = []
    for i, s in enumerate(ndimage.find_objects(lab)):
        area = int((lab[s] == i + 1).sum())
        if area >= min_frac * h * w:
            found.append((area, [round(s[1].start / w, 4), round(s[0].start / h, 4),
                                 round((s[1].stop - s[1].start) / w, 4), round((s[0].stop - s[0].start) / h, 4)]))
    return [box for _, box in sorted(found, key=lambda f: -f[0])[:most]]


def anchor(mc, kind="feet"):
    """feet: x = mean of the lowest 5 % of rows, y = the bottom of the drawing; center: the middle."""
    if kind == "center":
        return [0.5, 0.5]
    h, w = mc.shape
    ys, xs = np.where(mc)
    low = ys >= ys.max() - max(1, int(0.05 * (ys.max() - ys.min() + 1)))
    return [round(float(xs[low].mean()) / w, 4), round((int(ys.max()) + 1) / h, 4)]
