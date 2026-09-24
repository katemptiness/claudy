"""Static checks on sprites, activity definitions and phrases."""

import unittest

import character
import phrases
import schedule
from config import GRID, PALETTE
from sprites.activities import ALL as ACTIVITY_SPRITES
from sprites.base import ALL as BASE_SPRITES

ALL_SPRITES = {**BASE_SPRITES, **ACTIVITY_SPRITES}

# Sprites the state machine picks directly (not via activity phases).
REACTION_SPRITES = ["idle", "blink", "walk_a", "walk_b", "happy", "love",
                    "wave", "surprise"]


def _all_phases():
    for name, phases in character.ACTIVITIES.items():
        for phase in phases:
            yield name, phase
    for key, factory in character.FRIEND_ACTIVITY_POOL.items():
        for phase in factory():
            yield f"friend:{key}", phase


class SpriteTests(unittest.TestCase):

    def test_grids_are_square_and_use_palette(self):
        for name, grid in ALL_SPRITES.items():
            with self.subTest(sprite=name):
                self.assertEqual(len(grid), GRID)
                for row in grid:
                    self.assertEqual(len(row), GRID)
                    for value in row:
                        self.assertIn(value, PALETTE)

    def test_every_referenced_frame_exists(self):
        for activity, phase in _all_phases():
            for frame in phase.frames:
                with self.subTest(activity=activity, frame=frame):
                    self.assertIn(frame, ALL_SPRITES)

    def test_reaction_sprites_exist(self):
        for name in REACTION_SPRITES:
            self.assertIn(name, ALL_SPRITES)


class ScheduleTests(unittest.TestCase):

    def test_every_hour_maps_to_a_weighted_period(self):
        for mode in ("owl", "lark"):
            for hour in range(24):
                with self.subTest(mode=mode, hour=hour):
                    period = schedule.get_period(hour=hour, mode=mode)
                    self.assertIn(period, schedule.ACTIVITY_WEIGHTS)

    def test_weights_reference_known_activities(self):
        known = set(character.ACTIVITIES) | {"idle", "walking"}
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

    def test_character_phrase_pools_are_translated(self):
        pools = [
            character.IDLE_PHRASES, character.SHELL_SEARCH_PHRASES,
            character.FRIEND_PHRASES, character.FRIEND_TOGETHER,
            character.FRIEND_AFTER, character.FRIEND_WALK_PHRASES,
            character.FRIEND_WALK_END_PHRASES, character.FRIEND_PLAY_PHRASES,
            character.FRIEND_SIT_PHRASES, character.FRIEND_CHAT_PHRASES,
            character.FRIEND_CHAT_REPLY_PHRASES,
            [c["name"] for c in character.CATCHES],
            [m["text"] for m in character.MAGIC_RESULTS],
        ]
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


if __name__ == "__main__":
    unittest.main()
