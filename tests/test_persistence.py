"""Tests for Settings and Memory persistence."""

import io
import json
import logging
import logging.handlers
import os
import sys
import threading
import unittest
from unittest import mock

from claudy import log
from claudy.content import ui_text
from claudy.core import memory, settings
from tests import support


def write_file(path, content):
    """Put `content` (bytes, or anything JSON can hold) at `path`."""
    if not isinstance(content, bytes):
        content = json.dumps(content, ensure_ascii=False).encode("utf-8")
    with open(path, "wb") as f:
        f.write(content)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


class SettingsTests(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        if os.path.exists(settings.SETTINGS_FILE):
            os.remove(settings.SETTINGS_FILE)
        support.reset_singletons()

    def test_defaults(self):
        s = settings.Settings.shared()
        self.assertEqual(s.schedule, "owl")
        self.assertEqual(s.dock_icons, 13)
        self.assertEqual(s.vertical_offset, 0)
        self.assertEqual(s.star_height, 160)

    def test_numeric_settings_are_clamped(self):
        s = settings.Settings.shared()
        s.vertical_offset = 999
        self.assertEqual(s.vertical_offset, settings.VERTICAL_OFFSET_MAX)
        s.vertical_offset = "nonsense"
        self.assertEqual(s.vertical_offset, 0)
        s.dock_icons = -3
        self.assertEqual(s.dock_icons, settings.DOCK_ICONS_MIN)
        s.dock_icons = 7.6
        self.assertEqual(s.dock_icons, 8)
        s.star_height = 10
        self.assertEqual(s.star_height, settings.STAR_HEIGHT_MIN)

    def test_save_and_reload(self):
        s = settings.Settings.shared()
        s.user_name = "Катя"
        s.schedule = "lark"
        s.save()
        settings.Settings._instance = None
        reloaded = settings.Settings.shared()
        self.assertEqual(reloaded.user_name, "Катя")
        self.assertEqual(reloaded.schedule, "lark")

    def test_corrupt_file_falls_back_to_defaults(self):
        os.makedirs(os.path.dirname(settings.SETTINGS_FILE), exist_ok=True)
        with open(settings.SETTINGS_FILE, "w") as f:
            f.write("{not json")
        settings.Settings._instance = None
        self.assertEqual(settings.Settings.shared().schedule, "owl")

    def test_unknown_keys_are_ignored(self):
        with open(settings.SETTINGS_FILE, "w") as f:
            json.dump({"schedule": "lark", "bogus": 1}, f)
        settings.Settings._instance = None
        s = settings.Settings.shared()
        self.assertEqual(s.schedule, "lark")
        self.assertNotIn("bogus", s._data)

    def test_hand_edited_junk_falls_back_to_the_defaults(self):
        """Each setting checks its own value once, so nothing downstream
        trips over a string where a number belongs, or an option that no
        longer exists."""
        write_file(settings.SETTINGS_FILE, b'''{
            "speech_interval": ["1m"], "gift_duration": "2h",
            "gift_cooldown": null, "schedule": "bat", "language": "de",
            "terminal": 5, "dev_mode": "false", "user_name": 5,
            "gift_limit": "a lot", "dock_icons": 1e999}''')
        settings.Settings._instance = None
        s = settings.Settings.shared()
        defaults = {name: field.default
                    for name, field in settings.Settings.fields().items()}
        for name in ("speech_interval", "gift_duration", "gift_cooldown",
                     "schedule", "language", "terminal", "dev_mode",
                     "user_name", "gift_limit", "dock_icons"):
            with self.subTest(setting=name):
                self.assertEqual(getattr(s, name), defaults[name])
                self.assertEqual(s._data[name], defaults[name])
        self.assertEqual(s.speech_cooldown_range(),
                         settings.SPEECH_COOLDOWNS["1m"])
        self.assertEqual(s.gift_duration_seconds(), 300)
        self.assertEqual(s.gift_cooldown_seconds(), 600)

    def test_a_gift_limit_is_a_count(self):
        s = settings.Settings.shared()
        s.gift_limit = "5"
        self.assertEqual(s.gift_limit, 5)
        s.gift_limit = 0
        self.assertEqual(s.gift_limit, 0)       # no limit
        s.gift_limit = -4
        self.assertEqual(s.gift_limit, 0)

    def test_every_option_the_windows_offer_is_a_valid_setting(self):
        """The settings windows list the options from ui_text, and the
        tables here turn them into numbers: the two must agree."""
        tables = (
            (ui_text.SPEECH_OPTIONS, settings.SPEECH_COOLDOWNS),
            (ui_text.GIFT_DURATION_OPTIONS, settings.GIFT_DURATIONS),
            (ui_text.GIFT_COOLDOWN_OPTIONS, settings.GIFT_COOLDOWNS),
        )
        for options, table in tables:
            self.assertEqual(sorted(o[0] for o in options), sorted(table))
        for name, field in settings.Settings.fields().items():
            if hasattr(field, "choices"):
                with self.subTest(setting=name):
                    self.assertIn(field.default, field.choices)
                    for choice in field.choices:
                        self.assertEqual(field.coerce(choice), choice)

    def test_text_that_is_not_utf8_does_not_stop_the_launch(self):
        """A write cut off inside a Cyrillic letter, or a hand edit saved
        in another encoding: defaults, and the file kept for the user."""
        broken = '{"user_name": "Катя'.encode("utf-8")[:-1]
        write_file(settings.SETTINGS_FILE, broken)
        settings.Settings._instance = None
        with self.assertLogs("claudy", level="ERROR"):
            s = settings.Settings.shared()
        self.assertEqual(s.user_name, "")
        self.assertEqual(read_bytes(settings.SETTINGS_FILE + ".bad"), broken)

    def test_save_replaces_the_file_whole(self):
        s = settings.Settings.shared()
        s.user_name = "Катя"
        s.save()
        self.assertFalse(os.path.exists(settings.SETTINGS_FILE + ".tmp"))
        with open(settings.SETTINGS_FILE, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["user_name"], "Катя")

    def test_a_failed_save_is_logged_and_keeps_the_old_file(self):
        """The Save button must still close its window, and a disk that
        filled up mid-write must not leave half a settings file."""
        s = settings.Settings.shared()
        s.schedule = "lark"
        s.save()
        before = read_bytes(settings.SETTINGS_FILE)
        s.schedule = "owl"
        with mock.patch("os.replace", side_effect=OSError(28, "No space")), \
                self.assertLogs("claudy", level="ERROR"):
            s.save()
        self.assertEqual(read_bytes(settings.SETTINGS_FILE), before)


class MemoryTests(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        self.mem = memory.Memory.shared()

    def test_attachment_needs_enough_clicks(self):
        for _ in range(memory.ATTACHMENT_THRESHOLD - 1):
            self.mem.record_click()
        self.assertFalse(self.mem.is_attached())
        self.mem.record_click()
        self.assertTrue(self.mem.is_attached())

    def test_gift_lifecycle(self):
        self.assertIsNone(self.mem.get_pending_gift())
        self.mem.add_gift("fish", "🐟")
        pending = self.mem.get_pending_gift()
        self.assertEqual(pending["emoji"], "🐟")
        self.assertEqual(self.mem.get_collected_gifts(), [])
        self.mem.collect_gift()
        self.assertIsNone(self.mem.get_pending_gift())
        self.assertEqual(len(self.mem.get_collected_gifts()), 1)

    def test_expired_gift_is_discarded(self):
        """An unclaimed gift is gone, and doesn't use up the day's limit."""
        self.mem.add_gift("shell", "🐚")
        self.mem.discard_pending_gift()
        self.assertIsNone(self.mem.get_pending_gift())
        self.assertEqual(self.mem.get_collected_gifts(), [])
        self.assertEqual(self.mem.count_gifts_today(), 0)

    def test_the_named_star_is_not_one_of_the_days_gifts(self):
        """The star joins the collection dated today, but naming it must
        not use up a gift the user could still get: with a limit of one,
        that would be the day's only gift."""
        self.mem.add_gift("star", "⭐", name="Kate", collected=True)
        self.mem.name_star("Kate")
        self.assertEqual(self.mem.count_gifts_today(), 0)
        self.mem.add_gift("fish", "🐟")
        self.assertEqual(self.mem.count_gifts_today(), 1)

    def test_collected_gifts_are_newest_first(self):
        for emoji in ("🐟", "🐡"):
            self.mem.add_gift("fish", emoji)
            self.mem.collect_gift()
        self.assertEqual(
            [g["emoji"] for g in self.mem.get_collected_gifts()], ["🐡", "🐟"])

    def test_the_activity_log_forgets_the_oldest(self):
        for i in range(memory.ACTIVITY_LOG + 10):
            self.mem.log_activity("reading" if i % 2 else "fishing")
        self.assertEqual(len(self.mem.recent_activities()), memory.ACTIVITY_LOG)

    def test_a_night_of_waking_up_counts_as_one_sleep(self):
        """Every click in the night wakes Claudy, and deep sleep offers
        nothing but "sleeping" again; unchecked, all those returns
        to sleep would crowd what he could dream of out of the log."""
        self.mem.log_activity("fishing")
        for _ in range(100):
            self.mem.log_activity("sleeping")
        self.assertEqual(self.mem.recent_activities(), ["fishing", "sleeping"])

    def test_the_named_star_outlives_the_session(self):
        """Claudy put it in the sky, so it has to survive a relaunch —
        unlike everything else in this file."""
        self.mem.name_star("Kate")
        memory.Memory._instance = None
        fresh = memory.Memory.shared()
        self.assertEqual(fresh.get_star()["name"], "Kate")

    def test_a_broken_star_is_dropped_on_load(self):
        """A hand edit gone wrong must not crash every night frame that
        places the star, nor stop Claudy from ever naming a real one."""
        for broken in ("Kate", {"date": "2026-09-25"}, {"name": None}, {}, []):
            with self.subTest(star=broken):
                write_file(memory.MEMORY_FILE, {"star": broken})
                memory.Memory._instance = None
                self.assertIsNone(memory.Memory.shared().get_star())

    def test_a_star_with_a_broken_date_keeps_its_name(self):
        write_file(memory.MEMORY_FILE, {"star": {"name": "Kate", "date": 5}})
        memory.Memory._instance = None
        self.assertEqual(memory.Memory.shared().get_star(),
                         {"name": "Kate", "date": None})

    def test_a_star_named_by_an_older_build_is_kept(self):
        """Before the star had a key of its own it was only a gift. This is
        the file such a build leaves behind, star and all."""
        write_file(memory.MEMORY_FILE, {
            "first_launch": "2026-09-25",
            "total_days": 5,
            "today": {"date": "2026-09-29", "clicks": 12,
                      "app_launches": {"firefox": 3},
                      "days_phrase_shown": True},
            "gifts": [
                {"type": "fish", "emoji": "🐟", "date": "2026-09-25",
                 "collected": True, "story_id": 4},
                {"type": "star", "emoji": "⭐", "date": "2026-09-25",
                 "collected": True, "story_id": 11, "name": "katemptiness"},
            ],
        })
        memory.Memory._instance = None
        star = {"name": "katemptiness", "date": "2026-09-25"}
        self.assertEqual(memory.Memory.shared().get_star(), star)
        # ...and it is now saved where the next launch looks for it
        memory.Memory._instance = None
        self.assertEqual(memory.Memory.shared().get_star(), star)
        self.assertEqual(memory.Memory.shared()._data["first_launch"],
                         "2026-09-25")

    def test_an_older_star_named_for_nobody_is_kept_too(self):
        """Without a user name the gift was stored with no name at all."""
        write_file(memory.MEMORY_FILE, {"gifts": [
            {"type": "star", "emoji": "⭐", "date": "2026-09-25",
             "collected": True, "story_id": 0}]})
        memory.Memory._instance = None
        self.assertEqual(memory.Memory.shared().get_star(),
                         {"name": "", "date": "2026-09-25"})

    def test_an_unreadable_file_is_set_aside_not_overwritten(self):
        """A trailing comma from renaming the star by hand must not cost
        the star: the file moves to memory.json.bad before Claudy starts
        fresh."""
        for content in (b'{"star": {"name": "Kate",},}',
                        b'{"star": {"name": "\xd0"}}',
                        b'["not", "an", "object"]'):
            with self.subTest(content=content):
                write_file(memory.MEMORY_FILE, content)
                memory.Memory._instance = None
                with self.assertLogs("claudy", level="ERROR"):
                    fresh = memory.Memory.shared()
                self.assertIsNone(fresh.get_star())
                self.assertEqual(read_bytes(memory.MEMORY_FILE + ".bad"),
                                 content)
                with open(memory.MEMORY_FILE, encoding="utf-8") as f:
                    self.assertIsNone(json.load(f)["star"])

    def test_each_launch_starts_a_fresh_session(self):
        self.mem.record_click()
        self.mem.add_gift("fish", "🐟")
        memory.Memory._instance = None
        fresh = memory.Memory.shared()
        self.assertEqual(fresh.get_clicks_today(), 0)
        self.assertEqual(fresh.get_total_days(), 1)
        self.assertIsNone(fresh.get_pending_gift())

    def test_app_launches_are_counted(self):
        self.assertEqual(self.mem.record_app_launch("firefox"), 1)
        self.assertEqual(self.mem.record_app_launch("firefox"), 2)
        self.assertEqual(self.mem.record_app_launch("kitty"), 1)


def failing_frame(message="tick failed", value=1):
    """A log record like the frame loop's, raised from the same line."""
    try:
        raise ValueError(value)
    except ValueError:
        return logging.LogRecord("claudy", logging.ERROR, __file__, 0,
                                 message, (), sys.exc_info())


class ErrorLogTests(unittest.TestCase):

    def setUp(self):
        # install_excepthook() swaps both hooks for the whole process. Put
        # them back, or every later test would run with them installed,
        # stacked once more by each test here that installs them.
        self.addCleanup(setattr, sys, "excepthook", sys.excepthook)
        self.addCleanup(setattr, threading, "excepthook", threading.excepthook)

    def test_reported_logs_and_prints_what_a_callback_raises(self):
        """AppKit swallows what a callback raises; reported() gets it into
        the log (and the terminal) and lets the app carry on."""
        with mock.patch.object(log.log, "exception") as logged, \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            with log.reported("click"):
                raise ValueError("boom")
        logged.assert_called_once_with("%s failed", "click")
        self.assertIn("ValueError: boom", err.getvalue())

    def test_a_repeating_error_is_written_once_then_counted(self):
        """A bug hit on every frame logs sixty tracebacks a second; the
        log keeps the first and then says how often it came back."""
        now = [0.0]
        repeats = log.RepeatFilter(interval_s=600, clock=lambda: now[0])
        self.assertTrue(repeats.filter(failing_frame()))
        for frame in range(1, 600):
            now[0] = frame / 60
            # the exception text may change from frame to frame
            self.assertFalse(repeats.filter(failing_frame(value=frame)))
        now[0] = 600.0
        summary = failing_frame()
        self.assertTrue(repeats.filter(summary))
        self.assertIsNone(summary.exc_info)
        self.assertEqual(summary.getMessage(),
                         "tick failed (again, 600 more times in the last "
                         "10 min)")
        # A different failure is news, and goes in straight away
        self.assertTrue(repeats.filter(failing_frame("menu action failed")))

    def test_an_error_that_does_not_repeat_keeps_its_traceback(self):
        now = [0.0]
        repeats = log.RepeatFilter(interval_s=600, clock=lambda: now[0])
        self.assertTrue(repeats.filter(failing_frame()))
        now[0] = 3600.0
        again = failing_frame()
        self.assertTrue(repeats.filter(again))
        self.assertIsNotNone(again.exc_info)

    def test_the_log_file_is_capped(self):
        handler = log.log.handlers[0]
        self.assertIsInstance(handler, logging.handlers.RotatingFileHandler)
        self.assertEqual(handler.maxBytes, log.LOG_MAX_BYTES)
        self.assertTrue(any(isinstance(f, log.RepeatFilter)
                            for f in handler.filters))

    def test_uncaught_exceptions_are_logged_and_still_printed(self):
        printed = mock.Mock()
        with mock.patch.object(sys, "excepthook", printed):
            log.install_excepthook()
            try:
                raise RuntimeError("no window")
            except RuntimeError:
                exc_info = sys.exc_info()
            with self.assertLogs("claudy", level="ERROR") as logged:
                sys.excepthook(*exc_info)
        printed.assert_called_once_with(*exc_info)
        self.assertIn("RuntimeError: no window", logged.output[0])

    def test_installing_twice_logs_once(self):
        with mock.patch.object(sys, "excepthook", mock.Mock()):
            log.install_excepthook()
            log.install_excepthook()
            with self.assertLogs("claudy", level="ERROR") as logged:
                sys.excepthook(RuntimeError, RuntimeError("once"), None)
        self.assertEqual(len(logged.output), 1)

    def test_ctrl_c_is_not_an_error(self):
        printed = mock.Mock()
        with mock.patch.object(sys, "excepthook", printed), \
                mock.patch.object(log.log, "error") as error:
            log.install_excepthook()
            sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
        error.assert_not_called()
        printed.assert_called_once()

    def test_uncaught_exceptions_in_threads_are_logged(self):
        printed = mock.Mock()
        with mock.patch.object(threading, "excepthook", printed):
            log.install_excepthook()
            with self.assertLogs("claudy", level="ERROR") as logged:
                worker = threading.Thread(target=lambda: 1 / 0, name="poll")
                worker.start()
                worker.join()
        printed.assert_called_once()
        self.assertIn("thread poll", logged.output[0])


if __name__ == "__main__":
    unittest.main()
