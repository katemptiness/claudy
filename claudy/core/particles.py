"""Particles: little pixel-art bits that float, drift and fade.

Positions are in ground-overlay pixels: x from the left edge, y as height
above the bottom edge. Velocities are px/s (positive vy rises), gravity is
px/s² pulling down. Each particle picks one of its kind's images (see
content/sprites/particles.py).
"""

import math
import random
from dataclasses import dataclass

from claudy.content.sprites.particles import RAINBOW

FADE_IN_MS = 100
FADE_OUT_SHARE = 0.35   # the last part of a particle's life fades out
MAX_PARTICLES = 80


@dataclass(frozen=True)
class Kind:
    images: tuple               # art names; one is picked per particle
    life_ms: tuple = (1000, 1200)
    vx: tuple = (-15, 15)
    vy: tuple = (45, 65)
    gravity: float = 0.0
    drag: float = 0.0           # share of speed lost per second
    sway: float = 0.0           # px of side-to-side drift...
    sway_ms: float = 1200       # ...over this period
    spread: float = 30          # spawn area width
    at_feet: bool = False       # spawn at Claudy's feet instead of head
    offset_x: float = 0         # spawn this far in front of Claudy...
    offset_y: float = 0         # ...and this much higher
    flap_ms: float = 0          # cycle through the images at this pace
    tints: tuple = ()           # recolor variants to pick from


KINDS = {
    "zzz": Kind(("z_big", "z_small"), (2000, 2400), vx=(10, 22), vy=(22, 32),
                sway=4, sway_ms=1600, spread=16, offset_x=12),
    "sparkle": Kind(("sparkle", "sparkle_small"), (650, 900),
                    vx=(-25, 25), vy=(55, 85)),
    "heart": Kind(("heart",), (1100, 1300), vy=(45, 65), sway=5, sway_ms=900),
    "note": Kind(("note", "note_beamed"), (1000, 1200), vx=(-20, 20),
                 vy=(40, 60), sway=6, sway_ms=800),
    "sweat": Kind(("sweat",), (550, 700), vx=(8, 20), vy=(-5, 15),
                  gravity=220, spread=20, offset_x=14),
    "question": Kind(("question",), (1200, 1200), vx=(0, 0), vy=(35, 35),
                     drag=2.5, spread=6),
    "exclaim": Kind(("exclaim",), (1000, 1000), vx=(0, 0), vy=(35, 35),
                    drag=2.5, spread=6),
    "star": Kind(("star",), (900, 1100), vx=(-30, 30), vy=(75, 100), drag=0.7),
    "flower": Kind(("flower_pink", "flower_yellow", "flower_red"), (1100, 1300),
                   vx=(-20, 20), vy=(45, 65), sway=5),
    "rainbow": Kind(("sparkle",), (1100, 1300), vx=(-12, 12), vy=(60, 80),
                    tints=tuple(RAINBOW)),
    "butterfly": Kind(("butterfly_open", "butterfly_closed"), (2000, 2200),
                      vx=(-30, 30), vy=(25, 40), sway=10, sway_ms=1400,
                      flap_ms=140),
    "poof": Kind(("poof",), (500, 650), vx=(-50, 50), vy=(15, 40), drag=3,
                 spread=40),
    "dust": Kind(("dust",), (350, 450), vx=(-45, 45), vy=(8, 22), drag=4,
                 gravity=40, spread=44, at_feet=True),
    "code": Kind(("code_tag", "code_braces", "code_bits"), (900, 900),
                 vx=(-10, 10), vy=(40, 55), spread=12, at_feet=True,
                 offset_x=50, offset_y=30),   # from the laptop screen
    "flame": Kind(("flame", "ember", "spark"), (1100, 1500), vx=(-8, 8),
                  vy=(28, 45), sway=3, sway_ms=500, spread=10, at_feet=True,
                  offset_x=47, offset_y=30),
}


class Particle:
    __slots__ = ("kind", "image", "tint", "x", "y", "vx", "vy", "age",
                 "lifetime", "sway_phase", "opacity")

    def __init__(self, kind, x, y):
        k = KINDS[kind]
        self.kind = k
        self.image = random.choice(k.images)
        self.tint = random.choice(k.tints) if k.tints else None
        self.x = x + (random.random() - 0.5) * k.spread
        self.y = y + random.random() * 10
        self.vx = random.uniform(*k.vx)
        self.vy = random.uniform(*k.vy)
        self.age = 0.0
        self.lifetime = random.uniform(*k.life_ms)
        self.sway_phase = random.random() * 2 * math.pi
        self.opacity = 0.0

    def update(self, dt):
        k = self.kind
        self.age += dt
        s = dt / 1000
        if k.drag:
            slow = max(0.0, 1 - k.drag * s)
            self.vx *= slow
            self.vy *= slow
        self.vy -= k.gravity * s
        self.x += self.vx * s
        self.y += self.vy * s

        fade_in = min(1.0, self.age / FADE_IN_MS)
        fade_out = min(1.0, (self.lifetime - self.age)
                       / (self.lifetime * FADE_OUT_SHARE))
        self.opacity = max(0.0, min(fade_in, fade_out))

    @property
    def alive(self):
        return self.age < self.lifetime

    @property
    def draw_x(self):
        """x including the side-to-side sway."""
        k = self.kind
        if not k.sway:
            return self.x
        angle = 2 * math.pi * self.age / k.sway_ms + self.sway_phase
        return self.x + k.sway * math.sin(angle)

    @property
    def frame(self):
        """The image to show right now (flapping kinds cycle images)."""
        k = self.kind
        if not k.flap_ms:
            return self.image
        return k.images[int(self.age / k.flap_ms) % len(k.images)]


class ParticleSystem:

    def __init__(self):
        self._particles = []

    def add(self, kind, x, head_y, feet_y=0, facing_right=True):
        """Spawn a particle of `kind` around Claudy (x = its center)."""
        k = KINDS.get(kind)
        if not k or len(self._particles) >= MAX_PARTICLES:
            return
        x += k.offset_x if facing_right else -k.offset_x
        y = (feet_y if k.at_feet else head_y) + k.offset_y
        self._particles.append(Particle(kind, x, y))

    def update(self, dt):
        for p in self._particles:
            p.update(dt)
        self._particles = [p for p in self._particles if p.alive]

    def get_active(self):
        return self._particles
