"""Render 16x16 pixel grids to CGImage via CGContext (macOS)."""

import Quartz
from config import GRID, PIXEL_SCALE, SPRITE_SIZE, PALETTE, FRIEND_PALETTE


def render_sprite(grid, palette=None):
    """Render a 16x16 grid to an 80x80 CGImage."""
    if palette is None:
        palette = PALETTE
    cs = Quartz.CGColorSpaceCreateDeviceRGB()
    ctx = Quartz.CGBitmapContextCreate(
        None, SPRITE_SIZE, SPRITE_SIZE,
        8,  # bits per component
        SPRITE_SIZE * 4,  # bytes per row
        cs,
        Quartz.kCGImageAlphaPremultipliedLast,
    )

    # Flip Y so row 0 of the grid is at the top of the image
    Quartz.CGContextTranslateCTM(ctx, 0, SPRITE_SIZE)
    Quartz.CGContextScaleCTM(ctx, 1, -1)

    for row_idx, row in enumerate(grid):
        for col_idx, val in enumerate(row):
            if val == 0:
                continue
            r, g, b, a = palette[val]
            Quartz.CGContextSetRGBFillColor(ctx, r, g, b, a)
            x = col_idx * PIXEL_SCALE
            y = row_idx * PIXEL_SCALE
            Quartz.CGContextFillRect(ctx, ((x, y), (PIXEL_SCALE, PIXEL_SCALE)))

    return Quartz.CGBitmapContextCreateImage(ctx)


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
