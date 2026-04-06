"""Speech bubble system — floating text above the crab (Linux/GTK3)."""

import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo
import cairo


class SpeechBubble:
    """A small floating window that shows text above the crab."""

    def __init__(self):
        self.window = None
        self._drawing_area = None
        self.text = ""
        self.last_shown = 0
        self.min_interval = 3000  # ms between speeches
        self.show_chance = 1.0
        self._hide_timer = None
        self._visible = False
        self._persistent = False
        self._opacity = 0.0
        self._target_opacity = 0.0
        self._fade_timer = None

    def setup(self):
        """Create the speech bubble window."""
        self.window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.window.set_decorated(False)
        self.window.set_keep_above(True)
        self.window.set_accept_focus(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)

        # Enable transparency
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        self.window.set_app_paintable(True)

        self._drawing_area = Gtk.DrawingArea()
        self._drawing_area.connect("draw", self._on_draw)
        self.window.add(self._drawing_area)

        self.window.set_default_size(160, 40)

    def _on_draw(self, widget, cr):
        """Draw the speech bubble background and text."""
        # Clear to transparent
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

        # Text
        cr.set_source_rgba(1, 1, 1, alpha)
        layout = widget.create_pango_layout(self.text)
        font_desc = Pango.FontDescription("Monospace 11")
        layout.set_font_description(font_desc)
        layout.set_alignment(Pango.Alignment.CENTER)
        layout.set_width((w - 16) * Pango.SCALE)

        text_w, text_h = layout.get_pixel_size()
        cr.move_to(8, (h - text_h) / 2)
        PangoCairo.show_layout(cr, layout)

    def _start_fade(self, target, duration_ms):
        """Animate opacity towards target."""
        self._target_opacity = target
        if self._fade_timer:
            GLib.source_remove(self._fade_timer)
            self._fade_timer = None

        steps = max(1, int(duration_ms / 16))
        step_delta = (target - self._opacity) / steps

        def fade_step():
            self._opacity += step_delta
            if (step_delta > 0 and self._opacity >= self._target_opacity) or \
               (step_delta < 0 and self._opacity <= self._target_opacity) or \
               step_delta == 0:
                self._opacity = self._target_opacity
                if self._opacity <= 0:
                    self.window.hide()
                self._drawing_area.queue_draw()
                self._fade_timer = None
                return False
            self._drawing_area.queue_draw()
            return True

        self._fade_timer = GLib.timeout_add(16, fade_step)

    def maybe_show(self, text, crab_x, crab_y):
        """Show the bubble with probability check and rate limiting."""
        if not self.window or self._persistent:
            return
        now = time.time() * 1000
        if now - self.last_shown < self.min_interval:
            return
        import random
        if random.random() > self.show_chance:
            return
        self.show(text, crab_x, crab_y)

    def _calc_size(self, text):
        """Calculate bubble size to fit text."""
        width = max(80, min(300, len(text) * 9 + 20))
        # Wrap to second line if needed
        chars_per_line = max(1, (width - 20) // 9)
        lines = (len(text) + chars_per_line - 1) // chars_per_line
        height = max(36, 20 + lines * 18)
        return width, height

    def show(self, text, crab_x, crab_y):
        """Show the speech bubble immediately."""
        if not self.window or self._persistent:
            return

        self.last_shown = time.time() * 1000
        self._visible = True
        self.text = text

        width, height = self._calc_size(text)
        self.window.resize(width, height)

        # Position above the crab (GTK Y-down: subtract to go up)
        bubble_x = int(crab_x - width / 2)
        bubble_y = int(crab_y - height - 10)
        self.window.move(bubble_x, bubble_y)

        self.window.show_all()
        self._start_fade(1.0, 300)

        # Schedule fade out
        if self._hide_timer:
            GLib.source_remove(self._hide_timer)
        display_time = max(2.0, min(5.0, len(text) * 0.15))
        self._hide_timer = GLib.timeout_add(
            int(display_time * 1000), self._hide_bubble)

    def show_persistent(self, text, crab_x, crab_y, duration=300.0):
        """Show a persistent bubble that blocks other messages."""
        if not self.window:
            return
        self._persistent = True
        self.last_shown = time.time() * 1000
        self._visible = True
        self.text = text

        width, height = self._calc_size(text)
        self.window.resize(width, height)

        bubble_x = int(crab_x - width / 2)
        bubble_y = int(crab_y - height - 10)
        self.window.move(bubble_x, bubble_y)

        self.window.show_all()
        self._start_fade(1.0, 300)

        if self._hide_timer:
            GLib.source_remove(self._hide_timer)
        self._hide_timer = GLib.timeout_add(
            int(duration * 1000), self._hide_bubble)

    def clear_persistent(self):
        """Clear persistent mode and hide the bubble."""
        if self._persistent:
            self._persistent = False
            if self._hide_timer:
                GLib.source_remove(self._hide_timer)
                self._hide_timer = None
            self._hide_bubble()

    def _hide_bubble(self):
        """Fade out the speech bubble."""
        if not self._visible:
            return False
        self._visible = False
        self._persistent = False
        self._start_fade(0.0, 500)
        self._hide_timer = None
        return False

    def update_position(self, crab_x, crab_y):
        """Reposition the bubble if crab moves while it's visible."""
        if self._visible and self.window:
            w, h = self.window.get_size()
            self.window.move(
                int(crab_x - w / 2),
                int(crab_y - h - 10),
            )
