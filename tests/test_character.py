"""Behavioral tests for the Character state machine."""

import unittest

from claudy.content.sprites import SPRITES
from claudy.core import activities
from claudy.core.animations import Juggle
from claudy.core.character import Character
from tests import support


def _event_types(events):
    return [kind for kind, _ in events]


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

        def check(view):
            seen_sprites.add(view["sprite"])
            self.assertGreaterEqual(view["x"], self.char.walk_min_x - 1)
            self.assertLessEqual(view["x"], self.char.walk_max_x + 1)

        _, events = support.run_until_idle(self.char, on_tick=check)
        for sprite in seen_sprites:
            self.assertIn(sprite, SPRITES)
        return events

    def test_every_activity_finishes_and_returns_to_idle(self):
        for name in activities.ACTIVITIES:
            for attached in (False, True):
                with self.subTest(activity=name, attached=attached):
                    support.reset_singletons()
                    if attached:
                        support.attach()
                    self.char = Character(support.SCREEN_WIDTH)
                    self._run_activity(name)

    def test_activity_templates_are_not_modified_by_runs(self):
        before = {name: list(phases)
                  for name, phases in activities.ACTIVITIES.items()}
        self.char.has_marshmallow = True
        for name in ("fishing", "campfire", "summoning", "fishing"):
            for seed in range(5):
                support.seeded(seed)
                self.char.force_activity(name)
                support.run_until_idle(self.char)
        after = {name: list(phases)
                 for name, phases in activities.ACTIVITIES.items()}
        self.assertEqual(before, after)

    def test_activities_emit_messages(self):
        events = self._run_activity("reading")
        self.assertIn("message", _event_types(events))
        self.assertIn("particle", _event_types(events))

    def test_summoning_brings_a_friend_and_sends_it_home(self):
        visible = []
        self.char.trigger_activity("summoning")
        support.run_until_idle(
            self.char, on_tick=lambda v: visible.append(v["friend_visible"]))
        self.assertTrue(any(visible))
        self.assertFalse(self.char.friend_visible)

    def test_interrupted_visit_sends_the_friend_home(self):
        self.char.trigger_activity("summoning")
        support.run(self.char, 4000)
        self.assertTrue(self.char.friend_visible)
        self.char.greet(attached=False)
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

    def test_force_interrupts_a_running_activity(self):
        self.char.trigger_activity("reading")
        self.char.force_activity("music")
        self.assertEqual(self.char.state, "music")

    def test_unknown_activity_is_ignored(self):
        self.char.trigger_activity("skydiving")
        self.assertEqual(self.char.state, "idle")


class WakingTests(CharacterTestCase):

    def test_waking_up_yawns_then_idles(self):
        self.char.wake_up()
        self.assertEqual(self.char.sprite_name(), "sleep_a")
        elapsed, events = support.run_until_idle(self.char)
        self.assertIn(("message", "*зевает*"), events)
        self.assertGreaterEqual(elapsed, 3000)

    def test_attached_wake_up_is_personal(self):
        support.attach()
        self.char.wake_up()
        _, events = support.run_until_idle(self.char)
        self.assertNotIn(("message", "*зевает*"), events)
        self.assertIn("message", _event_types(events))

    def test_system_sleep(self):
        self.char.go_to_sleep()
        self.assertEqual(self.char.state, "sleeping")


class IdleAndWalkingTests(CharacterTestCase):

    def test_idle_eventually_picks_something_else(self):
        with support.fixed_weights({"reading": 1.0}):
            support.run(self.char, 21_000)
        self.assertEqual(self.char.state, "reading")

    def test_recent_activities_are_not_repeated(self):
        weights = {"reading": 0.4, "music": 0.3, "painting": 0.3}
        with support.fixed_weights(weights):
            picks = []
            for _ in range(6):
                self.char._enter_idle()
                self.char._pick_next_activity()
                picks.append(self.char.state)
        for a, b in zip(picks, picks[1:]):
            self.assertNotEqual(a, b)

    def test_gift_waiting_pauses_activity_changes(self):
        self.char.trigger_activity("reading")
        self.char.wait_for_gift(True)
        self.assertEqual(self.char.state, "idle")
        support.run(self.char, 60_000)
        self.assertEqual(self.char.state, "idle")

    def test_walking_stays_in_bounds_and_ends_idle(self):
        self.char.update_walk_bounds(10, 58)
        for _ in range(10):
            self.char._start_walking()
            support.run_until_idle(self.char, on_tick=lambda v: (
                self.assertGreaterEqual(v["x"], self.char.walk_min_x - 1),
                self.assertLessEqual(v["x"], self.char.walk_max_x + 1)))

    def test_idle_chatter(self):
        events = support.run(self.char, 80_000)
        self.assertIn("message", _event_types(events))


class PaintingTests(CharacterTestCase):

    def _painted_frames(self):
        self.char.force_activity("painting")
        return {frame for phase in self.char.phases for frame in phase.frames}

    def test_paints_a_different_picture_now_and_then(self):
        pictures = set()
        for _ in range(20):
            frames = self._painted_frames()
            done = [f for f in frames if f.endswith("_done")]
            self.assertEqual(len(done), 1)
            pictures.add(done[0])
            for frame in frames:
                self.assertIn(frame, SPRITES)
        self.assertEqual(len(pictures), len(activities.PAINTINGS))

    def test_the_picture_grows_stage_by_stage(self):
        self.char.force_activity("painting")
        canvases = []
        for phase in self.char.phases[1:-1]:
            grid = SPRITES[phase.frames[0]]
            canvases.append([row[25:30] for row in grid[3:8]])
        blank = [[5] * 5] * 5
        self.assertNotEqual(canvases[0], blank)
        self.assertEqual(canvases[2], canvases[3])   # admiring the last stage
        self.assertEqual(len({str(c) for c in canvases}), 3)


