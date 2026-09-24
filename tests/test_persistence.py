"""Tests for Settings and Memory persistence."""

import json
import os
import unittest

import memory
import settings
from tests import support


class SettingsTests(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        if os.path.exists(settings.SETTINGS_FILE):
            os.remove(settings.SETTINGS_FILE)
        support.reset_singletons()

    def test_defaults(self):
        s = settings.Settings.shared()
        self.assertEqual(s.schedule, "owl")
        self.assertEqual(s.dock_icons, settings.DEFAULTS["dock_icons"])
        self.assertEqual(s.vertical_offset, 0)

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
        self.mem.add_gift("shell", "🐚")
        self.mem.discard_pending_gift()
        self.assertIsNone(self.mem.get_pending_gift())
        self.assertEqual(self.mem.count_session_gifts("shell"), 0)

    def test_collected_gifts_are_newest_first(self):
        for emoji in ("🐟", "🐡"):
            self.mem.add_gift("fish", emoji)
            self.mem.collect_gift()
        self.assertEqual(
            [g["emoji"] for g in self.mem.get_collected_gifts()], ["🐡", "🐟"])

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
        self.assertEqual(self.mem.get_app_launches_today("firefox"), 2)


if __name__ == "__main__":
    unittest.main()
