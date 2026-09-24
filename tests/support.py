"""Shared helpers for the test suite."""

import random
from unittest import mock

import memory
import settings

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
        result = character.update(step)
        events.extend(result["events"])
        elapsed += step
    return events


def run_until_idle(character, limit_ms=15 * 60 * 1000, step=50, on_tick=None):
    """Advance until the character returns to idle. Returns (elapsed, events)."""
    events = []
    elapsed = 0
    while elapsed < limit_ms:
        result = character.update(step)
        events.extend(result["events"])
        if on_tick:
            on_tick(result)
        elapsed += step
        if character.state == "idle":
            return elapsed, events
    raise AssertionError(
        f"still in state {character.state!r} after {limit_ms} ms")


def fixed_period(period):
    """Patch the schedule so every lookup reports `period`."""
    return mock.patch("schedule.get_period", return_value=period)


def seeded(seed=1234):
    random.seed(seed)