class MotionTests(CharacterTestCase):

    def test_juggling_throws_on_the_beat_and_over_the_head(self):
        self.char.force_activity("juggling")
        beat = Juggle.BEAT_MS
        heights = []
        for n in range(1, 3 * beat // 10):  # a full round of every ball
            view = self.char.update(10)
            if n * 10 % beat == 30:          # just after a throw
                self.assertEqual(view["sprite"], "juggle_toss")
            if n * 10 % beat == beat - 30:   # just before the next one
                self.assertEqual(view["sprite"], "juggle_catch")
            self.assertEqual(len(view["juggle"]), 3)
            heights += [(height, dx) for dx, height, _ in view["juggle"]]
        top, dx = max(heights)
        self.assertAlmostEqual(top, Juggle.PEAK, delta=1)
        self.assertLess(abs(dx), 4)          # right over Claudy's head

    def test_balls_are_put_away_after_juggling(self):
        self.char.force_activity("juggling")
        support.run(self.char, 4500)
        self.assertEqual(self.char.view()["juggle"], ())

    def test_walking_eases_in(self):
        self.char.update_walk_bounds(40, 58)
        self.char._start_walking()
        self.char.target_x = self.char.x + 300
        x0 = self.char.x
        self.char.update(50)
        early = self.char.x - x0
        for _ in range(20):
            self.char.update(50)
        x1 = self.char.x
        self.char.update(50)
        cruising = self.char.x - x1
        self.assertLess(early, cruising)


class WalkBoundsTests(CharacterTestCase):

    def test_bounds_are_centered_on_screen(self):
        self.char.update_walk_bounds(10, 58)
        center = support.SCREEN_WIDTH / 2
        self.assertAlmostEqual(center - self.char.walk_min_x,
                               self.char.walk_max_x - center)
        self.assertLess(self.char.walk_min_x, center)

    def test_huge_dock_is_clamped_to_screen(self):
        from claudy.config import WINDOW_WIDTH
        self.char.update_walk_bounds(500, 58)
        self.assertEqual(self.char.walk_min_x, WINDOW_WIDTH)
        self.assertEqual(self.char.walk_max_x,
                         support.SCREEN_WIDTH - WINDOW_WIDTH)

    def test_tiny_dock_collapses_to_center(self):
        self.char.update_walk_bounds(0, 58)
        self.assertEqual(self.char.walk_min_x, self.char.walk_max_x)


class ReactionTests(CharacterTestCase):

    def test_reactions_return_to_idle(self):
        for reaction in activities.REACTIONS:
            with self.subTest(reaction=reaction):
                self.char.react(reaction)
                self.assertTrue(self.char.is_reacting)
                support.run_until_idle(self.char, limit_ms=5000)
                self.assertFalse(self.char.is_reacting)

    def test_greeting_says_something_and_sparkles(self):
        self.char.greet(attached=False)
        events = self.char.take_events()
        self.assertIn("message", _event_types(events))
        self.assertIn(("particle", "sparkle"), events)
        self.assertEqual(self.char.sprite_name(), "happy")

    def test_attached_greeting_brings_hearts(self):
        self.char.greet(attached=True)
        support.run(self.char, 2000)
        self.assertEqual(self.char.sprite_name(), "love")
        events = self.char.take_events() + support.run(self.char, 500)
        self.assertIn(("particle", "heart"), events)

    def test_hover_waves_and_leaving_ends_it(self):
        self.char.hover(True)
        self.assertEqual(self.char.sprite_name(), "wave")
        self.char.hover(False)
        self.assertEqual(self.char.state, "idle")

    def test_drag_and_drop(self):
        self.char.start_drag()
        self.char.drag_to(300)
        self.assertEqual(self.char.sprite_name(), "surprise")
        self.char.drop(120)
        heights = [self.char.update(16)["y_offset"] for _ in range(200)]
        self.assertEqual(self.char.x, 300)
        self.assertGreater(heights[0], 100)
        self.assertEqual(heights[-1], 0)


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
        self.char.receive_gift("book")
        self.char.last_gift_received_time = 0
        self.assertTrue(self.char.has_book)
        self.assertFalse(self.char.can_accept_gift("book"))

    def test_marshmallow_is_eaten_at_the_campfire(self):
        self.char.receive_gift("marshmallow")
        support.run_until_idle(self.char, limit_ms=5000)
        self.assertTrue(self.char.has_marshmallow)
        self.char.trigger_activity("campfire")
        self.assertFalse(self.char.has_marshmallow)
        _, events = support.run_until_idle(self.char)
        messages = [text for kind, text in events if kind == "message"]
        self.assertNotIn("жарит зефирку!", messages)

    def test_toy_shows_only_while_sleeping(self):
        self.char.receive_gift("toy")
        support.run_until_idle(self.char, limit_ms=5000)
        self.assertFalse(self.char.update(16)["show_toy"])
        self.char.trigger_activity("sleeping")
        self.assertTrue(self.char.update(16)["show_toy"])


if __name__ == "__main__":
    unittest.main()
