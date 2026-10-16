"""trace2.palette: the shared trace palette of asset_sheet.py and slice.py."""
import importlib
import sys

import numpy as np

import deps

sys.path.insert(0, deps.locate("sv") + "/scripts")
trace2 = importlib.import_module("trace2")
BG = (0, 177, 64)
RED = (215, 38, 61)


def art_with_small_red():
    """24 large blue-green-grey fills (more than the 14 median-cut slots) and a red patch of 0.5 % (a headband)."""
    fills = [(40 + 3 * i, 80 + 5 * i, 90 + 5 * i) for i in range(24)]
    px = [np.tile(c, (4000, 1)) for c in fills] + [np.tile(RED, (500, 1))]
    return np.concatenate(px).astype("uint8")


def nearest(pal, c):
    cols = np.array(pal.getpalette()[:768]).reshape(-1, 3)
    return int(np.abs(cols - np.array(c)).sum(1).min())


def test_a_small_distinct_colour_keeps_its_own_entry():
    assert nearest(trace2.palette(art_with_small_red(), BG), RED) < 40


def test_ink_white_and_background_come_first():
    assert trace2.palette(art_with_small_red(), BG).getpalette()[:9] == [18, 18, 22, 255, 255, 255, *BG]


def test_a_noisy_flat_fill_gets_one_entry_not_many():
    rng = np.random.default_rng(2)
    skin = np.clip(np.array([65, 150, 225]) + rng.integers(-6, 7, (50000, 3)), 0, 255)   # a generated flat fill is not flat
    art = np.concatenate([skin, np.tile((45, 111, 169), (10000, 1))]).astype("uint8")
    cols = np.array(trace2.palette(art, BG).getpalette()[:768]).reshape(-1, 3)
    cols = cols[3:][cols[3:].sum(1) > 0]                       # the art's entries
    near = [c for c in cols if np.abs(c - np.array([65, 150, 225])).sum() < 30]
    assert len(near) == 1                                       # one skin colour: no mottled patches of near-twins
