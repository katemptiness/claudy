"""Text format for pixel-art sprites.

Each sprite is a block of characters, one per pixel: 16 rows, and 16
columns — or wider, in steps of two, when a prop needs the room (Claudy
stays in the middle 16). Rows may be indented; blank lines around the block
are ignored. Symbols map to palette indices in claudy.config.PALETTE:

    .  transparent    #  body     e  eyes     b  blush     w  brown (wood)
    c  cream          u  blue     p  purple   g  gray      y  gold
    s  sand           S  sand shade           o  flame orange
    r  red            n  green    k  shell pink
    d  dark metal     l  light metal
    +  Claudy's side face, for poses turned three-quarters toward a prop
"""

SYMBOLS = {
    ".": 0, "#": 1, "e": 2, "b": 3, "w": 4,
    "c": 5, "u": 6, "p": 7, "g": 8, "y": 9,
    "s": 10, "S": 11, "o": 12, "r": 13, "n": 14,
    "k": 15, "d": 16, "l": 17, "+": 18,
}


def sprite(text):
    """Parse a text sprite into a list of rows of palette indices."""
    rows = [line.strip() for line in text.strip().splitlines()]
    return [[SYMBOLS[ch] for ch in row] for row in rows]
