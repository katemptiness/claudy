"""Pixel art as images: every picture Claudy draws is built here.

An image is identified by a hashable key; `build(key)` turns it into a
PixelImage (rows of RGBA colors, None for transparent) that backends
convert to a native image once and cache (see canvas.ImageCache).
"""

from dataclasses import dataclass

from claudy.config import (
    FRIEND_PALETTE, FRIEND_SHADES, PALETTE, PIXEL_SCALE, SHADES,
)
from claudy.content.sprites import SPRITES


@dataclass(frozen=True)
class PixelImage:
    rows: tuple    # rows of (r, g, b, a) tuples or None
    scale: int     # screen pixels per art pixel

    @property
    def width(self):
        return len(self.rows[0]) * self.scale

    @property
    def height(self):
        return len(self.rows) * self.scale


def sprite_key(name, friend=False, flip=False):
    """Key for a character sprite, optionally recolored or mirrored."""
    return ("sprite", name if name in SPRITES else "idle", friend, flip)


def build(key):
    kind = key[0]
    if kind == "sprite":
        return _build_sprite(*key[1:])
    raise KeyError(key)


def _build_sprite(name, friend, flip):
    grid = SPRITES[name]
    palette = FRIEND_PALETTE if friend else PALETTE
    shades = FRIEND_SHADES if friend else SHADES
    tones = shading(grid)
    rows = []
    for r, row in enumerate(grid):
        colors = [shades[tones[r, c]] if (r, c) in tones
                  else palette[v] if v else None
                  for c, v in enumerate(row)]
        if flip:
            colors.reverse()
        rows.append(tuple(colors))
    return PixelImage(tuple(rows), PIXEL_SCALE)


BODY, EYE = 1, 2


def shading(grid):
    """Light the crab from above: {(row, col): tone} for pixels to recolor.

    - "highlight": body pixels with nothing above them (top edges)
    - "shadow": the body's bottom row, the legs, and other bottom edges
    - "glint": the top-left pixel of each eye that is at least 2x2
    """
    height, width = len(grid), len(grid[0])

    def at(r, c):
        return grid[r][c] if 0 <= r < height and 0 <= c < width else 0

    def body_cols(r):
        return [c for c in range(width) if at(r, c) == BODY]

    def is_thin(r):
        # Every body pixel in the row stands alone, like legs
        return all(at(r, c - 1) != BODY and at(r, c + 1) != BODY
                   for c in body_cols(r))

    body_rows = [r for r in range(height) if body_cols(r)]
    wide_rows = [r for r in body_rows if not is_thin(r)]
    bottom = max(wide_rows) if wide_rows else height

    tones = {}
    for r in body_rows:
        for c in body_cols(r):
            if r >= bottom or (at(r + 1, c) == 0 and r > min(wide_rows)):
                tones[r, c] = "shadow"
            elif at(r - 1, c) == 0:
                tones[r, c] = "highlight"
    for r in range(height):
        for c in range(width):
            if (at(r, c) == EYE and at(r - 1, c) != EYE and at(r, c - 1) != EYE
                    and at(r + 1, c) == EYE and at(r, c + 1) == EYE):
                tones[r, c] = "glint"
    return tones
