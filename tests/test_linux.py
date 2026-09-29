"""Tests for the Linux backend (GTK3).

Nothing here shows a window. Windows are at most realized, which creates
them on the X server without mapping them, widgets get their events
straight from the test, and the app's own windows are stood in for by mocks.
The GTK tests are skipped where GTK 3 or a display isn't available.
"""

import ctypes
import ctypes.util
import types
import unittest
from unittest import mock

from claudy.content import app_reactions
from claudy.core.speech import Speech
from claudy.render.scene import BUBBLE_OVERLAP

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from claudy.backends.linux import app, bubble, events, settings_ui, windows
    from gi.repository import Gdk, GLib, Gtk
    import cairo
    HAVE_GTK = Gdk.Display.get_default() is not None
except (ImportError, ValueError):
    HAVE_GTK = False

needs_gtk = unittest.skipUnless(HAVE_GTK, "needs GTK 3 and a display")


class ProcessMatchingTests(unittest.TestCase):
    """Which running process is which app (no GTK needed)."""

    def setUp(self):
        self.match = app_reactions.match_linux_process

    def test_electron_crash_handler_is_not_chrome(self):
        # Every Electron app runs one, Claude's desktop app among them
        self.assertIsNone(self.match("chrome_crashpad"))
        self.assertEqual(self.match("chrome"), "chrome")
        self.assertEqual(self.match("claude-desktop"), "claude")

    def test_helper_processes_still_match_their_app(self):
        self.assertEqual(self.match("vivaldi-bin"), "vivaldi")
        self.assertEqual(self.match("chromium-browse"), "chromium")
        self.assertEqual(self.match("telegram-deskto"), "telegram")
        self.assertEqual(self.match("ptyxis-agent"), "ptyxis")

    def test_libreoffice_is_found_by_the_process_that_stays(self):
        self.assertEqual(self.match("soffice.bin"), "soffice")
        self.assertIsNone(self.match("oosplash"))

    def test_name_cut_off_by_ps_matches_the_longer_key(self):
        self.assertEqual(self.match("gnome-text-edit"), "gnome-text-editor")

    def test_every_linux_app_has_a_name_to_be_counted_by(self):
        for key, app_info in app_reactions.LINUX_APPS.items():
            with self.subTest(app=key):
                self.assertTrue(app_info.name)
                self.assertEqual(self.match(key), key)


@needs_gtk
class SystemEventTests(unittest.TestCase):

    def make_handler(self, controller, bus=None):
        """A handler on a stand-in system bus, polling nothing yet."""
        gio = mock.Mock()
        gio.bus_get_sync.return_value = bus or mock.Mock()
        with mock.patch.object(events, "Gio", gio), \
                mock.patch.object(events.SystemEventHandler, "_scan_apps",
                                  return_value=set()), \
                mock.patch.object(events.GLib, "timeout_add_seconds"):
            return events.SystemEventHandler(controller)

    @staticmethod
    def prepare_for_sleep(handler, going_to_sleep):
        params = GLib.Variant("(b)", (going_to_sleep,))
        handler._on_prepare_for_sleep(None, None, None, None, None, params, None)

    def test_the_sleep_subscription_keeps_its_bus(self):
        bus = mock.Mock()
        handler = self.make_handler(mock.Mock(), bus)
        # GLib holds the shared bus only weakly: dropping it would drop
        # the subscription too
        self.assertIs(handler._system_bus, bus)
        args = bus.signal_subscribe.call_args[0]
        self.assertEqual(args[2], "PrepareForSleep")
        self.assertEqual(args[6], handler._on_prepare_for_sleep)

    def test_sleep_and_wake_reach_the_controller(self):
        controller = mock.Mock()
        handler = self.make_handler(controller)
        self.prepare_for_sleep(handler, True)
        controller.on_system_sleep.assert_called_once_with()
        self.prepare_for_sleep(handler, False)
        controller.on_system_wake.assert_called_once_with()

    def test_a_failed_reaction_to_sleep_is_logged(self):
        controller = mock.Mock()
        controller.on_system_sleep.side_effect = RuntimeError("boom")
        handler = self.make_handler(controller)
        with mock.patch.object(events, "log") as log:
            self.prepare_for_sleep(handler, True)
        log.exception.assert_called_once()

    def test_a_launch_is_counted_under_the_apps_own_name(self):
        controller = mock.Mock()
        handler = self.make_handler(controller)
        with mock.patch.object(events.SystemEventHandler, "_scan_apps",
                               return_value={"code"}):
            handler._check_new_apps()
        controller.on_app_launched.assert_called_once_with(
            "code", app_reactions.LINUX_APPS["code"], "VS Code")


