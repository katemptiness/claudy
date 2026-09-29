"""The borderless overlay windows Claudy lives in (Linux/GTK3).

Shared by the crab, ground and star windows in app.py and the speech bubble,
the way macos/views.py serves the macOS backend.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import cairo


def take_clicks_only_in(window, region):
    """Let clicks outside `region` fall through `window` to whatever is
    behind it; an empty region makes the whole window click-through.

    Set on the Gtk.Window rather than its GdkWindow: GTK re-applies its own
    input shape whenever it realizes the window, and would wipe one set on
    the GdkWindow from a realize handler straight away.
    """
    window.input_shape_combine_region(region)


def make_overlay_window(click_through=False):
    """A borderless, transparent, always-on-top popup window.

    POPUP bypasses WM positioning rules so Claudy can sit on the panel.
    A click-through window hands every click to whatever is behind it, so
    it never swallows a click meant for the app underneath.
    """
    win = Gtk.Window(type=Gtk.WindowType.POPUP)
    win.set_decorated(False)
    win.set_keep_above(True)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    visual = win.get_screen().get_rgba_visual()
    if visual:
        win.set_visual(visual)
    win.set_app_paintable(True)
    if click_through:
        take_clicks_only_in(win, cairo.Region())
    return win
