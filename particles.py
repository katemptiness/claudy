"""Particle system for visual effects."""

import random
import time


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "lifetime", "born", "opacity",
                 "text", "size", "color")

    def __init__(self, x, y, vx, vy, lifetime, text, size, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.born = time.time() * 1000
        self.opacity = 1.0
        self.text = text
        self.size = size
        self.color = color  # (r, g, b) floats 0-1


# Particle type definitions
def _make(ptype, bx, by):
    """Create a particle of the given type at base position."""
    spread_x = (random.random() - 0.5) * 30
    spread_y = random.random() * 10

    defs = {
        "zzz": ("z", 11, (0.545, 0.643, 0.769),
                0.3, -0.5, 2200),
        "sparkle": ("✦", random.randint(10, 16), (1.0, 0.843, 0.0),
                    (random.random() - 0.5) * 0.5, -1.2, 800),
        "heart": ("♥", random.randint(10, 15), (1.0, 0.420, 0.541),
                  (random.random() - 0.5) * 0.4, -1.0, 1200),
        "note": (random.choice(["♪", "♫", "♬"]),
                 random.randint(11, 16), (0.753, 0.518, 0.988),
                 (random.random() - 0.5) * 0.6, -0.8, 1000),
        "sweat": ("💧", 9, (0.376, 0.647, 0.980),
                  0.2, 0.8, 600),
        "question": ("❓", 14, (1.0, 0.843, 0.0),
                     0, -0.3, 1200),
        "exclaim": ("❗", 14, (1.0, 0.267, 0.267),
                    0, -0.3, 1000),
        "star": ("⭐", random.randint(10, 14), (1.0, 0.843, 0.0),
                 (random.random() - 0.5) * 0.8, -1.5, 1000),
        "flower": (random.choice(["🌸", "🌼", "🌺"]),
                   random.randint(10, 14), (1.0, 0.753, 0.796),
                   (random.random() - 0.5) * 0.6, -1.0, 1100),
        "rainbow": ("✦", random.randint(10, 14),
                    random.choice([
                        (1.0, 0.0, 0.0), (1.0, 0.5, 0.0), (1.0, 1.0, 0.0),
                        (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.29, 0.0, 0.51),
                        (0.56, 0.0, 1.0),
                    ]),
                    (random.random() - 0.5) * 0.3, -1.2, 1200),
        "butterfly": ("🦋", random.randint(12, 16), (0.659, 0.333, 0.969),
                      (random.random() - 0.5) * 1.0, -0.5, 2000),
        "poof": ("💨", random.randint(12, 16), (0.7, 0.7, 0.7),
                 (random.random() - 0.5) * 1.5, -0.5, 600),
        "code": (random.choice(["</>", "{ }", "01"]),
                 10, (0.376, 0.647, 0.980),
                 (random.random() - 0.5) * 0.3, -0.8, 900),
        "page": ("📖", 12, (0.961, 0.941, 0.910),
                 (random.random() - 0.5) * 0.3, -0.4, 1500),
        "flame": (random.choice(["🔥", "✦", "•"]),
                  random.randint(8, 12),
                  random.choice([
                      (1.0, 0.6, 0.0),    # orange
                      (1.0, 0.843, 0.0),   # gold
                      (1.0, 0.4, 0.0),     # deep orange
                  ]),
                  (random.random() - 0.5) * 0.3, -0.6, 1400),
    }

    if ptype not in defs:
        return None

    text, size, color, vx, vy, life = defs[ptype]
    return Particle(
        x=bx + spread_x,
        y=by + spread_y,
        vx=vx, vy=vy,
        lifetime=life,
        text=text, size=size, color=color,
    )


class ParticleSystem:

    def __init__(self):
        self._particles = []

    def add(self, ptype, bx, by):
        p = _make(ptype, bx, by)
        if p:
            self._particles.append(p)

    def update(self, dt):
        now = time.time() * 1000
        alive = []
        for p in self._particles:
            age = now - p.born
            if age > p.lifetime:
                continue
            p.x += p.vx
            p.y += p.vy
            p.opacity = max(0, 1.0 - age / p.lifetime)
            alive.append(p)
        self._particles = alive

    def get_active(self):
        return self._particles
