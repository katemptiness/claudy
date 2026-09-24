"""What Claudy's windows show, painted through a backend's Canvas.

Three windows, all drawn here:
- the crab window: Claudy, the summoned friend, the toy;
- the ground overlay: shadows, the gift on the Dock, particles;
- the speech bubble, sized to its text by bubble_layout().
"""

from dataclasses import dataclass

from claudy.config import (
    FRIEND_OFFSET_X, OVERLAY_HEIGHT, PIXEL_SCALE, SPRITE_SIZE, SPRITE_X,
    SPRITE_Y, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from claudy.render import art

INK = (0.0, 0.0, 0.0, 1.0)

# Shadows sit on the ground just under the feet (the sprite's last two
# rows are empty), as one row of art pixels
SHADOW_Y = OVERLAY_HEIGHT - WINDOW_HEIGHT + SPRITE_Y + 14 * PIXEL_SCALE + 1
SHADOW_UNITS = 10       # width of the dark middle, in art pixels
SHADOW_ALPHA = 0.22
SHADOW_FADE_HEIGHT = 80  # px above ground where the shadow is smallest

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


def _snap(value, unit):
    """Round up to a whole number of units."""
    return int(-(-value // unit) * unit)


class Scene:

    def __init__(self, controller):
        self.ctl = controller
        self._bubble = None

    # ---- Crab window ----

    def paint_crab(self, canvas):
        view = self.ctl.view
        if view["friend_visible"]:
            canvas.image(art.sprite_key(view["friend_sprite"], friend=True),
                         SPRITE_X + FRIEND_OFFSET_X, SPRITE_Y)
        key = art.sprite_key(view["sprite"], flip=not view["facing_right"],
                             pose=view["pose"])
        # Sprites wider than 16 (props) keep Claudy in their middle
        x = (WINDOW_WIDTH - art.build(key).width) / 2
        canvas.image(key, round(x + view["shake_dx"]), SPRITE_Y)
        if view["show_toy"]:
            canvas.text("🧸", SPRITE_X + SPRITE_SIZE - 10, WINDOW_HEIGHT - 25, 16, INK)

    # ---- Ground overlay ----

    def paint_ground(self, canvas):
        view = self.ctl.view
        height = max(0.0, view["y_offset"])
        if view["friend_visible"]:
            self._shadow(canvas, WINDOW_WIDTH / 2 + FRIEND_OFFSET_X, height)
        self._shadow(canvas, WINDOW_WIDTH / 2, height)

        if self.ctl.gift_emoji:
            canvas.text(self.ctl.gift_emoji, SPRITE_X + SPRITE_SIZE + 5,
                        OVERLAY_HEIGHT - 32, 20, INK)

        for p in self.ctl.particles.get_active():
            key = art.particle_key(p.frame, p.tint)
            image = art.build(key)
            canvas.image(key, round(p.draw_x - image.width / 2),
                         round(OVERLAY_HEIGHT - p.y - image.height / 2),
                         p.opacity)

    @staticmethod
    def _shadow(canvas, center_x, height):
        """A pixel shadow that shrinks and fades as Claudy leaves the ground."""
        closeness = max(0.3, 1 - height / SHADOW_FADE_HEIGHT)
        units = max(2, round(SHADOW_UNITS * closeness))
        alpha = SHADOW_ALPHA * (0.4 + 0.6 * closeness)
        w = units * PIXEL_SCALE
        x = round(center_x - w / 2)
        canvas.rect(x, SHADOW_Y, w, PIXEL_SCALE, (0, 0, 0, alpha))
        edge = (0, 0, 0, alpha / 2)
        canvas.rect(x - PIXEL_SCALE, SHADOW_Y, PIXEL_SCALE, PIXEL_SCALE, edge)
        canvas.rect(x + w, SHADOW_Y, PIXEL_SCALE, PIXEL_SCALE, edge)

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