def _input_rects(window):
    """The parts of `window` that take clicks, as the X server has them.

    The window is realized, so that it exists on the server, but never shown.
    Returns None where the server can't be asked (not X11, no libXext).
    """
    try:
        gi.require_version("GdkX11", "3.0")
        from gi.repository import GdkX11
    except (ImportError, ValueError):
        return None
    libx11 = ctypes.util.find_library("X11")
    libxext = ctypes.util.find_library("Xext")
    if not (libx11 and libxext and
            isinstance(window.get_display(), GdkX11.X11Display)):
        return None

    class XRectangle(ctypes.Structure):
        _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                    ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]

    x11, xext = ctypes.CDLL(libx11), ctypes.CDLL(libxext)
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XFree.argtypes = [ctypes.c_void_p]
    xext.XShapeGetRectangles.restype = ctypes.POINTER(XRectangle)
    xext.XShapeGetRectangles.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    shape_input = 2

    window.realize()
    window.get_display().sync()   # let GTK's requests reach the server
    xid = GdkX11.X11Window.get_xid(window.get_window())
    display = x11.XOpenDisplay(window.get_display().get_name().encode())
    if not display:
        return None
    try:
        count, ordering = ctypes.c_int(), ctypes.c_int()
        rects = xext.XShapeGetRectangles(
            display, xid, shape_input, ctypes.byref(count),
            ctypes.byref(ordering))
        found = [(r.x, r.y, r.width, r.height)
                 for r in (rects[i] for i in range(count.value))]
        if rects:
            x11.XFree(ctypes.cast(rects, ctypes.c_void_p))
        return found
    finally:
        x11.XCloseDisplay(display)


@needs_gtk
class OverlayWindowTests(unittest.TestCase):

    def input_rects(self, window):
        self.addCleanup(window.destroy)
        window.set_default_size(200, 90)
        rects = _input_rects(window)
        if rects is None:
            self.skipTest("needs an X11 display and libXext")
        self.assertFalse(window.get_mapped())
        return rects

    def test_click_through_windows_take_no_clicks(self):
        self.assertEqual(
            self.input_rects(windows.make_overlay_window(click_through=True)),
            [])

    def test_other_windows_take_clicks_where_asked(self):
        self.assertEqual(self.input_rects(windows.make_overlay_window()),
                         [(0, 0, 200, 90)])
        window = windows.make_overlay_window()
        windows.take_clicks_only_in(
            window, cairo.Region(cairo.RectangleInt(60, 10, 80, 80)))
        self.assertEqual(self.input_rects(window), [(60, 10, 80, 80)])

    def test_the_speech_bubble_takes_no_clicks(self):
        speech_bubble = bubble.BubbleWindow(scene=None, images=None)
        self.assertEqual(self.input_rects(speech_bubble.window), [])


class _BubbleScene:
    def bubble_layout(self, canvas):
        return types.SimpleNamespace(width=120, height=60)


@needs_gtk
class BubbleTests(unittest.TestCase):
    """The bubble moves and redraws only when something changed."""

    def setUp(self):
        self.bubble = bubble.BubbleWindow(_BubbleScene(), images=None)
        self.bubble.window.destroy()
        self.window = self.bubble.window = mock.Mock()
        self.area = self.bubble._area = mock.Mock()
        self.visible = False
        self.window.get_visible.side_effect = lambda: self.visible
        self.window.show_all.side_effect = lambda: setattr(self, "visible", True)
        self.window.hide.side_effect = lambda: setattr(self, "visible", False)
        self.speech = Speech()
        self.speech.say("привет")
        self.speech.update(1000)   # typed out and faded in

    def test_standing_still_costs_nothing(self):
        for _ in range(3):
            self.bubble.sync(self.speech, 500, 800)
        self.window.move.assert_called_once_with(
            440, 800 + BUBBLE_OVERLAP - 60)
        self.area.queue_draw.assert_called_once_with()

        self.bubble.sync(self.speech, 510, 800)   # Claudy took a step
        self.assertEqual(self.window.move.call_count, 2)
        self.assertEqual(self.area.queue_draw.call_count, 1)

        self.speech.hide()
        self.speech.update(100)                   # fading out
        self.bubble.sync(self.speech, 510, 800)
        self.assertEqual(self.window.move.call_count, 2)
        self.assertEqual(self.area.queue_draw.call_count, 2)

    def test_placed_afresh_after_hiding(self):
        self.bubble.sync(self.speech, 500, 800)
        self.bubble.sync(Speech(), 500, 800)      # nothing to say
        self.window.hide.assert_called_once_with()
        self.bubble.sync(self.speech, 500, 800)
        self.assertEqual(self.window.move.call_count, 2)
        self.assertEqual(self.area.queue_draw.call_count, 2)


