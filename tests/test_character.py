"""Behavioral tests for the Character state machine."""

import contextlib
import unittest
from unittest import mock

from claudy.content import phrases
from claudy.content.sprites import SPRITES
from claudy.core import activities
from claudy.core.animations import Juggle
from claudy.core.character import Character
from claudy.core.settings import Settings
from claudy.core.speech import Speech
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

    def test_nothing_starts_while_claudy_waits_by_a_gift(self):
        """Some props (the laptop) would be drawn over the gift."""
        self.char.wait_for_gift(True)
        self.assertFalse(self.char.trigger_activity("working"))
        self.assertEqual(self.char.state, "idle")

    def test_an_opening_line_replaces_the_first_and_stays_until_read(self):
        line = "о, опять этот редактор? ну давай поработаем!"
        self.assertTrue(self.char.trigger_activity("working", opening=line))
        said = [text for kind, text in self.char.take_events()
                if kind == "message"]
        self.assertEqual(said, [line])
        events = support.run(self.char, Speech.readable_ms(line) - 50)
        self.assertNotIn("message", _event_types(events))
        self.assertEqual(self.char.sprite_name(), "work_closed")

    def test_opening_lines_can_be_read_before_the_next_one(self):
        """The still poses an activity opens with (getting the book or the
        wand out) last until their line is typed out and read."""
        self.addCleanup(setattr, Settings.shared(), "language", "ru")
        for name, phases in activities.ACTIVITIES.items():
            for phase in phases:
                if len(phase.frames) > 1 or phase.special or not phase.message:
                    break
                for language in ("ru", "en"):
                    Settings.shared().language = language
                    line = phrases.t(phase.message)
                    with self.subTest(activity=name, line=line):
                        self.assertGreaterEqual(phase.duration_ms,
                                                Speech.readable_ms(line))


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

    def test_claudy_lingers_after_a_gift_is_gone(self):
        """Or whatever he started next would talk over the line that saw
        the gift off."""
        with support.fixed_weights({"reading": 1.0}):
            self.char.wait_for_gift(True)
            support.run(self.char, 60_000)
            self.char.wait_for_gift(False)
            support.run(self.char, 5000)
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

    def test_balls_in_the_air_come_down_before_they_are_put_away(self):
        self.char.force_activity("juggling")
        shown, falling_after_the_last_throw = {}, False
        while self.char.state == "juggling":
            view = self.char.update(5)
            balls = {index: height for _, height, index in view["juggle"]}
            if self.char.phase_index > 0 and balls:
                falling_after_the_last_throw = True
            for index, height in shown.items():
                if index not in balls:
                    self.assertLess(height, 2, "a ball vanished in mid-air")
            shown = balls
        self.assertTrue(falling_after_the_last_throw)
        self.assertEqual(self.char.view()["juggle"], ())

    def test_playing_ends_with_a_landing(self):
        self.char.force_activity("playing")
        heights, events = [0.0], []
        while self.char.phase_index == 0:
            heights.append(self.char.update(16)["y_offset"])
            events += self.char.take_events()
        drops = [a - b for a, b in zip(heights, heights[1:])]
        self.assertLess(max(drops), 2)       # no snapping down to the ground
        self.assertEqual(events[-1], ("particle", "dust"))

    def test_hopping_or_wandering_off_the_dock_never_jumps_back(self):
        self.char.update_walk_bounds(10, 58)
        for name in ("playing", "shell_collecting"):
            with self.subTest(activity=name):
                self.char.x = self.char.walk_min_x - 200
                self.char.force_activity(name)
                xs = [self.char.x]
                while self.char.state == name:
                    xs.append(self.char.update(50)["x"])
                self.assertLess(max(abs(b - a) for a, b in zip(xs, xs[1:])), 5)

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

    def test_claudy_walks_back_onto_the_dock(self):
        self.char.update_walk_bounds(10, 58)
        self.char.x = self.char.walk_min_x - 200
        xs = [self.char.x]
        with support.fixed_weights({"idle": 1.0}):
            self.char.update(50)
            self.assertEqual(self.char.state, "walking")
            for _ in range(200):
                xs.append(self.char.update(50)["x"])
        self.assertEqual(self.char.state, "idle")
        self.assertGreaterEqual(self.char.x, self.char.walk_min_x - 2)
        self.assertLess(max(abs(b - a) for a, b in zip(xs, xs[1:])), 5)

    def test_claudy_waits_by_a_gift_even_off_the_dock(self):
        self.char.update_walk_bounds(10, 58)
        self.char.x = self.char.walk_min_x - 200
        self.char.wait_for_gift(True)
        support.run(self.char, 1000)
        self.assertEqual(self.char.state, "idle")


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

    def test_hover_leaves_a_busy_claudy_to_it(self):
        """The pointer crosses Claudy on its way to the Dock."""
        for name in ("reading", "sleeping"):
            with self.subTest(activity=name):
                self.char.force_activity(name)
                support.run(self.char, 2000)
                self.char.hover(True)
                self.assertNotEqual(self.char.sprite_name(), "wave")
                self.char.hover(False)
                support.run(self.char, 100)
                self.assertEqual(self.char.state, name)

    def test_hover_does_not_send_a_friend_home(self):
        self.char.trigger_activity("summoning")
        support.run(self.char, 4000)
        self.assertTrue(self.char.friend_visible)
        self.char.hover(True)
        self.char.hover(False)
        self.assertTrue(self.char.friend_visible)

    def test_drag_and_drop(self):
        self.char.start_drag()
        self.char.drag_to(300)
        self.assertEqual(self.char.sprite_name(), "surprise")
        self.char.drop(120)
        heights = [self.char.update(16)["y_offset"] for _ in range(200)]
        self.assertEqual(self.char.x, 300)
        self.assertGreater(heights[0], 100)
        self.assertEqual(heights[-1], 0)

    def test_held_up_high_and_let_go_from_there(self):
        """The height Claudy is held at is what his shadow goes by."""
        self.char.start_drag()
        self.char.drag_to(300, 120)
        self.assertEqual(self.char.update(16)["y_offset"], 120)
        self.char.drag_to(310)
        self.assertEqual(self.char.update(16)["y_offset"], 0)
        self.char.drag_to(320, 120)
        self.char.update(16)
        self.char.drop(120)
        self.assertGreater(self.char.update(16)["y_offset"], 115)


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


