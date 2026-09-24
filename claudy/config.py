"""Constants and configuration for Claudy."""

import os

# Where settings, memory and the error log live. CLAUDY_HOME overrides it
# (the test suite points it at a temp directory).
DATA_DIR = os.environ.get("CLAUDY_HOME") or os.path.expanduser("~/.claudy")

# Sprite grid
GRID = 16
PIXEL_SCALE = 5
SPRITE_SIZE = GRID * PIXEL_SCALE  # 80

# Claudy uses two windows of the same width, bottom edges aligned at rest:
# the small crab window (takes clicks, rises when Claudy hops) and a taller
# click-through overlay that stays on the Dock (shadows, gift, particles).
# Drawing coordinates have their origin at a window's top-left.
WINDOW_WIDTH = 200
WINDOW_HEIGHT = SPRITE_SIZE + 10  # 90, just the sprite + small margin
OVERLAY_HEIGHT = 300
# The sprite is centered horizontally, at the bottom of the crab window
SPRITE_X = (WINDOW_WIDTH - SPRITE_SIZE) // 2
SPRITE_Y = WINDOW_HEIGHT - SPRITE_SIZE

# The friend crab stands this far to the left of Claudy
FRIEND_OFFSET_X = -50

# Vertical offset to align crab feet with dock top
DOCK_Y_ADJUST = -15

# Dock walking confinement. Claudy estimates the Dock's width from its icon
# count (a user setting) so it only paces across the Dock instead of the whole
# screen. The Dock sits centered on screen, so the left/right walking edges
# fall symmetrically around the screen center. These are deliberate estimates —
# being a little narrow is fine (and preferred), since the user tunes the count.
DOCK_DEFAULT_TILE_SIZE = 48   # macOS default icon size when 'tilesize' is unset
DOCK_TILE_GAP = 10            # px of spacing added per icon to get the pitch
DOCK_EDGE_PADDING = 20        # px of Dock chrome at each end (rounded corners)
DOCK_WALK_MARGIN = 22         # keep the crab's center this far inside the edge


def _rgba(hex_color, alpha=1.0):
    """'#RRGGBB' -> (r, g, b, a) floats in 0..1."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


# Palette: sprite value -> RGBA (symbols in content/sprites/grid.py)
PALETTE = {
    0: (0.0, 0.0, 0.0, 0.0),  # transparent
    1: _rgba("#D77757"),      # body
    2: _rgba("#2D2D2D"),      # eyes
    3: _rgba("#F2A08A"),      # blush
    4: _rgba("#7B5B3A"),      # brown prop
    5: _rgba("#F5F0E8"),      # cream prop
    6: _rgba("#60A5FA"),      # blue prop
    7: _rgba("#A855F7"),      # purple
    8: _rgba("#8A8A9A"),      # gray
    9: _rgba("#FFD700"),      # gold
}

# Tones the shading pass (render/art.py) adds to the body and eyes
SHADES = {
    "highlight": _rgba("#E8987A"),
    "shadow": _rgba("#B35A3E"),
    "glint": _rgba("#FFFFFF"),
}

# The summoned friend is a blue crab
FRIEND_PALETTE = dict(PALETTE)
FRIEND_PALETTE[1] = _rgba("#57A0D7")  # body
FRIEND_PALETTE[3] = _rgba("#A0C8F0")  # blush
FRIEND_SHADES = dict(SHADES)
FRIEND_SHADES["highlight"] = _rgba("#82BCE6")
FRIEND_SHADES["shadow"] = _rgba("#3D7DB3")

# Timing
FPS = 60
TICK_INTERVAL = 1.0 / FPS
# Longest step the simulation takes at once (after a stall or system sleep)
MAX_TICK_MS = 50
