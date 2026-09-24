"""Text format for pixel-art sprites.

Each sprite is a 16x16 block of characters, one per pixel. Rows may be
indented; blank lines around the block are ignored. Symbols map to palette
indices in claudy.config.PALETTE:

    .  transparent    #  body     e  eyes     b  blush     w  brown (wood)
    c  cream          u  blue     p  purple   g  gray      y  gold
"""

SYMBOLS = {
    ".": 0, "#": 1, "e": 2, "b": 3, "w": 4,
    "c": 5, "u": 6, "p": 7, "g": 8, "y": 9,
}


def sprite(text):
    """Parse a text sprite into a list of rows of palette indices."""
    rows = [line.strip() for line in text.strip().splitlines()]
    return [[SYMBOLS[ch] for ch in row] for row in rows]
