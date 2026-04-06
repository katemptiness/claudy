"""Render 16x16 pixel grids to Cairo ImageSurfaces (Linux)."""

import cairo
from config import GRID, PIXEL_SCALE, SPRITE_SIZE, PALETTE, FRIEND_PALETTE


def render_sprite(grid, palette=None):
    """Render a 16x16 grid to an 80x80 Cairo ImageSurface."""
    if palette is None:
        palette = PALETTE
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, SPRITE_SIZE, SPRITE_SIZE)
    ctx = cairo.Context(surface)

    # No Y-flip needed: Cairo and grid both use top-left origin
    for row_idx, row in enumerate(grid):
        for col_idx, val in enumerate(row):
            if val == 0:
                continue
            r, g, b, a = palette[val]
            ctx.set_source_rgba(r, g, b, a)
            x = col_idx * PIXEL_SCALE
            y = row_idx * PIXEL_SCALE
            ctx.rectangle(x, y, PIXEL_SCALE, PIXEL_SCALE)
            ctx.fill()

    return surface


class SpriteCache:
    """Pre-renders all sprite grids at init for fast swapping."""

    def __init__(self, sprite_dict):
        self._cache = {}
        for name, grid in sprite_dict.items():
            self._cache[name] = render_sprite(grid)

    def get(self, name):
        return self._cache[name]

    def add(self, name, grid):
        self._cache[name] = render_sprite(grid)

    def add_friend(self, name, grid):
        """Render a sprite with the friend (blue) palette."""
        self._cache[f"friend_{name}"] = render_sprite(grid, FRIEND_PALETTE)

    def has(self, name):
        return name in self._cache
