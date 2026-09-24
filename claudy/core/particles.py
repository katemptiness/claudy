"""Particle system for visual effects.

Particle positions are in overlay-window pixels with y pointing up from the
window's bottom edge. Velocities are in px per 60 fps frame (the unit the
original prototype used), with negative vy meaning "rise".
"""

import random

FRAME_MS = 1000 / 60


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "lifetime", "age", "opacity",
                 "text", "size", "color")

    def __init__(self, x, y, vx, vy, lifetime, text, size, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.age = 0.0
        self.opacity = 1.0
        self.text = text
        self.size = size
        self.color = color  # (r, g, b) floats 0-1


def _spread(amount):
    return (random.random() - 0.5) * amount


RAINBOW = [
    (1.0, 0.0, 0.0), (1.0, 0.5, 0.0), (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.29, 0.0, 0.51), (0.56, 0.0, 1.0),
]
FLAME_COLORS = [(1.0, 0.6, 0.0), (1.0, 0.843, 0.0), (1.0, 0.4, 0.0)]

# kind -> () -> (text, size, color, vx, vy, lifetime_ms)
PARTICLE_TYPES = {
    "zzz": lambda: ("z", 11, (0.545, 0.643, 0.769), 0.3, -0.5, 2200),
    "sparkle": lambda: ("✦", random.randint(10, 16), (1.0, 0.843, 0.0),
                        _spread(0.5), -1.2, 800),
    "heart": lambda: ("♥", random.randint(10, 15), (1.0, 0.420, 0.541),
                      _spread(0.4), -1.0, 1200),
    "note": lambda: (random.choice(["♪", "♫", "♬"]), random.randint(11, 16),
                     (0.753, 0.518, 0.988), _spread(0.6), -0.8, 1000),
    "sweat": lambda: ("💧", 9, (0.376, 0.647, 0.980), 0.2, 0.8, 600),
    "question": lambda: ("❓", 14, (1.0, 0.843, 0.0), 0, -0.3, 1200),
    "exclaim": lambda: ("❗", 14, (1.0, 0.267, 0.267), 0, -0.3, 1000),
    "star": lambda: ("⭐", random.randint(10, 14), (1.0, 0.843, 0.0),
                     _spread(0.8), -1.5, 1000),
    "flower": lambda: (random.choice(["🌸", "🌼", "🌺"]), random.randint(10, 14),
                       (1.0, 0.753, 0.796), _spread(0.6), -1.0, 1100),
    "rainbow": lambda: ("✦", random.randint(10, 14), random.choice(RAINBOW),
                        _spread(0.3), -1.2, 1200),
    "butterfly": lambda: ("🦋", random.randint(12, 16), (0.659, 0.333, 0.969),
                          _spread(1.0), -0.5, 2000),
    "poof": lambda: ("💨", random.randint(12, 16), (0.7, 0.7, 0.7),
                     _spread(1.5), -0.5, 600),
    "code": lambda: (random.choice(["</>", "{ }", "01"]), 10,
                     (0.376, 0.647, 0.980), _spread(0.3), -0.8, 900),
    "page": lambda: ("📖", 12, (0.961, 0.941, 0.910), _spread(0.3), -0.4, 1500),
    "flame": lambda: (random.choice(["🔥", "✦", "•"]), random.randint(8, 12),
                      random.choice(FLAME_COLORS), _spread(0.3), -0.6, 1400),
}


class ParticleSystem:

    def __init__(self):
        self._particles = []

    def add(self, kind, x, y):
        """Spawn a particle of the given kind around (x, y)."""
        factory = PARTICLE_TYPES.get(kind)
        if not factory:
            return
        text, size, color, vx, vy, lifetime = factory()
        self._particles.append(Particle(
            x=x + _spread(30), y=y + random.random() * 10,
            vx=vx, vy=vy, lifetime=lifetime,
            text=text, size=size, color=color))

    def update(self, dt):
        frames = dt / FRAME_MS
        alive = []
        for p in self._particles:
            p.age += dt
            if p.age > p.lifetime:
                continue
            p.x += p.vx * frames
            p.y -= p.vy * frames
            p.opacity = max(0.0, 1.0 - p.age / p.lifetime)
            alive.append(p)
        self._particles = alive

    def get_active(self):
        return self._particles
