"""Render sprite grids to CGImages via CGBitmapContext (macOS)."""

import Quartz

from claudy.config import PIXEL_SCALE, SPRITE_SIZE


def render_sprite(grid, palette):
    """Render a 16x16 grid to an 80x80 CGImage."""
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
            Quartz.CGContextSetRGBFillColor(ctx, *palette[val])
            Quartz.CGContextFillRect(
                ctx, ((col_idx * PIXEL_SCALE, row_idx * PIXEL_SCALE),
                      (PIXEL_SCALE, PIXEL_SCALE)))

    return Quartz.CGBitmapContextCreateImage(ctx)
