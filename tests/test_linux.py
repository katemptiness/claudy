"""Tests for the Linux backend (GTK3).

Nothing here shows a window. Windows are at most realized, which creates
them on the X server without mapping them, widgets get their events
straight from the test, and the app's own windows are stood in for by mocks.
The GTK tests are skipped where GTK 3 or a display isn't available.
"""

import unittest
from unittest import mock

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from claudy.backends.linux import events
    from gi.repository import Gdk, GLib
    HAVE_GTK = Gdk.Display.get_default() is not None
except (ImportError, ValueError):
    HAVE_GTK = False

needs_gtk = unittest.skipUnless(HAVE_GTK, "needs GTK 3 and a display")


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


if __name__ == "__main__":
    unittest.main()
