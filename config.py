"""Constants and configuration for Claudy."""

# Sprite grid
GRID = 16
PIXEL_SCALE = 5
SPRITE_SIZE = GRID * PIXEL_SCALE  # 80

# Window size (larger than sprite to allow particles above)
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 300
# Sprite is centered horizontally, at the bottom of the window
SPRITE_OFFSET_X = (WINDOW_WIDTH - SPRITE_SIZE) // 2
SPRITE_OFFSET_Y = 0  # bottom of window

# Vertical offset to align crab feet with dock top
DOCK_Y_ADJUST = -15

# Palette: index -> (r, g, b, a) as floats 0.0-1.0
PALETTE = {
    0: (0.0, 0.0, 0.0, 0.0),        # transparent
    1: (0.843, 0.467, 0.341, 1.0),   # body #D77757
    2: (0.176, 0.176, 0.176, 1.0),   # eyes #2D2D2D
    3: (0.941, 0.753, 0.627, 1.0),   # blush #F0C0A0
    4: (0.482, 0.357, 0.227, 1.0),   # brown prop #7B5B3A
    5: (0.961, 0.941, 0.910, 1.0),   # cream prop #F5F0E8
    6: (0.376, 0.647, 0.980, 1.0),   # blue prop #60A5FA
    7: (0.659, 0.333, 0.969, 1.0),   # purple #A855F7
    8: (0.541, 0.541, 0.604, 1.0),   # gray #8A8A9A
    9: (1.0, 0.843, 0.0, 1.0),       # gold #FFD700
}

# Friend palette — blue/teal crab
FRIEND_PALETTE = dict(PALETTE)
FRIEND_PALETTE[1] = (0.341, 0.627, 0.843, 1.0)   # body: blue #57A0D7
FRIEND_PALETTE[3] = (0.627, 0.784, 0.941, 1.0)    # blush: light blue #A0C8F0

# Timing
FPS = 60
TICK_INTERVAL = 1.0 / FPS
