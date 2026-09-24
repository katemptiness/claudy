"""Shared helpers for the test suite."""

import random
from unittest import mock

from claudy.core import memory, settings
from claudy.core.controller import Platform

SCREEN_WIDTH = 1440


def reset_singletons():
    """Start each test from fresh Settings/Memory with default values."""
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
