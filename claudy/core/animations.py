"""Small time-based motion effects. All times are in milliseconds and
heights in pixels above the crab's resting line."""

import math
import random


class Bounce:
    """A few quick hops in place, following |sin|."""

    def __init__(self, height=10, hops=3, speed=0.012):
        self.height = height
        self.speed = speed
        self.end = math.pi * hops
        self.phase = 0.0

    def update(self, dt):
        """Returns (height, done)."""
        self.phase += dt * self.speed
        if self.phase >= self.end:
            return 0.0, True
        return abs(math.sin(self.phase)) * self.height, False


class Shake:
    """Random horizontal jitter for a while."""

    def __init__(self, duration=500, jitter=6):
        self.remaining = duration
        self.jitter = jitter

    def update(self, dt):
        """Returns (dx, done)."""
        self.remaining -= dt
        if self.remaining <= 0:
            return 0.0, True
        return (random.random() - 0.5) * self.jitter, False


class Hop:
    """Repeating parabolic hops (used while playing)."""

    def __init__(self, height=12, duration=600):
        self.height = height
        self.duration = duration
        self.timer = 0.0

    def update(self, dt):
        """Returns (height, landed) — landed is True once per hop."""
        self.timer += dt
        t = min(self.timer / self.duration, 1.0)
        if t >= 1.0:
            self.timer = 0.0
            return 0.0, True
        return 4 * self.height * t * (1 - t), False


class Fall:
    """Drop under gravity and bounce to rest on the ground (height 0)."""

    GRAVITY = 0.0015  # px/ms^2

    def __init__(self, height):
        self.height = max(0.0, height)
        self.vy = 0.0
        self.bounces = 0

    def update(self, dt):
        """Returns (height, done)."""
        self.vy += self.GRAVITY * dt
        self.height -= self.vy * dt
        if self.height <= 0:
            self.height = 0.0
            self.vy *= -0.5  # bounce with damping
            self.bounces += 1
        done = self.bounces >= 3 or (self.bounces > 0 and abs(self.vy) < 0.05)
        return self.height, done
