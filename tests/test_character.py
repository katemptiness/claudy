"""Behavioral tests for the Character state machine."""

import unittest
from unittest import mock

import character
from character import Character
from sprites.activities import ALL as ACTIVITY_SPRITES
from sprites.base import ALL as BASE_SPRITES
from tests import support

ALL_SPRITES = {**BASE_SPRITES, **ACTIVITY_SPRITES}


def _event_types(events):
    return [etype for etype, _ in events]


class CharacterTestCase(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        support.seeded()
        self.period = support.fixed_period("day")
        self.period.start()
        self.addCleanup(self.period.stop)
        self.char = Character(support.SCREEN_WIDTH)


class ActivityRunTests(CharacterTestCase):

    def _run_activity(self, name):
        self.char.trigger_activity(name)
        self.assertEqual(self.char.state, name)
        seen_sprites = set()

        def check(result):
            seen_sprites.add(result["sprite"])
            self.assertGreaterEqual(result["x"], self.char.walk_min_x - 1)
            self.assertLessEqual(result["x"], self.char.walk_max_x + 1)

        _, events = support.run_until_idle(self.char, on_tick=check)
        for sprite in seen_sprites:
            self.assertIn(sprite, ALL_SPRITES)
        return events

    def test_every_activity_finishes_and_returns_to_idle(self):
        for name in character.ACTIVITIES:
            for attached in (False, True):
                with self.subTest(activity=name, attached=attached):
                    support.reset_singletons()
                    if attached:
                        support.attach()
                    self.char = Character(support.SCREEN_WIDTH)
                    self._run_activity(name)

    def test_activities_emit_messages(self):
        events = self._run_activity("reading")
        self.assertIn("message", _event_types(events))
        self.assertIn("particle", _event_types(events))

    def test_summoning_brings_a_friend_and_sends_it_home(self):
        visible = []
        self.char.trigger_activity("summoning")
        _, events = support.run_until_idle(
            self.char, on_tick=lambda r: visible.append(r["friend_visible"]))
        types = _event_types(events)
        self.assertIn("friend_appear", types)
        self.assertIn("friend_leave", types)
        self.assertTrue(any(visible))
        self.assertFalse(self.char.friend_visible)

    def test_sleeping_loops_during_deep_sleep(self):
        with support.fixed_period("deep_sleep"):
            self.char.trigger_activity("sleeping")
            support.run(self.char, 60_000)
            self.assertEqual(self.char.state, "sleeping")

    def test_sleeping_is_a_short_nap_during_the_day(self):
        self.char.trigger_activity("sleeping")
        elapsed, _ = support.run_until_idle(self.char)
        self.assertLess(elapsed, 30_000)

    def test_trigger_does_not_interrupt_a_running_activity(self):
        self.char.trigger_activity("reading")
        self.char.trigger_activity("music")
        self.assertEqual(self.char.state, "reading")

    def test_unknown_activity_is_ignored(self):
        self.char.trigger_activity("skydiving")
        self.assertEqual(self.char.state, "idle")


class IdleAndWalkingTests(CharacterTestCase):

    def test_idle_eventually_picks_something_else(self):
        with mock.patch.object(character, "get_weights",
                               return_value={"reading": 1.0}):
            support.run(self.char, 21_000)
        self.assertEqual(self.char.state, "reading")

    def test_recent_activities_are_not_repeated(self):
        weights = {"reading": 0.4, "music": 0.3, "painting": 0.3}
        with mock.patch.object(character, "get_weights", return_value=weights):
            picks = []
            for _ in range(6):
                self.char._enter_idle()
                self.char._pick_next_activity()
                picks.append(self.char.state)
        for a, b in zip(picks, picks[1:]):
            self.assertNotEqual(a, b)

    def test_gift_waiting_pauses_activity_changes(self):
        self.char.gift_waiting = True
        support.run(self.char, 60_000)
        self.assertEqual(self.char.state, "idle")

    def test_walking_stays_in_bounds_and_ends_idle(self):
        self.char.update_walk_bounds(10, 58)
        for _ in range(10):
            self.char._start_walking()
            support.run_until_idle(self.char, on_tick=lambda r: (
                self.assertGreaterEqual(r["x"], self.char.walk_min_x - 1),
                self.assertLessEqual(r["x"], self.char.walk_max_x + 1)))


class WalkBoundsTests(CharacterTestCase):

    def test_bounds_are_centered_on_screen(self):
        self.char.update_walk_bounds(10, 58)
        center = support.SCREEN_WIDTH / 2
        self.assertAlmostEqual(center - self.char.walk_min_x,
                               self.char.walk_max_x - center)
        self.assertLess(self.char.walk_min_x, center)

    def test_huge_dock_is_clamped_to_screen(self):
        self.char.update_walk_bounds(500, 58)
        self.assertEqual(self.char.walk_min_x, character.WINDOW_WIDTH)
        self.assertEqual(self.char.walk_max_x,
                         support.SCREEN_WIDTH - character.WINDOW_WIDTH)

    def test_tiny_dock_collapses_to_center(self):
        self.char.update_walk_bounds(0, 58)
        self.assertEqual(self.char.walk_min_x, self.char.walk_max_x)


class ReactionTests(CharacterTestCase):

    def test_click_reactions_return_to_idle(self):
        for reaction in ("happy", "happy_love", "wave", "surprise"):
            with self.subTest(reaction=reaction):
                self.char.interrupt(reaction)
                self.assertTrue(self.char.state.startswith("reaction_"))
                support.run_until_idle(self.char, limit_ms=5000)

    def test_happy_reaction_says_something_and_sparkles(self):
        self.char.interrupt("happy")
        events = self.char.events
        self.assertIn("message", _event_types(events))
        self.assertIn(("particle", "sparkle"), events)


class GiftReceivingTests(CharacterTestCase):

    def test_gift_is_accepted_then_cooldown_applies(self):
        self.assertTrue(self.char.receive_gift("flower"))
        self.assertEqual(self.char.state, "reaction_gift_received")
        self.assertFalse(self.char.can_receive_gift())
        self.assertFalse(self.char.receive_gift("song"))

    def test_toy_and_book_are_one_at_a_time(self):
        self.char.receive_gift("toy")
        self.char.last_gift_received_time = 0  # skip the cooldown
        self.assertFalse(self.char.can_accept_gift("toy"))
        self.assertTrue(self.char.can_accept_gift("book"))

    def test_marshmallow_is_eaten_at_the_campfire(self):
        self.char.receive_gift("marshmallow")
        support.run_until_idle(self.char, limit_ms=5000)
        self.assertTrue(self.char.has_marshmallow)
        self.char.trigger_activity("campfire")
        self.assertFalse(self.char.has_marshmallow)
        support.run_until_idle(self.char)

    def test_toy_shows_only_while_sleeping(self):
        self.char.receive_gift("toy")
        support.run_until_idle(self.char, limit_ms=5000)
        self.assertFalse(self.char.update(16)["show_toy"])
        self.char.trigger_activity("sleeping")
        self.assertTrue(self.char.update(16)["show_toy"])


if __name__ == "__main__":
    unittest.main()
