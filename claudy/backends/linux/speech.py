"""Speech bubble — floating text above the crab (Linux/GTK3).

The bubble only displays and fades; what to say, and for how long, is
decided by the controller.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo
import cairo

FADE_IN_MS = 300
FADE_OUT_MS = 500
GAP_ABOVE_CRAB = 10


class SpeechBubble:
    """A small click-through window that shows text above the crab."""

    def __init__(self):
        self.text = ""
        self._visible = False
        self._opacity = 0.0
        self._fade_timer = None

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

        self._drawing_area = Gtk.DrawingArea()
        self._drawing_area.connect("draw", self._on_draw)
        self.window.add(self._drawing_area)
        self.window.set_default_size(160, 40)

    def show(self, text, crab_x, crab_y):
        """Show `text` above (crab_x, crab_y), replacing any current line."""
        self._visible = True
        self.text = text
        width, height = self._calc_size(text)
        self.window.resize(width, height)
        self._place(crab_x, crab_y, width, height)
        self.window.show_all()
        self._drawing_area.queue_draw()
        self._fade_to(1.0, FADE_IN_MS)

    def hide(self):
        """Fade the bubble out."""
        if self._visible:
            self._visible = False
            self._fade_to(0.0, FADE_OUT_MS)

    def update_position(self, crab_x, crab_y):
        """Follow the crab while visible."""
        if self._visible:
            width, height = self.window.get_size()
            self._place(crab_x, crab_y, width, height)

    def _place(self, crab_x, crab_y, width, height):
        # GTK Y grows downward: subtract to go up
        self.window.move(int(crab_x - width / 2),
                         int(crab_y - height - GAP_ABOVE_CRAB))

    @staticmethod
    def _calc_size(text):
        """Bubble size that fits the text, wrapping long lines."""
        width = max(80, min(300, len(text) * 9 + 20))
        chars_per_line = max(1, (width - 20) // 9)
        lines = (len(text) + chars_per_line - 1) // chars_per_line
        height = max(36, 20 + lines * 18)
        return width, height

    def _fade_to(self, target, duration_ms):
        if self._fade_timer:
            GLib.source_remove(self._fade_timer)
        steps = max(1, int(duration_ms / 16))
        step = (target - self._opacity) / steps

        def fade_step():
            self._opacity += step
            done = (step == 0 or (step > 0 and self._opacity >= target)
                    or (step < 0 and self._opacity <= target))
            if done:
                self._opacity = target
                self._fade_timer = None
                if target <= 0:
                    self.window.hide()
            self._drawing_area.queue_draw()
            return not done

        self._fade_timer = GLib.timeout_add(16, fade_step)

    def _on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        if not self.text or self._opacity <= 0:
            return

        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height
        alpha = self._opacity

        # Rounded rectangle background
        radius = 8
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.new_sub_path()
        cr.arc(w - radius, radius, radius, -1.5708, 0)
        cr.arc(w - radius, h - radius, radius, 0, 1.5708)
        cr.arc(radius, h - radius, radius, 1.5708, 3.14159)
        cr.arc(radius, radius, radius, 3.14159, 4.71239)
        cr.close_path()
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.85 * alpha)
        cr.fill()

        cr.set_source_rgba(1, 1, 1, alpha)
        layout = widget.create_pango_layout(self.text)
        layout.set_font_description(Pango.FontDescription("Monospace 11"))
        layout.set_alignment(Pango.Alignment.CENTER)
        layout.set_width((w - 16) * Pango.SCALE)
        _, text_h = layout.get_pixel_size()
        cr.move_to(8, (h - text_h) / 2)
        PangoCairo.show_layout(cr, layout)
