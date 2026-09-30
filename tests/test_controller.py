"""Tests for the shared application controller and particles."""

import unittest
from unittest import mock

from claudy.config import (
    OVERLAY_HEIGHT, SITTER_OFFSET_X, SPRITE_SIZE, WINDOW_WIDTH,
)
from claudy.content import app_reactions, phrases
from claudy.content.sprites.items import GIFT_ART
from claudy.core import activities, controller
from claudy.core.controller import Controller, MenuItem
from claudy.core.memory import Memory
from claudy.core.particles import ParticleSystem
from claudy.core.settings import Settings
from claudy.core.speech import Speech
from tests import support


class ControllerTestCase(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        support.seeded()
        support.fail_on_logged_errors(self)
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

    def lines_over(self, ms, step=10):
        """Advance `ms`; return (ms since now, text) for each line said."""
        lines, elapsed, seen = [], 0, len(self._said)
        while elapsed < ms:
            self.ctl.tick(step)
            elapsed += step
            lines += [(elapsed, text) for text in self._said[seen:]]
            seen = len(self._said)
        return lines

    @property
    def hidden(self):
        return self._hidden[0]

    def offer_gift(self):
        self.ctl._offer_gift({"type": "fish", "emoji": "🐟"})


class StartupTests(unittest.TestCase):

    def test_claudy_wakes_up_with_a_yawn(self):
        support.reset_singletons()
        support.fail_on_logged_errors(self)
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

    def test_a_painting_is_given_and_taken_with_words_of_its_own(self):
        """A painting wasn't found, so "look what i found!" won't do."""
        emoji = activities.PAINTING_GIFT_EMOJI["friend"]
        with mock.patch("claudy.core.memory.random_story_id",
                        return_value=0) as story:
            self.ctl._offer_gift({"type": "painting", "emoji": emoji})
        story.assert_called_once_with("painting", emoji)
        name = Settings.shared().user_name
        self.assertIn(self.said()[-1],
                      {phrases.format_phrase(p, name=name)
                       for p in phrases.PAINTING_ANNOUNCE_PHRASES})
        self.ctl.on_click()
        self.assertIn(self.said()[-1],
                      {phrases.format_phrase(p)
                       for p in phrases.PAINTING_COLLECT_PHRASES})

    def test_a_painting_taken_is_hung_in_the_gallery(self):
        self.ctl._offer_gift({"type": "painting", "emoji": "\u26F5"})
        story_id = Memory.shared().get_pending_gift()["story_id"]
        self.ctl.on_click()
        self.assertEqual([(e["picture"], e["story_id"])
                          for e in Memory.shared().get_gallery()],
                         [("boat", story_id)])

    def test_a_painting_left_to_fade_is_not_hung(self):
        self.ctl._offer_gift({"type": "painting", "emoji": "\u26F5"})
        self.advance(Settings.shared().gift_duration_seconds() * 1000 + 100)
        self.assertEqual(Memory.shared().get_gallery(), [])

    def test_other_gifts_stay_out_of_the_gallery(self):
        self.offer_gift()
        self.ctl.on_click()
        self.assertEqual(Memory.shared().get_gallery(), [])

    def test_the_test_gift_of_a_painting_is_a_painting(self):
        """So taking it in developer mode tries the gallery."""
        Settings.shared().gift_limit = 0        # all eight in one day
        for emoji in activities.PAINTING_GIFT_EMOJI.values():
            with self.subTest(emoji=emoji), mock.patch(
                    "claudy.core.controller.random.choice",
                    return_value=emoji):
                self.ctl.test_gift()
                self.assertEqual(Memory.shared().get_pending_gift()["type"],
                                 "painting")
                self.ctl.on_click()

    def test_activity_gift_events_reach_the_controller(self):
        support.attach()
        with mock.patch("claudy.core.character.random.random", return_value=0.0):
            self.ctl.character.force_activity("shell_collecting")
            self.advance(30_000)
        self.assertEqual(self.ctl.gift_emoji, "🐚")

    def test_the_find_is_admired_before_the_gift_is_announced(self):
        support.attach()
        with mock.patch("claudy.core.character.random.random", return_value=0.0):
            self.ctl.character.force_activity("shell_collecting")
            lines = self.lines_over(30_000)
        texts = [text for _, text in lines]
        admired = texts.index("какая красивая ракушка!")
        name = Settings.shared().user_name
        self.assertIn(texts[admired + 1],
                      {phrases.format_phrase(p, name=name)
                       for p in phrases.GIFT_ANNOUNCE_PHRASES})
        shown_ms = lines[admired + 1][0] - lines[admired][0]
        self.assertGreaterEqual(shown_ms, Speech.readable_ms(texts[admired]))

    def test_the_line_seeing_a_gift_off_is_not_talked_over(self):
        with support.fixed_weights({"reading": 1.0}):
            self.offer_gift()
            self.advance(Settings.shared().gift_duration_seconds() * 1000 - 100)
            lines = self.lines_over(3100)
        self.assertIsNone(self.ctl.gift_emoji)
        self.assertEqual(len(lines), 1)     # just the goodbye to the gift
        self.assertEqual(self.ctl.character.state, "idle")


class StarNamingTests(ControllerTestCase):

    def test_claudy_names_one_star_and_then_keeps_it(self):
        """The star stays in the sky from then on, so a second one would
        quietly replace the first."""
        support.attach(self.ctl.memory)
        with support.dark_sky(), mock.patch(
                "claudy.core.character.random.random", return_value=0.0):
            for _ in range(3):
                self.ctl.character._special_star_gaze()
                self.advance(100)
        stars = [gift for gift in self.ctl.memory.get_collected_gifts()
                 if gift["type"] == "star"]
        self.assertEqual(len(stars), 1)
        self.assertIsNotNone(self.ctl.memory.get_star())


class DreamTests(ControllerTestCase):
    """Pictures that surface above Claudy while he is deeply asleep."""

    def sleep_until_dream(self):
        """Keep Claudy asleep until a dream starts; return its picture.

        Claudy only counts the time he is actually asleep, and a run of
        "sleeping" ends every few seconds, so the test keeps sending him
        back to bed.
        """
        limit = 3 * controller.DREAM_GAP_MS[1]
        elapsed = 0
        while elapsed < limit:
            if self.ctl.character.state != "sleeping":
                self.ctl.character.force_activity("sleeping")
            self.ctl.tick(50)
            elapsed += 50
            if self.ctl.dream:
                return self.ctl.dream[0]
        return None

    def test_claudy_dreams_of_something_he_actually_did(self):
        self.ctl.character.force_activity("fishing")
        self.advance(200)
        self.assertIn(self.sleep_until_dream(), ("fish", "puffer"))

    def test_nothing_is_dreamt_before_claudy_has_done_anything(self):
        """He dreams of what stayed with him, so a blank day dreams nothing."""
        self.ctl.memory._data["activities"] = ["walking"]
        self.assertIsNone(self.sleep_until_dream())

    def test_an_awake_claudy_never_dreams(self):
        self.ctl.character.force_activity("fishing")
        self.advance(sum(controller.DREAM_GAP_MS))
        self.assertIsNone(self.ctl.dream)

    def dream_alphas(self, until=None):
        """Opacity of the current dream every 50 ms until it is gone (or
        until `until(elapsed_ms)` says to stop)."""
        alphas, elapsed = [], 0
        while self.ctl.dream and not (until and until(elapsed)):
            alphas.append(self.ctl.dream[1])
            self.ctl.tick(50)
            elapsed += 50
        return alphas

    def test_a_dream_fades_in_holds_and_goes(self):
        self.ctl.character.force_activity("reading")
        self.advance(200)
        self.sleep_until_dream()
        with support.fixed_period("deep_sleep"):
            alphas = self.dream_alphas()
        self.assertLess(alphas[0], 0.5, "should fade in, not appear")
        self.assertLess(alphas[-1], 0.5, "should fade out, not vanish")
        held = [a for a in alphas if a == 1.0]
        self.assertAlmostEqual(len(held) * 50, controller.DREAM_HOLD_MS,
                               delta=100)
        rising = alphas[:alphas.index(1.0)]
        self.assertEqual(rising, sorted(rising))
        self.assertEqual(alphas[alphas.index(1.0):],
                         sorted(alphas[alphas.index(1.0):], reverse=True))

    def test_waking_up_lets_the_dream_go(self):
        self.ctl.character.force_activity("reading")
        self.advance(200)
        self.sleep_until_dream()
        self.assertIsNotNone(self.ctl.dream)
        self.ctl.character.force_activity("playing")
        self.advance(controller.DREAM_LET_GO_MS + 100)
        self.assertIsNone(self.ctl.dream)

    def test_waking_mid_fade_in_never_flashes_the_dream(self):
        self.ctl.character.force_activity("reading")
        self.advance(200)
        self.sleep_until_dream()
        with support.fixed_period("deep_sleep"):
            self.dream_alphas(until=lambda ms: ms >= 200)
            before = self.ctl.dream[1]
            self.assertLess(before, 0.5)
            self.ctl.on_click()
            after = self.dream_alphas()
        self.assertTrue(after)
        self.assertLessEqual(max(after), before + 0.1)
        self.assertEqual(after, sorted(after, reverse=True))

    def test_a_dream_gives_way_to_speech(self):
        self.ctl.character.force_activity("reading")
        self.advance(200)
        self.sleep_until_dream()
        self.ctl._say("мм?")
        self.advance(controller.DREAM_LET_GO_MS + 100)
        self.assertIsNone(self.ctl.dream)

    def test_no_zzz_cross_a_dream(self):
        self.ctl.character.force_activity("reading")
        self.advance(200)
        self.sleep_until_dream()
        before = set(self.ctl.particles.get_active())
        self.ctl._handle_event("particle", "zzz")
        self.ctl._handle_event("particle", "heart")
        new = set(self.ctl.particles.get_active()) - before
        self.assertEqual({p.image for p in new}, {"heart"})


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

    def test_idle_chatter_never_talks_over_a_line(self):
        line = "это длинная фраза, и её надо успеть дочитать"
        with support.fixed_weights({"idle": 1.0}):
            self.ctl._say(line)
            self.advance(controller.CHATTER_GAP_MS + 100)
            self.ctl._say("болтовня", chatter=True)
            self.assertEqual(self.said(), [line])
            self.advance(Speech.typing_ms(line)
                         + controller.reading_time(line) * 1000)
            self.ctl._say("болтовня", chatter=True)
        self.assertEqual(self.said()[-1], "болтовня")

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
        self.ctl.tick(16)
        self.assertTrue(self.said())

    def test_the_app_phrase_opens_the_activity_and_can_be_read(self):
        for app_id in ("gnome-terminal", "spotify"):
            with self.subTest(app=app_id):
                self.ctl.character.force_activity("playing")
                self.advance(6000)              # free again
                app = app_reactions.LINUX_APPS[app_id]
                self.ctl.on_app_launched(app_id, app, app_id)
                self.ctl.tick(10)
                phrase = self.ctl.speech.text
                self.assertIn(phrase, app.phrases)
                self.advance(Speech.readable_ms(phrase) - 20, step=10)
                self.assertEqual(self.ctl.speech.text, phrase)

    def test_opening_a_terminal_next_to_a_gift_starts_nothing(self):
        self.offer_gift()
        app = app_reactions.LINUX_APPS["gnome-terminal"]
        self.ctl.on_app_launched("gnome-terminal", app, "gnome-terminal")
        self.advance(1000)
        self.assertEqual(self.ctl.character.state, "idle")
        self.assertEqual(self.ctl.gift_emoji, "🐟")

    def test_unknown_app_is_only_counted(self):
        self.ctl.on_app_launched("com.example.unknown")
        self.assertEqual(self.said(), [])
        self.assertEqual(
            Memory.shared().record_app_launch("com.example.unknown"), 2)

    def test_a_high_drop_still_shows_its_surprise(self):
        """Dropped from high on a Mac, the "!" used to be born above the top
        of the ground overlay and never seen."""
        self.ctl.on_drag_start()
        self.ctl.on_drag_move(self.ctl.character.x, height=400)
        self.ctl.tick(50)
        self.ctl.on_drop(400)
        seen = []
        for _ in range(100):
            self.ctl.tick(50)
            seen += [OVERLAY_HEIGHT - p.y for p in self.ctl.particles.get_active()
                     if p.image == "exclaim"]
        self.assertTrue(seen, "no surprise at all")
        self.assertGreaterEqual(min(seen), 0, "drawn above the overlay")

    def test_a_smaller_screen_keeps_claudy_in_sight(self):
        self.ctl.character.x = 2000
        self.ctl.set_screen_width(1280)
        ch = self.ctl.character
        self.assertEqual(ch.screen_width, 1280)
        self.assertTrue(ch.walk_min_x <= ch.x <= ch.walk_max_x)
        self.assertLess(ch.walk_max_x, 1280)

    def test_a_walk_under_way_stays_on_a_smaller_screen(self):
        ch = self.ctl.character
        ch.x = 1300
        ch._start_walking(1400)
        self.ctl.set_screen_width(1000)
        for _ in range(400):             # 20 s
            self.ctl.tick(50)
            self.assertLessEqual(ch.x, 1000 - SPRITE_SIZE / 2)

    def test_sleep_and_wake(self):
        self.ctl.on_system_sleep()
        self.assertEqual(self.ctl.character.state, "sleeping")
        self.ctl.on_system_wake()
        self.assertEqual(self.ctl.character.state, "waking")


class InputTests(ControllerTestCase):

    def test_a_dragged_claudy_is_as_high_as_he_is_held(self):
        """His shadow on the Dock goes by it, and so does the fall."""
        self.ctl.on_drag_start()
        self.ctl.on_drag_move(500, height=150)
        self.ctl.tick(16)
        self.assertEqual(self.ctl.view["y_offset"], 150)
        self.ctl.on_drop(150)
        self.ctl.tick(16)
        self.assertGreater(self.ctl.view["y_offset"], 140)

    def test_a_drag_without_a_height_stays_on_the_ground(self):
        self.ctl.on_drag_start()
        self.ctl.on_drag_move(500)
        self.ctl.tick(16)
        self.assertEqual(self.ctl.view["y_offset"], 0)


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

    def test_the_dev_test_gift_can_be_any_gift_picture(self):
        self.assertEqual(set(controller.TEST_GIFT_EMOJIS), set(GIFT_ART))

    def test_giving_a_toy_marks_it_owned(self):
        gifts = self._find(self.ctl.menu(), "Подарить подарок").submenu
        self._find(gifts, "Игрушку 🧸").action()
        self.assertTrue(self.ctl.character.has_toy)
        gifts = self._find(self.ctl.menu(), "Подарить подарок").submenu
        toy = self._find(gifts, "Игрушку 🧸 ✓")
        self.assertFalse(toy.enabled)
        self.assertIsInstance(gifts[-1], MenuItem)
        self.assertFalse(gifts[-1].enabled)  # "wait a bit" while cooling down


class ParticleEventTests(ControllerTestCase):
    """Particles Claudy asks for end up around him."""

    def test_the_sitters_particles_rise_across_the_easel(self):
        for facing_right, side in ((True, 1), (False, -1)):
            with self.subTest(facing_right=facing_right):
                self.ctl.particles = ParticleSystem()
                self.ctl.view = dict(self.ctl.view, facing_right=facing_right)
                self.ctl._handle_event("sitter_particle", "heart")
                heart, = self.ctl.particles.get_active()
                self.assertLess(abs(heart.x - (WINDOW_WIDTH / 2
                                               + side * SITTER_OFFSET_X)), 16)

    def test_particles_spawn_around_claudy(self):
        self.ctl.on_click()
        self.ctl.tick(16)
        sparkles = self.ctl.particles.get_active()
        self.assertTrue(sparkles)
        for p in sparkles:
            self.assertLess(abs(p.x - WINDOW_WIDTH / 2), 16)
            self.assertGreaterEqual(p.y, controller.PARTICLE_HEAD_Y)


class ParticleTests(unittest.TestCase):

    def test_particles_fade_in_rise_and_die(self):
        system = ParticleSystem()
        system.add("heart", 100, 80)
        p = system.get_active()[0]
        y0 = p.y
        system.update(10)
        self.assertLess(p.opacity, 0.5)       # fading in
        system.update(500)
        self.assertEqual(p.opacity, 1.0)
        self.assertGreater(p.y, y0)           # rising
        system.update(600)
        self.assertLess(p.opacity, 1.0)       # fading out
        system.update(1000)
        self.assertEqual(system.get_active(), [])

    def test_sweat_drips_down(self):
        system = ParticleSystem()
        system.add("sweat", 100, 80)
        p = system.get_active()[0]
        y0 = p.y
        system.update(300)
        self.assertLess(p.y, y0)

    def test_dust_starts_at_the_feet(self):
        system = ParticleSystem()
        system.add("dust", 100, head_y=80, feet_y=10)
        self.assertLess(system.get_active()[0].y, 30)

    def test_spawn_side_follows_facing(self):
        system = ParticleSystem()
        support.seeded(1)
        system.add("flame", 100, 80, 10, facing_right=True)
        support.seeded(1)
        system.add("flame", 100, 80, 10, facing_right=False)
        right, left = system.get_active()
        self.assertGreater(right.x, 100)
        self.assertLess(left.x, 100)

    def test_butterflies_flap(self):
        system = ParticleSystem()
        system.add("butterfly", 100, 80)
        p = system.get_active()[0]
        frames = set()
        for _ in range(10):
            system.update(50)
            frames.add(p.frame)
        self.assertEqual(frames, {"butterfly_open", "butterfly_closed"})

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

    def test_particle_count_is_capped(self):
        system = ParticleSystem()
        for _ in range(500):
            system.add("sparkle", 100, 80)
        self.assertLessEqual(len(system.get_active()), 80)


if __name__ == "__main__":
    unittest.main()
