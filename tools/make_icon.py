"""Build Claudy's macOS app icon from its own sprites.

    pip install pillow
    python3 tools/make_icon.py

Writes assets/claudy.icns, which setup.py bundles into Claudy.app. The icns
is committed, so this only needs running when the icon should change.

Every size is drawn on its own rather than scaled down from one big image, so
Claudy stays a crisp grid of square pixels wherever macOS shows the icon.
"""

import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claudy.render import art  # noqa: E402

SPRITE = "idle"
# Claudy sits on a rounded square, the way macOS icons have looked since
# Big Sur: the plate covers 824 of a 1024 canvas, with a soft shadow under it.
CANVAS = 1024
PLATE = 824
RADIUS = PLATE * 0.2237
COVERAGE = 0.62          # how much of the plate's width Claudy's art spans
TOP = (0x3C, 0x8A, 0x9B)   # deep sea, light at the top
BOTTOM = (0x15, 0x44, 0x53)
# The sizes an .iconset needs, as (pixels, file name)
SIZES = [(16, "16x16"), (32, "16x16@2x"), (32, "32x32"), (64, "32x32@2x"),
         (128, "128x128"), (256, "128x128@2x"), (256, "256x256"),
         (512, "256x256@2x"), (512, "512x512"), (1024, "512x512@2x")]


def sprite_pixels():
    """Claudy's art as (rows, ink box), with the empty margin measured off."""
    image = art.build(art.sprite_key(SPRITE))
    rows = [[tuple(round(c * 255) for c in color) if color else None
             for color in row] for row in image.rows]
    xs = [x for row in rows for x, color in enumerate(row) if color]
    ys = [y for y, row in enumerate(rows) for color in row if color]
    return rows, (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def draw_crab(icon, size, rows, ink):
    """Paint Claudy centered on the plate, one square per art pixel."""
    left, top, right, bottom = ink
    cell = size * (PLATE / CANVAS) * COVERAGE / (right - left)
    if cell < 2:
        return False                      # too small to stay square; scale instead
    cell = round(cell)
    x0 = (size - (right - left) * cell) / 2 - left * cell
    y0 = (size - (bottom - top) * cell) / 2 - top * cell + size * 0.012
    d = ImageDraw.Draw(icon)
    for y, row in enumerate(rows):
        for x, color in enumerate(row):
            if color:
                px, py = round(x0 + x * cell), round(y0 + y * cell)
                d.rectangle([px, py, px + cell - 1, py + cell - 1], fill=color)
    return True


def render(size, rows, ink):
    plate = round(size * PLATE / CANVAS)
    margin = (size - plate) / 2
    radius = max(1, round(size * RADIUS / CANVAS))

    band = Image.new("RGBA", (plate, plate))
    d = ImageDraw.Draw(band)
    for y in range(plate):
        t = y / max(1, plate - 1)
        d.line([(0, y), (plate, y)],
               fill=tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)) + (255,))
    mask = Image.new("L", (plate, plate), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, plate - 1, plate - 1],
                                           radius, fill=255)
    band.putalpha(mask)

    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if size >= 128:                       # the shadow only reads at larger sizes
        shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shadow.paste((0, 0, 0, 90), (round(margin), round(margin + size * 0.018)),
                     mask)
        icon.alpha_composite(shadow.filter(
            ImageFilter.GaussianBlur(size * 0.021)))
    icon.alpha_composite(band, (round(margin), round(margin)))

    if not draw_crab(icon, size, rows, ink):
        big = render(128, rows, ink)
        icon = big.resize((size, size), Image.LANCZOS)
    return icon


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "claudy.icns")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows, ink = sprite_pixels()
    with tempfile.TemporaryDirectory() as tmp:
        iconset = os.path.join(tmp, "claudy.iconset")
        os.makedirs(iconset)
        for size, name in SIZES:
            render(size, rows, ink).save(os.path.join(iconset, f"icon_{name}.png"))
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out], check=True)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
