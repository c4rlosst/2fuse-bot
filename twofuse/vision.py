"""Read the 2Fuse board from a screenshot or video frame.

Geometry is for the 540x1170 portrait recording of an iPhone screen. Everything is
expressed as fractions of the frame so a different resolution of the same aspect
ratio works unchanged.
"""
from __future__ import annotations

import colorsys
from dataclasses import dataclass

import numpy as np
from PIL import Image

# Board bounds as fractions of the frame (measured on a 540x1170 frame).
BOARD_X0, BOARD_X1 = 8 / 540, 530 / 540
BOARD_Y0, BOARD_Y1 = 398 / 1170, 915 / 1170
N = 4

COLORS = "RGB"
EMPTY = "."


@dataclass(frozen=True)
class Cell:
    color: str  # one of RGB, or EMPTY
    value: str  # "1", "2", "S" (star), or "" when empty

    def __str__(self) -> str:
        return EMPTY * 2 if self.color == EMPTY else self.color + self.value


def _hue_to_color(h: float) -> str:
    """Hue in degrees -> tile color letter.

    The game only has red, green and blue tiles. Power-up glows tint tiles yellow or
    orange, so those hues are folded into the nearest real color.
    """
    if h < 48 or h >= 290:
        return "R"
    if h < 170:
        return "G"
    return "B"


def cell_boxes(w: int, h: int) -> list[list[tuple[int, int, int, int]]]:
    x0, x1 = BOARD_X0 * w, BOARD_X1 * w
    y0, y1 = BOARD_Y0 * h, BOARD_Y1 * h
    cw, ch = (x1 - x0) / N, (y1 - y0) / N
    return [
        [(round(x0 + c * cw), round(y0 + r * ch), round(x0 + (c + 1) * cw), round(y0 + (r + 1) * ch))
         for c in range(N)]
        for r in range(N)
    ]


def classify_cell(rgb: np.ndarray) -> Cell:
    """rgb: HxWx3 uint8 crop of exactly one grid cell."""
    h, w, _ = rgb.shape
    f = rgb.astype(np.float32) / 255.0
    mx, mn = f.max(axis=2), f.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)

    # Tile color: sample the inner frame of the tile, away from the centre glyph.
    m = int(0.16 * w)
    band = int(0.12 * w)
    ring = np.zeros((h, w), bool)
    ring[m:h - m, m:w - m] = True
    ring[m + band:h - m - band, m + band:w - m - band] = False
    px = f[ring]
    s_px, v_px = sat[ring], mx[ring]
    keep = (s_px > 0.45) & (v_px > 0.45)

    # Glyph in the centre: white numerals, or a bright yellow star.
    c0, c1 = int(0.25 * h), int(0.75 * h)
    r0, r1 = int(0.25 * w), int(0.75 * w)
    centre = f[c0:c1, r0:r1]
    white = centre.min(axis=2) > 0.80
    ch = _hue_deg(centre)
    star = (ch > 38) & (ch < 62) & (sat[c0:c1, r0:r1] > 0.55) & (mx[c0:c1, r0:r1] > 0.85)
    glyph = white.mean() >= 0.10 or star.mean() >= 0.15

    # Real tiles fill the whole ring; flame over an empty cell only fills part of it. A burst
    # effect can wash the ring out, so a visible glyph also proves a tile is there.
    ring_ok = keep.mean() >= 0.60
    if not ring_ok and not glyph:
        return Cell(EMPTY, "")

    color = "?"
    lenient = (s_px > 0.25) & (v_px > 0.40)
    if ring_ok or lenient.mean() >= 0.5:
        sel = px[keep] if ring_ok else px[lenient]
        r, g, b = (float(np.median(sel[:, i])) for i in range(3))
        color = _hue_to_color(colorsys.rgb_to_hsv(r, g, b)[0] * 360)

    if white.mean() < 0.04:
        return Cell(color, "S")
    # A "2" has a horizontal bar through the middle; a "1" is only a stem there.
    q = white.shape[0] // 4
    mid = white[q:3 * q].mean()
    return Cell(color, "2" if mid > 0.45 else "1")


def _hue_deg(f: np.ndarray) -> np.ndarray:
    """Per-pixel hue in degrees for an HxWx3 float array in 0..1."""
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(axis=2), f.min(axis=2)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4))
    return h * 60


def read_board(img: Image.Image) -> list[list[Cell]]:
    rgb = np.asarray(img.convert("RGB"))
    h, w, _ = rgb.shape
    return [[classify_cell(rgb[y0:y1, x0:x1]) for (x0, y0, x1, y1) in row] for row in cell_boxes(w, h)]


def board_str(board: list[list[Cell]]) -> str:
    return "\n".join(" ".join(str(c) for c in row) for row in board)
