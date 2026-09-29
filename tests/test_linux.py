"""Tests for the Linux backend (GTK3).

Nothing here shows a window. Windows are at most realized, which creates
them on the X server without mapping them, widgets get their events
straight from the test, and the app's own windows are stood in for by mocks.
The GTK tests are skipped where GTK 3 or a display isn't available.
"""

import ctypes
import ctypes.util
import os
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

from claudy.content import app_reactions
from claudy.core.speech import Speech
from claudy.render.scene import BUBBLE_OVERLAP
from tests import ROOT

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
        # ...and, where it can't sandbox itself otherwise, Chromium's sandbox
        self.assertIsNone(self.match("chrome-sandbox"))
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

    def test_a_click_waits_as_long_as_the_desktop_says(self):
        settings = Gtk.Settings.get_default()
        before = settings.props.gtk_double_click_time
        settings.props.gtk_double_click_time = 250
        self.addCleanup(setattr, settings.props, "gtk_double_click_time",
                        before)
        press = types.SimpleNamespace(button=1,
                                      type=Gdk.EventType.BUTTON_PRESS)
        with mock.patch.object(app.GLib, "timeout_add") as timeout_add:
            self.crab._on_button_press(None, press)
        timeout_add.assert_called_once_with(250, self.crab._single_click_fired)

    def test_follows_the_primary_monitor_when_monitors_change(self):
        view = {"x": 700, "y_offset": 0}
        self.crab._move_windows(view)
        with mock.patch.object(app, "get_screen_geometry",
                               return_value=(1080, 2560, 1586)):
            self.assertFalse(self.crab._follow_screen())
        self.assertEqual(
            (self.crab._monitor_x, self.crab._monitor_width,
             self.crab._base_y), (1080, 2560, 1586))
        self.crab.controller.set_screen_width.assert_called_once_with(2560)
        # Standing still, Claudy still goes along to the new monitor
        self.crab._move_windows(view)
        self.assertEqual(self.crab.window.move.call_count, 2)
        x, y = self.crab.window.move.call_args[0]
        self.assertGreaterEqual(x, 1080)
        self.assertLess(y, 1586)

        # For a moment there may be no monitor at all
        with mock.patch.object(app, "get_screen_geometry", return_value=None):
            self.crab._follow_screen()
        self.assertEqual(self.crab._monitor_width, 2560)

    def test_launched_apps_get_a_session_of_their_own(self):
        with mock.patch.object(app.subprocess, "Popen") as popen:
            app._launch(["kitty", "claude"])
        kwargs = popen.call_args[1]
        self.assertTrue(kwargs["start_new_session"])
        for stream in ("stdin", "stdout", "stderr"):
            self.assertEqual(kwargs[stream], subprocess.DEVNULL)

    def test_icons_are_crisp_and_centered(self):
        sizes = [icon.get_width() for icon in
                 (app.claudy_icon(scale) for scale in app.ICON_SCALES)]
        self.assertEqual(sizes, [16, 32, 48, 64, 96, 128, 256])
        icon = app.claudy_icon(1)
        self.assertEqual(icon.get_height(), 16)
        pixels, stride = icon.get_pixels(), icon.get_rowstride()
        inked = [y for y in range(16)
                 if any(pixels[y * stride + x * 4 + 3] for x in range(16))]
        above, below = inked[0], 15 - inked[-1]
        self.assertLessEqual(abs(above - below), 1)


@needs_gtk
class GtkStartTests(unittest.TestCase):
    """How the backend starts GTK, in a fresh process of its own.

    WAYLAND_DISPLAY points at a stand-in that only counts who knocks, so
    whether GTK went for Wayland shows on an X11 session too, where it
    would end up on X11 either way.
    """

    CLAUDY = "import claudy.backends.linux.app\n"
    PLAIN_GTK = ("import gi\n"
                 "gi.require_version('Gtk', '3.0')\n"
                 "from gi.repository import Gtk\n")
    REPORT = ("import os\n"
              "from gi.repository import Gdk, GLib\n"
              "print(GLib.get_prgname(), GLib.get_application_name(),\n"
              "      type(Gdk.Display.get_default()).__name__,\n"
              "      os.environ.get('GDK_BACKEND'))\n")

    def start(self, first_import=CLAUDY, backend=None):
        """Start GTK through `first_import`, with GDK_BACKEND=`backend` or
        unset. Returns ((prgname, application name, display class,
        GDK_BACKEND afterwards), how often GTK knocked on Wayland's door)."""
        environ = dict(os.environ)
        environ.pop("GDK_BACKEND", None)
        if backend:
            environ["GDK_BACKEND"] = backend
        self.assertIn("CLAUDY_HOME", environ)   # never the real ~/.claudy
        folder = tempfile.mkdtemp(prefix="claudy-wayland-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        wayland = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(wayland.close)
        wayland.bind(os.path.join(folder, "wayland-0"))
        wayland.listen()
        environ["WAYLAND_DISPLAY"] = wayland.getsockname()

        probe = subprocess.Popen(
            [sys.executable, "-c", first_import + self.REPORT], cwd=ROOT,
            env=environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True)
        knocks, give_up = 0, time.monotonic() + 60
        while probe.poll() is None:
            if time.monotonic() > give_up:
                probe.kill()
                probe.communicate()
                self.fail("GTK never finished starting")
            # A GTK that knocks waits for an answer; hanging up on it sends
            # it on to X11
            if select.select([wayland], [], [], 0.1)[0]:
                wayland.accept()[0].close()
                knocks += 1
        out, err = probe.communicate()
        self.assertEqual(probe.returncode, 0, err)
        return out.split(), knocks

    def test_named_claudy_on_x11_without_passing_it_on(self):
        (name, app_name, display, backend), knocks = self.start()
        self.assertEqual((name, app_name), ("claudy", "Claudy"))
        self.assertEqual(display, "X11Display")
        self.assertEqual(knocks, 0)
        # Apps Claudy launches inherit his environment
        self.assertEqual(backend, "None")

    def test_left_to_itself_gtk_would_go_for_wayland(self):
        # Otherwise no knocks above would prove nothing
        self.assertGreater(self.start(self.PLAIN_GTK)[1], 0)

    def test_a_backend_the_user_chose_is_kept(self):
        self.assertEqual(self.start(backend="x11")[0][3], "x11")


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
