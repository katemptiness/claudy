"""Static checks on sprites, activity definitions and phrases."""

import unittest

from claudy.config import GRID, PALETTE
from claudy.content import app_reactions, phrases, ui_text
from claudy.content.sprites import SPRITES
from claudy.core import activities, schedule
from claudy.core.character import Character

# Sprites the state machine picks directly (not via activity phases).
REACTION_SPRITES = ["idle", "blink", "walk_a", "walk_b", "happy", "love",
                    "wave", "surprise"]


def _all_phases():
    for name, phases in activities.ACTIVITIES.items():
        for phase in phases:
            yield name, phase
    for key, phases in activities.FRIEND_ACTIVITY_POOL.items():
        for phase in phases:
            yield f"friend:{key}", phase
    for phase in activities.FRIEND_GOODBYE:
        yield "friend:goodbye", phase
    for phase in activities.WAKING:
        yield "waking", phase


class SpriteTests(unittest.TestCase):

    def test_grids_have_valid_shape_and_colors(self):
        for name, grid in SPRITES.items():
            with self.subTest(sprite=name):
                self.assertEqual(len(grid), GRID)
                width = len(grid[0])
                # Wider sprites grow evenly on both sides of Claudy and
                # must fit the 200 px crab window
                self.assertGreaterEqual(width, GRID)
                self.assertEqual(width % 2, 0)
                self.assertLessEqual(width, 40)
                for row in grid:
                    self.assertEqual(len(row), width)
                    for value in row:
                        self.assertIn(value, PALETTE)

    def test_claudy_is_all_in_one_piece(self):
        # Every body pixel touches the rest of the body (diagonals count),
        # so no leg or claw floats loose
        for name, grid in SPRITES.items():
            body = {(r, c) for r, row in enumerate(grid)
                    for c, v in enumerate(row) if v == 1}
            start = body.pop()
            todo, seen = [start], {start}
            while todo:
                r, c = todo.pop()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        cell = (r + dr, c + dc)
                        if cell in body:
                            body.discard(cell)
                            seen.add(cell)
                            todo.append(cell)
            with self.subTest(sprite=name):
                self.assertEqual(body, set())

    def test_every_referenced_frame_exists(self):
        for activity, phase in _all_phases():
            for frame in phase.frames:
                with self.subTest(activity=activity, frame=frame):
                    self.assertIn(frame, SPRITES)

    def test_reaction_sprites_exist(self):
        for name in REACTION_SPRITES:
            self.assertIn(name, SPRITES)
        for name, reaction in activities.REACTIONS.items():
            for _, sprite in reaction.sprites:
                with self.subTest(reaction=name):
                    self.assertIn(sprite, SPRITES)
        for frames in activities.FRIEND_ANIMATIONS.values():
            for sprite in frames:
                self.assertIn(sprite, SPRITES)


class ActivityDefinitionTests(unittest.TestCase):

    def test_every_special_has_a_handler(self):
        for activity, phase in _all_phases():
            if phase.special:
                with self.subTest(activity=activity, special=phase.special):
                    self.assertTrue(
                        hasattr(Character, "_special_" + phase.special))

    def test_phases_are_immutable(self):
        phase = activities.ACTIVITIES["reading"][0]
        with self.assertRaises(Exception):
            phase.message = "changed"
        self.assertIsInstance(phase.frames, tuple)


class ParticleKindTests(unittest.TestCase):

    def test_every_particle_used_is_defined(self):
        from claudy.core.particles import KINDS
        used = {phase.particle for _, phase in _all_phases() if phase.particle}
        used |= {c["particles"] for c in activities.CATCHES}
        used |= {m["particles"] for m in activities.MAGIC_RESULTS}
        used |= {"sparkle", "heart", "note", "poof", "exclaim", "star", "dust"}
        for kind in used:
            with self.subTest(kind=kind):
                self.assertIn(kind, KINDS)

    def test_particle_images_exist(self):
        from claudy.content.sprites.particles import PARTICLE_ART
        from claudy.core.particles import KINDS
        for name, kind in KINDS.items():
            for image in kind.images:
                with self.subTest(kind=name, image=image):
                    self.assertIn(image, PARTICLE_ART)


class ScheduleTests(unittest.TestCase):

    def test_every_hour_maps_to_a_weighted_period(self):
        for mode in ("owl", "lark"):
            for hour in range(24):
                with self.subTest(mode=mode, hour=hour):
                    period = schedule.get_period(hour=hour, mode=mode)
                    self.assertIn(period, schedule.ACTIVITY_WEIGHTS)

    def test_weights_reference_known_activities(self):
        known = set(activities.ACTIVITIES) | {"idle", "walking"}
        for period, weights in schedule.ACTIVITY_WEIGHTS.items():
            for name, weight in weights.items():
                with self.subTest(period=period, activity=name):
                    self.assertIn(name, known)
                    self.assertGreater(weight, 0)

    def test_owl_sleeps_in_the_morning_and_lark_at_night(self):
        self.assertEqual(schedule.get_period(hour=7, mode="owl"), "deep_sleep")
        self.assertEqual(schedule.get_period(hour=23, mode="lark"), "deep_sleep")
        self.assertEqual(schedule.get_period(hour=15, mode="owl"), "day")


