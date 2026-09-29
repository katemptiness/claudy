"""Shared helpers for the test suite."""

import os
import random
from unittest import mock

from claudy.core import memory, settings
from claudy.core.controller import Platform
from tests import TEST_HOME_PREFIX

SCREEN_WIDTH = 1440


def _require_temp_home():
    """Refuse to run against the user's real ~/.claudy.

    tests/__init__.py points CLAUDY_HOME at a throwaway directory, but only
    when the suite is imported as the `tests` package before any Claudy
    module. Run another way (`unittest discover tests`, a test file run on
    its own, a script that execs the tests), the data files resolve to the
    real home, and the reset below would delete the user's memory.
    """
    home = os.path.dirname(memory.MEMORY_FILE)
    if not os.path.basename(home).startswith(TEST_HOME_PREFIX):
        raise RuntimeError(
            f"tests would touch {home}; run them from the project root with "
            "`python3 -m unittest discover -s tests -t .`")


def reset_singletons():
    """Start each test from fresh Settings/Memory with default values.

    The data files go too. A couple of things in memory outlive a session
    on purpose (the first launch date, the star Claudy named), saved
    settings are read back at the next start, and the whole suite shares one
    CLAUDY_HOME, so one test's star or setting would otherwise turn up in
    the next.
    """
    _require_temp_home()
    for path in (memory.MEMORY_FILE, settings.SETTINGS_FILE):
        try:
            os.remove(path)
        except OSError:
            pass
    settings.Settings._instance = None
    memory.Memory._instance = None
    settings.Settings.shared().language = "ru"


def attach(mem=None):
    """Click enough times today to unlock attachment-gated behavior."""
    mem = mem or memory.Memory.shared()
    while not mem.is_attached():
        mem.record_click()


def run(character, ms, step=50):
    """Advance the character by `ms` milliseconds; return all events emitted."""
    events = []
    elapsed = 0
    while elapsed < ms:
        character.update(step)
        events.extend(character.take_events())
        elapsed += step
    return events


def run_until_idle(character, limit_ms=15 * 60 * 1000, step=50, on_tick=None):
    """Advance until the character returns to idle. Returns (elapsed, events)."""
    events = []
    elapsed = 0
    while elapsed < limit_ms:
        view = character.update(step)
        events.extend(character.take_events())
        if on_tick:
            on_tick(view)
        elapsed += step
        if character.state == "idle":
            return elapsed, events
    raise AssertionError(
        f"still in state {character.state!r} after {limit_ms} ms")


def fixed_period(period):
    """Patch the schedule so every lookup reports `period`."""
    return mock.patch("claudy.core.schedule.get_period", return_value=period)


def dark_sky(dark=True):
    """Patch the clock so the named star is (or isn't) in the sky."""
    return mock.patch("claudy.core.schedule.is_dark", return_value=dark)


def fixed_weights(weights):
    return mock.patch("claudy.core.schedule.get_weights", return_value=weights)


def seeded(seed=1234):
    random.seed(seed)


class FakePlatform(Platform):
    """Records what the controller asks the backend to do."""

    def __init__(self):
        self.opened = []

    def open_claude(self):
        self.opened.append("claude")

    def open_claude_code(self):
        self.opened.append("claude_code")

    def open_settings(self):
        self.opened.append("settings")

    def open_gifts(self):
        self.opened.append("gifts")

    def show_about(self):
        self.opened.append("about")

    def quit(self):
        self.opened.append("quit")


def record_speech(controller):
    """Log every line `controller` says and every time the bubble hides.

    Returns (said, hidden): a list of texts and a one-item hide counter.
    """
    said, hidden = [], [0]
    speech = controller.speech
    say, hide = speech.say, speech.hide

    def logged_say(text):
        said.append(text)
        say(text)

    def logged_hide():
        if speech.visible and not speech._fading_out:
            hidden[0] += 1
        hide()

    speech.say, speech.hide = logged_say, logged_hide
    return said, hidden
