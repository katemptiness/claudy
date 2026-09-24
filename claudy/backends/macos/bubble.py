"""Speech bubble window (macOS), drawn by the shared scene."""

from claudy.backends.macos.canvas import QuartzCanvas
from claudy.backends.macos.views import add_drawing_view, make_overlay_window
from claudy.render.scene import BUBBLE_OVERLAP


class BubbleWindow:
    """A click-through window that mirrors the controller's Speech state."""

    def __init__(self, scene, images):
        self._scene = scene
        self._measure = QuartzCanvas(None, 0, images)
        self._size = (160, 40)
        self._shown = False
        self.window = make_overlay_window(*self._size)
        self.window.setIgnoresMouseEvents_(True)
        self.view = add_drawing_view(
            self.window, *self._size, scene.paint_bubble, images)

    def sync(self, speech, anchor_x, anchor_y):
        """Show, move and redraw the bubble to match `speech`.

        (anchor_x, anchor_y) is the screen point just above Claudy that the
        tail points at (y grows upward, as in AppKit).
        """
        if not speech.visible:
            if self._shown:
                self._shown = False
                self.window.orderOut_(None)
            return
        layout = self._scene.bubble_layout(self._measure)
        size = (layout.width, layout.height)
        if size != self._size:
            self._size = size
            self.window.setContentSize_(size)
        self.window.setFrameOrigin_(
            (anchor_x - layout.width / 2, anchor_y - BUBBLE_OVERLAP))
        self.window.setAlphaValue_(speech.alpha)
        if not self._shown:
            self._shown = True
            self.window.orderFront_(None)
        self.view.setNeedsDisplay_(True)