class GiftOfferTests(CharacterTestCase):
    """Gifts Claudy finds while fishing, casting spells or beachcombing."""

    # The phase special that finds each activity's gift
    FINDS = {"fishing": "fish_reveal", "magic": "cast_magic",
             "shell_collecting": "shell_gift_chance"}

    def setUp(self):
        super().setUp()
        support.attach()
        # Win every chance and take the first of every choice: a fish, a
        # bouquet, a shell
        luck = contextlib.ExitStack()
        luck.enter_context(mock.patch(
            "claudy.core.character.random.random", return_value=0.0))
        luck.enter_context(mock.patch(
            "claudy.core.character.random.choice", side_effect=lambda s: s[0]))
        self.addCleanup(luck.close)

    def _run_until_found(self, name):
        """Start `name` and run it into the phase that finds the gift."""
        self.char.force_activity(name)
        events = []
        while self.char.phases[self.char.phase_index].special != self.FINDS[name]:
            self.char.update(50)
            events += self.char.take_events()
        return events

    def test_the_find_has_its_moment_before_it_is_offered(self):
        """The gift comes once the activity is over, so the catch or the
        spell keeps its pose and its line until then."""
        for name in self.FINDS:
            with self.subTest(activity=name):
                events = self._run_until_found(name)
                pose_ms, elapsed = self.char.phase_duration, 0
                while "gift" not in _event_types(events) and elapsed < 60_000:
                    events = support.run(self.char, 50)
                    elapsed += 50
                self.assertIn("gift", _event_types(events))
                self.assertEqual(self.char.state, "idle")
                self.assertGreaterEqual(elapsed, pose_ms)

    def test_an_interrupted_find_is_not_offered(self):
        """Not then, and not at the end of whatever comes next either."""
        self._run_until_found("shell_collecting")
        self.char.greet(attached=True)
        _, events = support.run_until_idle(self.char)
        self.char.trigger_activity("playing")
        events += support.run_until_idle(self.char)[1]
        self.assertNotIn("gift", _event_types(events))


if __name__ == "__main__":
    unittest.main()
