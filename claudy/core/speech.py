"""Speech bubble state: what Claudy is saying and how far along it is.

Text types in a letter at a time, the bubble fades in and out, and a new
line replaces the old one immediately. Backends just draw the current state
(see render.scene) — all timing lives here.
"""

TYPE_MS_PER_CHAR = 30
FADE_IN_MS = 150
FADE_OUT_MS = 300
# Once a line is typed out, a moment to take it in before another may
# replace it
GLANCE_MS = 1000


class Speech:

    def __init__(self):
        self.text = ""
        self.visible = False   # the bubble is on screen (maybe fading out)
        self.alpha = 0.0
        self._age_ms = 0.0
        self._fading_out = False

    @staticmethod
    def typing_ms(text):
        return len(text) * TYPE_MS_PER_CHAR

    @staticmethod
    def readable_ms(text):
        """The least time a line needs on screen to be typed out and read."""
        return Speech.typing_ms(text) + GLANCE_MS

    def say(self, text):
        self.text = text
        self.visible = True
        self._age_ms = 0.0
        self._fading_out = False

    def hide(self):
        if self.visible:
            self._fading_out = True

    @property
    def shown_text(self):
        """The part of the text typed out so far."""
        chars = int(self._age_ms / TYPE_MS_PER_CHAR) + 1
        return self.text[:chars]

    @property
    def typing(self):
        return self.visible and len(self.shown_text) < len(self.text)

    def update(self, dt):
        if not self.visible:
            return
        self._age_ms += dt
        if self._fading_out:
            self.alpha -= dt / FADE_OUT_MS
            if self.alpha <= 0:
                self.alpha = 0.0
                self.visible = False
                self._fading_out = False
        else:
            self.alpha = min(1.0, self.alpha + dt / FADE_IN_MS)
