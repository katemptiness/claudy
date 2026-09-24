"""Small time-based motion effects. All times are in milliseconds and
heights in pixels above the crab's resting line.
"""

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


class Juggle:
    """Three balls, thrown in turn from the right claw over Claudy's head
    into the left one and passed back behind its back.

    Each ball's round takes three beats: flight, a moment in the left
    claw, the pass back, a moment in the right claw. A ball leaves the
    right claw on every beat.
    """

    BEAT_MS = 360
    REACH = 32       # px from Claudy's center to where a claw holds a ball
    PEAK = 32        # px the balls fly above the claws
    PASS_DIP = 8     # px the balls sink while going back behind Claudy
    FLIGHT = 0.66    # shares of a round...
    HOLD = 0.08      # ...in the left claw...
    PASS = 0.16      # ...going back; the rest waits in the right claw

    def __init__(self):
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt

    def balls(self):
        """(dx, height, index) per ball: dx toward the right claw, height of
        the ball's bottom above the claws."""
        for i in range(3):
            u = (self.timer / self.BEAT_MS - i) / 3 % 1  # ball i flies on beat i
            yield (*self._position(u), i)

    def _position(self, u):
        if u < self.FLIGHT:
            s = u / self.FLIGHT
            return self.REACH * (1 - 2 * s), 4 * self.PEAK * s * (1 - s)
        u -= self.FLIGHT
        if u < self.HOLD:
            return -self.REACH, 0.0
        u -= self.HOLD
        if u < self.PASS:
            s = u / self.PASS
            return (self.REACH * (2 * s - 1),
                    -self.PASS_DIP * math.sin(math.pi * s))
        return self.REACH, 0.0


class Fall:
    """Drop under gravity and bounce to rest on the ground (height 0)."""

    GRAVITY = 0.0015  # px/ms^2

    def __init__(self, height):
        self.height = max(0.0, height)
        self.vy = 0.0
        self.bounces = 0
        self.landed = False  # True on the update where Claudy touched down

    def update(self, dt):
        """Returns (height, done)."""
        self.vy += self.GRAVITY * dt
        self.height -= self.vy * dt
        self.landed = self.height <= 0
        if self.landed:
            self.height = 0.0
            self.vy *= -0.5  # bounce with damping
            self.bounces += 1
        done = self.bounces >= 3 or (self.bounces > 0 and abs(self.vy) < 0.05)
        return self.height, done
