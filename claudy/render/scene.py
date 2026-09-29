"""What Claudy's windows show, painted through a backend's Canvas.

Four windows, all drawn here:
- the crab window: Claudy, the summoned friend, the toy;
- the ground overlay: shadows, the gift on the Dock, particles, dreams;
- the star window: the one star Claudy named after the user;
- the speech bubble, sized to its text by bubble_layout().
"""

import zlib
from dataclasses import dataclass

from claudy.config import (
    FRIEND_OFFSET_X, OVERLAY_HEIGHT, PIXEL_SCALE, SPRITE_SIZE, SPRITE_X,
    SPRITE_Y, STAR_SPREAD, STAR_WINDOW, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from claudy.content.sprites.items import (
    DREAM_CLOUD, GIFT_ART, STAR_TWINKLE, TOY,
)
from claudy.content.sprites.particles import JUGGLE_BALL_COLORS
from claudy.render import art
from claudy.render.canvas import Canvas

CLAW_TOP = SPRITE_Y + 9 * PIXEL_SCALE  # where juggled balls rest

# The ground line in the crab window: every sprite leaves its last two rows
# empty, so Claudy's feet end here. Whatever stands beside him stands on it.
FEET_Y = SPRITE_Y + 14 * PIXEL_SCALE
GROUND_Y = OVERLAY_HEIGHT - WINDOW_HEIGHT + FEET_Y   # the same, in the overlay

# Shadows lie on the ground just under the feet, as one row of art pixels
SHADOW_Y = GROUND_Y + 1
SHADOW_UNITS = 10       # width of the dark middle, in art pixels
SHADOW_ALPHA = 0.22
SHADOW_FADE_HEIGHT = 80  # px above ground where the shadow is smallest

# The gift stands on the ground a fixed step clear of Claudy, pulled back
# only when a wide picture would otherwise run off the edge of the window
GIFT_X = SPRITE_X + SPRITE_SIZE + 5

# The toy is tucked against Claudy's side and drawn behind him, so his claw
# lies across it: something he sleeps with, not a separate object
TOY_X = SPRITE_X + SPRITE_SIZE - 3 * PIXEL_SCALE

# A dream floats above the sleeping Claudy in a cloud of its own (an item
# picture, so it is drawn with one opacity throughout). The cloud hangs on
# Claudy's own pixel grid, a little off to one side, and its trail of bubbles
# ends just above his head; the picture goes in the middle of the cloud.
DREAM_CLOUD_X = SPRITE_X
DREAM_CLOUD_Y = 120
DREAM_CENTER = (10.5, 8)    # art pixels into the cloud
CLOUD_ALPHA = 0.92

# The named star twinkles through a few pictures (STAR_TWINKLE) rather than
# fading: the backends redraw a window whenever its drawing calls change, and
# a star fading continuously would wake an always-on-top window 60 times a
# second to move nothing.
STAR_TWINKLE_MS = sum(ms for _, ms in STAR_TWINKLE)

# Speech bubble
BUBBLE_UNIT = 3          # its art pixel, a little finer than Claudy's
BUBBLE_FONT = 12
BUBBLE_MAX_TEXT_WIDTH = 220
BUBBLE_PAD_X = 9
BUBBLE_PAD_Y = 5
BUBBLE_TAIL_UNITS = 4
BUBBLE_FILL = (1.0, 0.973, 0.933, 1.0)   # #FFF8EE
BUBBLE_INK = (0.227, 0.165, 0.141, 1.0)  # #3A2A24
# The tail's tip reaches this far down into the crab window's empty top
BUBBLE_OVERLAP = 8


@dataclass(frozen=True)
class BubbleLayout:
    text: str
    lines: tuple         # wrapped lines
    line_widths: tuple
    line_height: float
    width: int           # whole window, tail included
    height: int
    box_height: int


def star_offset_x(name):
    """Where the named star hangs, in pixels from the center of the screen.

    Taken from the name so that it is always the same star in the same place,
    and so that two people's stars are not in the same spot.
    """
    seed = zlib.crc32(name.encode("utf-8"))
    return seed % (2 * STAR_SPREAD + 1) - STAR_SPREAD


def _snap(value, unit):
    """Round up to a whole number of units."""
    return int(-(-value // unit) * unit)


class _Recorder(Canvas):
    """Collects a window's drawing calls so two frames can be compared."""

    def __init__(self):
        self.calls = []

    def image(self, key, x, y, alpha=1.0):
        self.calls.append(("image", key, x, y, alpha))

    def rect(self, x, y, w, h, rgba):
        self.calls.append(("rect", x, y, w, h, rgba))

    def text(self, text, x, y, size, rgba, bold=False):
        self.calls.append(("text", text, x, y, size, rgba, bold))


class Scene:

    def __init__(self, controller):
        self.ctl = controller
        self._bubble = None
        self._painted = {}

    # ---- Redrawing ----

    def crab_changed(self):
        """Would the crab window draw differently than when last asked?"""
        return self._changed("crab", self.paint_crab)

    def ground_changed(self):
        """Would the ground overlay draw differently than when last asked?"""
        return self._changed("ground", self.paint_ground)

    def star_changed(self):
        """Would the star window draw differently than when last asked?"""
        return self._changed("star", self.paint_star)

    def _changed(self, window, paint):
        """Claudy holds still most of the time, and repainting a transparent
        always-on-top window costs the same whether or not anything moved, so
        backends ask this before marking a view dirty."""
        recorder = _Recorder()
        paint(recorder)
        if self._painted.get(window) == recorder.calls:
            return False
        self._painted[window] = recorder.calls
        return True

    # ---- Crab window ----

    def paint_crab(self, canvas):
        view = self.ctl.view
        if view["friend_visible"]:
            canvas.image(art.sprite_key(view["friend_sprite"], friend=True),
                         SPRITE_X + FRIEND_OFFSET_X, SPRITE_Y)
        # Juggled balls fly behind Claudy, never across its face
        center = WINDOW_WIDTH / 2 + view["shake_dx"]
        side = 1 if view["facing_right"] else -1
        for dx, height, index in view["juggle"]:
            ball = art.particle_key("ball", JUGGLE_BALL_COLORS[index])
            size = art.build(ball).width
            canvas.image(ball, round(center + side * dx - size / 2),
                         round(CLAW_TOP - height - size))
        if view["show_toy"]:
            toy = art.item_key(TOY)
            canvas.image(toy, TOY_X, FEET_Y - art.build(toy).height)
        key = art.sprite_key(view["sprite"], flip=not view["facing_right"])
        # Sprites wider than 16 (props) keep Claudy in their middle
        x = (WINDOW_WIDTH - art.build(key).width) / 2
        canvas.image(key, round(x + view["shake_dx"]), SPRITE_Y)

    # ---- Ground overlay ----

    def paint_ground(self, canvas):
        view = self.ctl.view
        height = max(0.0, view["y_offset"])
        if view["friend_visible"]:
            self._shadow(canvas, WINDOW_WIDTH / 2 + FRIEND_OFFSET_X, height)
        self._shadow(canvas, WINDOW_WIDTH / 2, height)
        if view["show_toy"]:
            self._item_shadow(canvas, TOY_X, art.build(art.item_key(TOY)))

        if self.ctl.gift_emoji:
            self._gift(canvas, self.ctl.gift_emoji)

        # Particles go behind a dream: the zzz already in the air when one
        # surfaces drift on behind its cloud instead of across the picture
        for p in self.ctl.particles.get_active():
            key = art.particle_key(p.frame, p.tint)
            image = art.build(key)
            canvas.image(key, round(p.draw_x - image.width / 2),
                         round(OVERLAY_HEIGHT - p.y - image.height / 2),
                         p.opacity)

        if self.ctl.dream:
            self._dream(canvas, *self.ctl.dream)

    @staticmethod
    def _dream(canvas, picture, alpha):
        """What Claudy is dreaming about, fading in and out above him."""
        canvas.image(art.item_key(DREAM_CLOUD), DREAM_CLOUD_X, DREAM_CLOUD_Y,
                     alpha * CLOUD_ALPHA)
        key = art.item_key(picture)
        image = art.build(key)
        u = PIXEL_SCALE
        cx, cy = DREAM_CENTER
        # Whole art pixels, so the picture stays on the cloud's grid (and
        # Claudy's); an odd-sized picture sits half a pixel off center
        canvas.image(key, DREAM_CLOUD_X + int(cx - image.width / u / 2) * u,
                     DREAM_CLOUD_Y + int(cy - image.height / u / 2 + 0.5) * u,
                     alpha)

    @staticmethod
    def _gift(canvas, emoji):
        """The gift waiting on the Dock, standing beside Claudy.

        Every gift Claudy offers has a picture (a content test makes sure).
        """
        key = art.item_key(GIFT_ART[emoji])
        image = art.build(key)
        # On Claudy's pixel grid, pulled back as far as a wide picture needs
        x = min(GIFT_X, SPRITE_X + (WINDOW_WIDTH - SPRITE_X - image.width)
                // PIXEL_SCALE * PIXEL_SCALE)
        Scene._item_shadow(canvas, x, image)
        canvas.image(key, x, GROUND_Y - image.height)

    @staticmethod
    def _item_shadow(canvas, x, image):
        """The shadow under something standing on the ground at `x`, a
        little narrower than its picture, like Claudy's under him."""
        Scene._shadow(canvas, x + image.width / 2, 0,
                      max(2, image.width // PIXEL_SCALE - 4))

    @staticmethod
    def _shadow(canvas, center_x, height, units=SHADOW_UNITS):
        """A pixel shadow that shrinks and fades as Claudy leaves the ground."""
        closeness = max(0.3, 1 - height / SHADOW_FADE_HEIGHT)
        units = max(2, round(units * closeness))
        alpha = SHADOW_ALPHA * (0.4 + 0.6 * closeness)
        w = units * PIXEL_SCALE
        x = round(center_x - w / 2)
        canvas.rect(x, SHADOW_Y, w, PIXEL_SCALE, (0, 0, 0, alpha))
        edge = (0, 0, 0, alpha / 2)
        canvas.rect(x - PIXEL_SCALE, SHADOW_Y, PIXEL_SCALE, PIXEL_SCALE, edge)
        canvas.rect(x + w, SHADOW_Y, PIXEL_SCALE, PIXEL_SCALE, edge)

    # ---- Star window ----

    def paint_star(self, canvas):
        """The star Claudy named, twinkling in its own small window.

        Nothing is drawn while Controller.star is None (no star yet, or
        daylight); backends hide the window then, and this keeps the two in
        step if one is ever slower than the other.
        """
        if self.ctl.star is None:
            return
        t = self.ctl.clock_ms % STAR_TWINKLE_MS
        for picture, ms in STAR_TWINKLE:
            if t < ms:
                break
            t -= ms
        key = art.item_key(picture)
        image = art.build(key)
        canvas.image(key, (STAR_WINDOW - image.width) // 2,
                     (STAR_WINDOW - image.height) // 2)

    # ---- Speech bubble ----

    def bubble_layout(self, canvas):
        """Size and line breaks for the current speech text (cached)."""
        text = self.ctl.speech.text
        if self._bubble and self._bubble.text == text:
            return self._bubble

        def width(s):
            return canvas.measure(s, BUBBLE_FONT, bold=True)[0]

        lines = []
        for word in text.split(" "):
            if lines and width(lines[-1] + " " + word) <= BUBBLE_MAX_TEXT_WIDTH:
                lines[-1] += " " + word
            else:
                lines.append(word)
        widths = tuple(width(line) for line in lines)
        line_height = canvas.measure("Ag", BUBBLE_FONT, bold=True)[1]

        u = BUBBLE_UNIT
        box_w = _snap(max(widths) + 2 * (BUBBLE_PAD_X + u), u)
        box_w = max(box_w, 12 * u)
        box_h = _snap(len(lines) * line_height + 2 * (BUBBLE_PAD_Y + u), u)
        self._bubble = BubbleLayout(
            text=text, lines=tuple(lines), line_widths=widths,
            line_height=line_height, width=box_w,
            height=box_h + BUBBLE_TAIL_UNITS * u, box_height=box_h)
        return self._bubble

    def paint_bubble(self, canvas):
        layout = self.bubble_layout(canvas)
        u = BUBBLE_UNIT
        w, h = layout.width, layout.box_height

        # Box with stepped corners: ink outline, then the fill inset by a unit
        for inset, color in ((0, BUBBLE_INK), (u, BUBBLE_FILL)):
            canvas.rect(2 * u, inset, w - 4 * u, h - 2 * inset, color)
            canvas.rect(u + inset, u, w - 2 * u - 2 * inset, h - 2 * u, color)
            canvas.rect(inset, 2 * u, w - 2 * inset, h - 4 * u, color)

        # Tail, centered, opening into the box: rows of (units below the
        # box bottom, left edge, width, rows tall), each outlined in ink
        tx = _snap((w - 7 * u) / 2, u)
        for dy, left, width, rows in ((-1, 0, 7, 2), (1, 1, 5, 1),
                                      (2, 2, 3, 1), (3, 3, 1, 1)):
            y = h + dy * u
            canvas.rect(tx + left * u, y, width * u, rows * u, BUBBLE_INK)
            if width > 2:
                canvas.rect(tx + (left + 1) * u, y, (width - 2) * u, rows * u,
                            BUBBLE_FILL)

        # Typed-out text; each line keeps the position of its full width
        remaining = len(self.ctl.speech.shown_text)
        top = (h - len(layout.lines) * layout.line_height) / 2
        for i, (line, line_w) in enumerate(zip(layout.lines, layout.line_widths)):
            if remaining <= 0:
                break
            canvas.text(line[:remaining], round((w - line_w) / 2),
                        round(top + i * layout.line_height),
                        BUBBLE_FONT, BUBBLE_INK, bold=True)
            remaining -= len(line) + 1  # the space the line break replaced
