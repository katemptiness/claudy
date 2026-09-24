"""Speech bubble window (Linux/GTK3), drawn by the shared scene."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from claudy.backends.linux.canvas import (
    CairoCanvas, clear, measuring_context,
)
from claudy.render.scene import BUBBLE_OVERLAP


class BubbleWindow:
    """A click-through window that mirrors the controller's Speech state."""

    def __init__(self, scene, images):
        self._scene = scene
        self._images = images
        self._alpha = 0.0
        self._measure = CairoCanvas(measuring_context(), images)
        self._size = None

        self.window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.window.set_decorated(False)
        self.window.set_keep_above(True)
        self.window.set_accept_focus(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
        visual = self.window.get_screen().get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        self.window.set_app_paintable(True)

        self._area = Gtk.DrawingArea()
        self._area.connect("draw", self._on_draw)
        self.window.add(self._area)

    def sync(self, speech, anchor_x, anchor_y):
        """Show, move and redraw the bubble to match `speech`.

        (anchor_x, anchor_y) is the screen point just above Claudy that the
        tail points at.
        """
        if not speech.visible:
            if self.window.get_visible():
                self.window.hide()
            return
        layout = self._scene.bubble_layout(self._measure)
        size = (layout.width, layout.height)
        if size != self._size:
            self._size = size
            self.window.resize(*size)
            self._area.set_size_request(*size)
        self.window.move(int(anchor_x - layout.width / 2),
                         int(anchor_y + BUBBLE_OVERLAP - layout.height))
        self._alpha = speech.alpha
        if not self.window.get_visible():
            self.window.show_all()
        self._area.queue_draw()

    def _on_draw(self, widget, cr):
        clear(cr)
        if self._alpha <= 0:
            return
        cr.push_group()
        self._scene.paint_bubble(CairoCanvas(cr, self._images))
        cr.pop_group_to_source()
        cr.paint_with_alpha(self._alpha)