class PhraseTests(unittest.TestCase):

    def _assert_translated(self, text):
        self.assertIn(text, phrases._EN, f"missing English for {text!r}")

    def test_activity_messages_are_translated(self):
        for activity, phase in _all_phases():
            if phase.message:
                with self.subTest(activity=activity):
                    self._assert_translated(phase.message)

    def test_phrase_pools_are_translated(self):
        pools = [
            phrases.IDLE_PHRASES, phrases.GREETING_PHRASES,
            phrases.HOVER_PHRASES, phrases.SHELL_SEARCH_PHRASES,
            phrases.FRIEND_PHRASES, phrases.FRIEND_AFTER,
            phrases.FRIEND_WALK_PHRASES, phrases.FRIEND_WALK_END_PHRASES,
            phrases.FRIEND_PLAY_PHRASES, phrases.FRIEND_SIT_PHRASES,
            phrases.FRIEND_CHAT_PHRASES, phrases.FRIEND_CHAT_REPLY_PHRASES,
            phrases.PERSONAL_CLICK_PHRASES, phrases.SLEEP_PHRASES,
            phrases.WAKE_PHRASES, phrases.GIFT_ANNOUNCE_PHRASES,
            phrases.GIFT_EXPIRED_PHRASES, phrases.GIFT_COLLECT_PHRASES,
            phrases.BOOK_IDLE_PHRASES,
            [c["name"] for c in activities.CATCHES],
            [m["text"] for m in activities.MAGIC_RESULTS],
        ]
        pools += list(phrases.GIFT_RECEIVE_PHRASES.values())
        pools += list(app_reactions.CATEGORY_PHRASES.values())
        for table in (app_reactions.MACOS_APPS, app_reactions.LINUX_APPS):
            pools += [app.extra_phrases for app in table.values()]
        for pool in pools:
            for text in pool:
                with self.subTest(text=text):
                    self._assert_translated(text)

    def test_format_phrase_removes_missing_name(self):
        phrases.set_language("ru")
        self.assertEqual(phrases.format_phrase("привет, {name}!"), "привет!")
        self.assertEqual(
            phrases.format_phrase("привет, {name}!", name="Катя"),
            "привет, Катя!")

    def test_english_lookup_falls_back_to_original(self):
        phrases.set_language("en")
        try:
            self.assertEqual(phrases.t("читает..."), "reading...")
            self.assertEqual(phrases.t("нет такой фразы"), "нет такой фразы")
        finally:
            phrases.set_language("ru")


class AppReactionTests(unittest.TestCase):

    def test_categories_are_known(self):
        for table in (app_reactions.MACOS_APPS, app_reactions.LINUX_APPS):
            for key, app in table.items():
                with self.subTest(app=key):
                    self.assertIn(app.category, app_reactions.CATEGORY_PHRASES)
                    if app.activity:
                        self.assertIn(app.activity, activities.ACTIVITIES)

    def test_linux_process_matching(self):
        match = app_reactions.match_linux_process
        self.assertEqual(match("gnome-terminal-"), "gnome-terminal")
        self.assertEqual(match("Firefox"), "firefox")
        self.assertEqual(match("codium"), "codium")
        self.assertIsNone(match("systemd"))
        terminal = app_reactions.LINUX_APPS[match("gnome-terminal-")]
        self.assertEqual(terminal.activity, "working")


class UiTextTests(unittest.TestCase):

    def test_russian_gift_plurals(self):
        phrases.set_language("ru")
        self.assertEqual(ui_text.gifts_header(1), "1 подарок собран")
        self.assertEqual(ui_text.gifts_header(3), "3 подарка собрано")
        self.assertEqual(ui_text.gifts_header(12), "12 подарков собрано")
        self.assertEqual(ui_text.gifts_header(21), "21 подарок собран")

    def test_dates(self):
        phrases.set_language("en")
        try:
            self.assertEqual(ui_text.format_date("2026-09-24"), "Sep 24, 2026")
        finally:
            phrases.set_language("ru")
        self.assertEqual(ui_text.format_date("2026-09-04"), "4 сен 2026")
        self.assertEqual(ui_text.format_date("junk"), "junk")


if __name__ == "__main__":
    unittest.main()