@needs_gtk
class CrabAppTests(unittest.TestCase):
    """CrabApp's own logic, on mock windows (building it would show them)."""

    def setUp(self):
        crab = self.crab = app.CrabApp.__new__(app.CrabApp)
        crab._settings = types.SimpleNamespace(vertical_offset=0,
                                               star_height=300)
        crab._monitor_x, crab._monitor_width, crab._base_y = 0, 1440, 900
        crab._spots = {}
        crab._click_timer = None
        crab.window = mock.Mock()
        crab.ground_window = mock.Mock()
        crab.star_window = mock.Mock()
        crab.star_window.get_visible.return_value = False
        crab.bubble = mock.Mock()
        crab.controller = mock.Mock()
        crab.controller.character = types.SimpleNamespace(screen_width=1440)

    def test_windows_move_only_when_claudy_does(self):
        view = {"x": 700, "y_offset": 0}
        self.crab._move_windows(view)
        self.crab._move_windows(view)
        self.crab.window.move.assert_called_once()
        self.crab.ground_window.move.assert_called_once()
        self.crab._move_windows({"x": 702, "y_offset": 0})
        self.assertEqual(self.crab.window.move.call_count, 2)
        self.assertEqual(self.crab.ground_window.move.call_count, 2)

    def test_the_star_is_placed_afresh_each_night(self):
        star = self.crab.star_window
        self.crab.controller.star = {"name": "Вега"}
        self.crab._place_star()
        star.get_visible.return_value = True
        self.crab._place_star()
        star.move.assert_called_once()

        self.crab.controller.star = None           # daylight
        self.crab._place_star()
        star.hide.assert_called_once_with()
        star.get_visible.return_value = False
        self.crab.controller.star = {"name": "Вега"}
        self.crab._place_star()
        self.assertEqual(star.move.call_count, 2)

    def test_follows_the_primary_monitor_when_monitors_change(self):
        with mock.patch.object(app, "get_screen_geometry",
                               return_value=(1080, 2560, 1586)):
            self.assertFalse(self.crab._follow_screen())
        self.assertEqual(
            (self.crab._monitor_x, self.crab._monitor_width,
             self.crab._base_y), (1080, 2560, 1586))
        self.assertEqual(self.crab.controller.character.screen_width, 2560)

        # For a moment there may be no monitor at all
        with mock.patch.object(app, "get_screen_geometry", return_value=None):
            self.crab._follow_screen()
        self.assertEqual(self.crab._monitor_width, 2560)


@needs_gtk
class SettingsFormTests(unittest.TestCase):

    @staticmethod
    def wheel(widget):
        """Turn the mouse wheel over `widget`; True if it took the turn."""
        event = Gdk.Event.new(Gdk.EventType.SCROLL)
        event.scroll.direction = Gdk.ScrollDirection.DOWN
        pointer = Gdk.Display.get_default().get_default_seat().get_pointer()
        event.set_device(pointer)
        event.set_source_device(pointer)
        return widget.emit("scroll-event", event)

    def test_the_wheel_scrolls_the_form_not_its_controls(self):
        form = settings_ui.SettingsWindow.__new__(settings_ui.SettingsWindow)
        form._grid, form._row = Gtk.Grid(), 0
        combo = Gtk.ComboBoxText()
        for text in ("a", "b", "c"):
            combo.append_text(text)
        combo.set_active(0)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        scale.set_value(50)
        form._add_widget(combo)
        form._add_widget(scale)

        # Not taken, so it goes on up to the scrolled window
        self.assertFalse(self.wheel(combo))
        self.assertFalse(self.wheel(scale))
        self.assertEqual(combo.get_active(), 0)
        self.assertEqual(scale.get_value(), 50)


if __name__ == "__main__":
    unittest.main()
