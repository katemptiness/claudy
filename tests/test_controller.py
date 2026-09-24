"""Tests for the shared application controller and particles."""

import unittest
from unittest import mock

from claudy.content import app_reactions
from claudy.core.controller import Controller, MenuItem
from claudy.core.memory import Memory
from claudy.core.particles import ParticleSystem
from claudy.core.settings import Settings
from tests import support


class ControllerTestCase(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        support.seeded()
        self.period = support.fixed_period("day")
        self.period.start()
        self.addCleanup(self.period.stop)
        self.platform = support.FakePlatform()
        self.ctl = Controller(self.platform, support.SCREEN_WIDTH, 58)
        self.advance(4000)  # finish waking up
        self._said, self._hidden = support.record_speech(self.ctl)

    def advance(self, ms, step=50):
        for _ in range(int(ms / step)):
            self.ctl.tick(step)

    def said(self):
        return self._said

    @property
    def hidden(self):
        return self._hidden[0]

    def offer_gift(self):
        self.ctl._offer_gift({"type": "fish", "emoji": "🐟"})


class StartupTests(unittest.TestCase):

    def test_claudy_wakes_up_with_a_yawn(self):
        support.reset_singletons()
        platform = support.FakePlatform()
        ctl = Controller(platform, support.SCREEN_WIDTH, 58)
        said, _ = support.record_speech(ctl)
        self.assertEqual(ctl.view["sprite"], "sleep_a")
        for _ in range(80):
            ctl.tick(50)
        self.assertIn("*зевает*", said)
        self.assertEqual(ctl.character.state, "idle")


class GiftTests(ControllerTestCase):

    def test_offered_gift_pins_speech_and_pauses_claudy(self):
        self.offer_gift()
        self.assertEqual(self.ctl.gift_emoji, "🐟")
        self.assertTrue(self.ctl.character.gift_waiting)
        # Other lines can't replace the announcement while it lasts
        self.ctl._say("что-то ещё")
        self.advance(60_000)
        self.assertNotIn("что-то ещё", self.said())
        self.assertEqual(self.hidden, 0)

    def test_click_collects_the_gift(self):
        self.offer_gift()
        self.ctl.on_click()
        self.assertIsNone(self.ctl.gift_emoji)
        self.assertFalse(self.ctl.character.gift_waiting)
        self.assertEqual(len(Memory.shared().get_collected_gifts()), 1)
        self.assertEqual(self.hidden, 1)
        self.assertEqual(self.ctl.character.state, "reaction_happy")

    def test_unclaimed_gift_expires(self):
        self.offer_gift()
        self.advance(Settings.shared().gift_duration_seconds() * 1000 + 100)
        self.assertIsNone(self.ctl.gift_emoji)
        self.assertEqual(self.hidden, 1)
        self.assertIsNone(Memory.shared().get_pending_gift())
        self.assertEqual(Memory.shared().get_collected_gifts(), [])

    def test_one_gift_at_a_time_and_daily_limit(self):
        Settings.shared().gift_limit = 2
        self.offer_gift()
        self.ctl._offer_gift({"type": "shell", "emoji": "🐚"})
        self.assertEqual(self.ctl.gift_emoji, "🐟")
        self.ctl.on_click()
        self.offer_gift()
        self.ctl.on_click()
        self.offer_gift()
        self.assertIsNone(self.ctl.gift_emoji)

    def test_activity_gift_events_reach_the_controller(self):
        support.attach()
        with mock.patch("claudy.core.character.random.random", return_value=0.0):
            self.ctl.character.force_activity("shell_collecting")
            self.advance(30_000)
        self.assertEqual(self.ctl.gift_emoji, "🐚")


class SpeechTests(ControllerTestCase):

    def test_click_greets_out_loud(self):
        self.ctl.on_click()
        self.advance(100)
        self.assertTrue(self.said())
        self.assertEqual(self.ctl.character.state, "reaction_happy")

    def test_idle_chatter_is_rate_limited(self):
        self.ctl._say("раз")
        self.ctl._say("два", chatter=True)
        self.assertEqual(self.said(), ["раз"])
        self.advance(3100)
        self.ctl._say("три", chatter=True)
        self.assertEqual(self.said()[-1], "три")

    def test_speech_hides_after_reading_time(self):
        self.ctl._say("привет")
        typing = len("привет") * 30
        self.advance(typing + 1900)
        self.assertEqual(self.hidden, 0)
        self.assertEqual(self.ctl.speech.shown_text, "привет")
        self.advance(200)
        self.assertEqual(self.hidden, 1)
        self.advance(400)
        self.assertFalse(self.ctl.speech.visible)

    def test_text_types_out(self):
        self.ctl._say("привет")
        self.ctl.tick(1)
        self.assertEqual(self.ctl.speech.shown_text, "п")
        self.assertTrue(self.ctl.speech.typing)
        self.advance(100)
        self.assertEqual(self.ctl.speech.shown_text, "прив")
        self.advance(100)
        self.assertFalse(self.ctl.speech.typing)

    def test_double_click_opens_claude(self):
        self.ctl.on_double_click()
        self.assertEqual(self.platform.opened, ["claude"])


class SystemEventTests(ControllerTestCase):

    def test_opening_a_terminal_starts_work(self):
        app = app_reactions.LINUX_APPS["gnome-terminal"]
        self.ctl.on_app_launched("gnome-terminal", app, "gnome-terminal")
        self.assertEqual(self.ctl.character.state, "working")
        self.assertTrue(self.said())

    def test_unknown_app_is_only_counted(self):
        self.ctl.on_app_launched("com.example.unknown")
        self.assertEqual(self.said(), [])
        self.assertEqual(
            Memory.shared().get_app_launches_today("com.example.unknown"), 1)

    def test_sleep_and_wake(self):
        self.ctl.on_system_sleep()
        self.assertEqual(self.ctl.character.state, "sleeping")
        self.ctl.on_system_wake()
        self.assertEqual(self.ctl.character.state, "waking")


class MenuTests(ControllerTestCase):

    def _find(self, items, label):
        for item in items:
            if item.label == label:
                return item
        raise AssertionError(f"no menu item {label!r}")

    def test_menu_actions(self):
        items = self.ctl.menu()
        self._find(items, "Настройки").action()
        self._find(items, "Выход").action()
        self.assertEqual(self.platform.opened, ["settings", "quit"])

    def test_dev_menu_only_in_dev_mode(self):
        labels = [i.label for i in self.ctl.menu()]
        self.assertNotIn("Активности", labels)
        Settings.shared().dev_mode = True
        dev = self._find(self.ctl.menu(), "Активности")
        self._find(dev.submenu, "Fishing").action()
        self.assertEqual(self.ctl.character.state, "fishing")

    def test_giving_a_toy_marks_it_owned(self):
        gifts = self._find(self.ctl.menu(), "Подарить подарок").submenu
        self._find(gifts, "Игрушку 🧸").action()
        self.assertTrue(self.ctl.character.has_toy)
        gifts = self._find(self.ctl.menu(), "Подарить подарок").submenu
        toy = self._find(gifts, "Игрушку 🧸 ✓")
        self.assertFalse(toy.enabled)
        self.assertIsInstance(gifts[-1], MenuItem)
        self.assertFalse(gifts[-1].enabled)  # "wait a bit" while cooling down


class ParticleTests(unittest.TestCase):

    def test_particles_rise_fade_and_die(self):
        system = ParticleSystem()
        system.add("heart", 100, 80)
        p = system.get_active()[0]
        y0 = p.y
        system.update(500)
        self.assertGreater(p.y, y0)
        self.assertLess(p.opacity, 1.0)
        system.update(1000)
        self.assertEqual(system.get_active(), [])

    def test_sweat_drips_down(self):
        system = ParticleSystem()
        system.add("sweat", 100, 80)
        p = system.get_active()[0]
        y0 = p.y
        system.update(300)
        self.assertLess(p.y, y0)

    def test_movement_does_not_depend_on_frame_rate(self):
        a, b = ParticleSystem(), ParticleSystem()
        support.seeded(7)
        a.add("zzz", 100, 80)
        support.seeded(7)
        b.add("zzz", 100, 80)
        for _ in range(60):
            a.update(1000 / 60)
        for _ in range(30):
            b.update(1000 / 30)
        pa, pb = a.get_active()[0], b.get_active()[0]
        self.assertAlmostEqual(pa.y, pb.y, places=3)

    def test_unknown_kind_is_ignored(self):
        system = ParticleSystem()
        system.add("unicorn", 0, 0)
        self.assertEqual(system.get_active(), [])


if __name__ == "__main__":
    unittest.main()
