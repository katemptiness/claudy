"""Pixel art as images: every picture Claudy draws is built here.

An image is identified by a hashable key; `build(key)` turns it into a
PixelImage (rows of RGBA colors, None for transparent) that backends
convert to a native image once and cache (see canvas.ImageCache).
"""

from dataclasses import dataclass
from functools import lru_cache

from claudy.config import (
    FRIEND_PALETTE, FRIEND_SHADES, PALETTE, PIXEL_SCALE, SHADES, hex_rgba,
)
from claudy.content.sprites import SPRITES
from claudy.content.sprites.particles import (
    PARTICLE_ART, PARTICLE_COLORS, PARTICLE_SCALE,
)


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


POSES = ("normal", "squash", "stretch")


def sprite_key(name, friend=False, flip=False, pose="normal"):
    """Key for a character sprite, optionally recolored, mirrored, or
    squashed/stretched (see posed())."""
    return ("sprite", name if name in SPRITES else "idle", friend, flip, pose)


def particle_key(name, tint=None):
    """Key for a particle image; `tint` ('#RRGGBB') recolors its gold."""
    return ("particle", name, tint)


@lru_cache(maxsize=None)
def build(key):
    kind = key[0]
    if kind == "sprite":
        return _build_sprite(*key[1:])
    if kind == "particle":
        return _build_particle(*key[1:])
    raise KeyError(key)


def _mix(color, other, amount):
    return tuple(a + (b - a) * amount for a, b in zip(color, other))


def _build_particle(name, tint):
    colors = {sym: hex_rgba(hex_color) for sym, hex_color in PARTICLE_COLORS.items()}
    if tint:
        colors["y"] = hex_rgba(tint)
        colors["Y"] = _mix(colors["y"], (1, 1, 1, 1), 0.6)
    lines = [line.strip() for line in PARTICLE_ART[name].strip().splitlines()]
    rows = tuple(tuple(colors[ch] if ch != "." else None for ch in line)
                 for line in lines)
    return PixelImage(rows, PARTICLE_SCALE)


def _build_sprite(name, friend, flip, pose):
    grid = posed(SPRITES[name], pose)
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


def _wide_body_rows(grid):
    """Rows where the body is more than single pixels (not legs or a
    raised claw)."""
    rows = []
    for r, row in enumerate(grid):
        cols = [c for c, v in enumerate(row) if v == BODY]
        if any(c + 1 in cols for c in cols):
            rows.append(r)
    return rows


def posed(grid, pose):
    """Squash or stretch a sprite by one pixel row, pixel-perfectly.

    The row just under the top of the body is removed ("squash": everything
    above drops by a pixel, feet stay put) or doubled ("stretch": everything
    above rises by a pixel). Grids come back unchanged when there's no room.
    """
    wide = _wide_body_rows(grid)
    if pose == "normal" or len(wide) < 3:
        return grid
    cut = wide[0] + 1
    rows = [list(row) for row in grid]
    empty = [0] * len(rows[0])
    if pose == "squash":
        del rows[cut]
        rows.insert(0, empty)
    elif pose == "stretch":
        if any(rows[0]):
            return grid
        rows.insert(cut, list(rows[cut]))
        del rows[0]
    return rows


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
