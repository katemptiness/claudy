"""System events — sleep/wake and app launches (Linux).

Sleep/wake comes from logind over D-Bus. There's no portable "app launched"
notification on Linux, so running processes are polled and matched against
content.app_reactions.LINUX_APPS.
"""

import subprocess
import time

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib

from claudy.content.app_reactions import LINUX_APPS, match_linux_process
from claudy.log import log

POLL_SECONDS = 3
# Don't react to the same app again within this many seconds
APP_COOLDOWN_S = 60


class SystemEventHandler:
    """Feeds system events to the controller."""

    def __init__(self, controller):
        self.controller = controller
        self._running_apps = self._scan_apps() or set()
        self._last_reaction = {}  # app key -> time of the last reaction
        self._subscribe_sleep_wake()
        GLib.timeout_add_seconds(POLL_SECONDS, self._check_new_apps)

    def _subscribe_sleep_wake(self):
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            bus.signal_subscribe(
                "org.freedesktop.login1",
                "org.freedesktop.login1.Manager",
                "PrepareForSleep",
                "/org/freedesktop/login1",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_prepare_for_sleep,
                None,
            )
        except GLib.Error:
            log.info("logind unavailable; sleep/wake events disabled")

    def _on_prepare_for_sleep(self, conn, sender, path, iface, signal, params, data):
        going_to_sleep = params.unpack()[0]
        if going_to_sleep:
            self.controller.on_system_sleep()
        else:
            self.controller.on_system_wake()

    @staticmethod
    def _scan_apps():
        """Keys of known apps currently running, or None if ps failed."""
        try:
            out = subprocess.check_output(
                ["ps", "ax", "-o", "comm="], text=True, timeout=2)
        except (OSError, subprocess.SubprocessError):
            return None
        keys = (match_linux_process(line.strip()) for line in out.splitlines())
        return {key for key in keys if key}

    def _check_new_apps(self):
        running = self._scan_apps()
        if running is None:
            return True
        now = time.time()
        for key in running - self._running_apps:
            if now - self._last_reaction.get(key, 0) < APP_COOLDOWN_S:
                continue
            self._last_reaction[key] = now
            try:
                self.controller.on_app_launched(key, LINUX_APPS[key], key)
            except Exception:
                log.exception("failed to react to %s", key)
        self._running_apps = running
        return True  # keep polling
