"""Pixel art as images: every picture Claudy draws is built here.

An image is identified by a hashable key; `build(key)` turns it into a
PixelImage (rows of RGBA colors, None for transparent) that backends
convert to a native image once and cache (see canvas.ImageCache).
"""

from dataclasses import dataclass

from claudy.config import FRIEND_PALETTE, PALETTE, PIXEL_SCALE
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
    palette = FRIEND_PALETTE if friend else PALETTE
    rows = []
    for row in SPRITES[name]:
        colors = [palette[v] if v else None for v in row]
        if flip:
            colors.reverse()
        rows.append(tuple(colors))
    return PixelImage(tuple(rows), PIXEL_SCALE)
