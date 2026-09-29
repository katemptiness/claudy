"""Tests for the Linux backend (GTK3).

Nothing here shows a window. Windows are at most realized, which creates
them on the X server without mapping them, widgets get their events
straight from the test, and the app's own windows are stood in for by mocks.
The GTK tests are skipped where GTK 3 or a display isn't available.
"""

import unittest
from unittest import mock

from claudy.content import app_reactions

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from claudy.backends.linux import events, settings_ui
    from gi.repository import Gdk, GLib, Gtk
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
