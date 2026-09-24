"""Render sprite grids to Cairo ImageSurfaces (Linux)."""

import cairo

from claudy.config import PIXEL_SCALE, SPRITE_SIZE


def render_sprite(grid, palette):
    """Render a 16x16 grid to an 80x80 Cairo ImageSurface."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, SPRITE_SIZE, SPRITE_SIZE)
    ctx = cairo.Context(surface)
    # No Y-flip needed: Cairo and grid both use top-left origin
    for row_idx, row in enumerate(grid):
        for col_idx, val in enumerate(row):
            if val == 0:
                continue
            ctx.set_source_rgba(*palette[val])
            ctx.rectangle(col_idx * PIXEL_SCALE, row_idx * PIXEL_SCALE,
                          PIXEL_SCALE, PIXEL_SCALE)
            ctx.fill()
    return surface
