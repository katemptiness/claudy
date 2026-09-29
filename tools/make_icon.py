"""Build Claudy's macOS app icon from its own sprites.

    pip install pillow
    python3 tools/make_icon.py

Writes assets/claudy.icns, which setup.py bundles into Claudy.app. The icns
is committed, so this only needs running when the icon should change.

From 32 px up, Claudy is painted at each size on its own, one square per art
pixel, rather than scaled down from one big image, so he stays a crisp grid
of square pixels wherever macOS shows the icon. Only at 16 px, where he
doesn't fit on the plate even at one screen pixel per art pixel, is a larger
icon scaled down.
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
# Pillow draws rounded rectangles without antialiasing, so the plate's mask is
# drawn this many times larger and shrunk, which smooths its corners
SUPERSAMPLE = 4
# Smaller plates are drawn at least this big and shrunk, so they keep a soft
# shadow that would be too faint to draw at their own size
SMALL = 128
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
    """Paint Claudy centered on the plate, one square per art pixel.

    Returns False, painting nothing, when he doesn't fit on the plate even at
    one screen pixel per art pixel.
    """
    left, top, right, bottom = ink
    cell = max(1, round(size * (PLATE / CANVAS) * COVERAGE / (right - left)))
    if (right - left) * cell > round(size * PLATE / CANVAS):
        return False
    x0 = (size - (right - left) * cell) / 2 - left * cell
    y0 = (size - (bottom - top) * cell) / 2 - top * cell + size * 0.012
    d = ImageDraw.Draw(icon)
    for y, row in enumerate(rows):
        for x, color in enumerate(row):
            if color:
                px, py = round(x0 + x * cell), round(y0 + y * cell)
                d.rectangle([px, py, px + cell - 1, py + cell - 1], fill=color)
    return True


def plate_mask(plate, size):
    """The plate's rounded square as an antialiased mask, `plate` px wide."""
    big = plate * SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, big - 1, big - 1],
        max(1, round(size * RADIUS / CANVAS * SUPERSAMPLE)), fill=255)
    return mask.resize((plate, plate), Image.BOX)


def background(size):
    """The plate and its shadow, without Claudy."""
    # A small plate is drawn a whole number of times larger and shrunk
    # exactly. Its width is measured at the real size, so there its straight
    # edges land on whole pixels, the same on every side. One big plate
    # scaled down to every size would put them between pixels instead, with
    # a soft rim on two sides.
    scale = -(-SMALL // size)             # at least SMALL px while drawing
    plate = round(size * PLATE / CANVAS) * scale
    size *= scale
    margin = (size - plate) / 2

    band = Image.new("RGBA", (plate, plate))
    d = ImageDraw.Draw(band)
    for y in range(plate):
        t = y / max(1, plate - 1)
        d.line([(0, y), (plate, y)],
               fill=tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)) + (255,))
    mask = plate_mask(plate, size)
    band.putalpha(mask)

    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 90), (round(margin), round(margin + size * 0.018)),
                 mask)
    icon.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(size * 0.021)))
    icon.alpha_composite(band, (round(margin), round(margin)))
    if scale > 1:
        icon = icon.resize((size // scale, size // scale), Image.BOX)
    return icon


def render(size, rows, ink):
    icon = background(size)
    if not draw_crab(icon, size, rows, ink):
        # 16 px: too small for square pixels, so shrink a bigger icon
        icon = render(SMALL, rows, ink).resize((size, size), Image.LANCZOS)
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
