"""Tests for how phrases and gift stories are filled in."""

import re
import unittest
from unittest import mock

from claudy.content import gift_stories, phrases

PLACEHOLDER = re.compile(r"\{[^{}]*\}")


def in_both_languages(test):
    """Run `test(lang)` in Russian and English, then go back to Russian."""
    try:
        for lang in ("ru", "en"):
            phrases.set_language(lang)
            test(lang)
    finally:
        phrases.set_language("ru")


def phrase_pools():
    """Every pool of phrases Claudy picks from, by name."""
    pools = {name: value for name, value in vars(phrases).items()
             if name.isupper() and isinstance(value, list)
             and all(isinstance(p, str) for p in value)}
    for gift, pool in phrases.GIFT_RECEIVE_PHRASES.items():
        pools[f"GIFT_RECEIVE_PHRASES[{gift}]"] = pool
    return pools


def pools_picked_without_a_name():
    """The pools pick() may get an empty name for. A pool with a _NAMELESS
    twin is only picked from when there is a name (pick_personal)."""
    pools = phrase_pools()
    return {name: pool for name, pool in pools.items()
            if name + "_NAMELESS" not in pools}


class NumberTests(unittest.TestCase):

    def test_russian_plurals(self):
        forms = ("день", "дня", "дней")
        expected = {1: "день", 2: "дня", 4: "дня", 5: "дней", 11: "дней",
                    12: "дней", 14: "дней", 21: "день", 22: "дня",
                    25: "дней", 101: "день", 111: "дней", 112: "дней"}
        for n, form in expected.items():
            with self.subTest(n=n):
                self.assertEqual(phrases.plural_ru(n, *forms), form)

    def test_english_ordinals(self):
        expected = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 11: "11th",
                    12: "12th", 13: "13th", 21: "21st", 22: "22nd",
                    23: "23rd", 101: "101st", 111: "111th", 112: "112th"}
        for n, ordinal in expected.items():
            with self.subTest(n=n):
                self.assertEqual(phrases.ordinal_en(n), ordinal)

    def test_days_together_agree_with_the_number(self):
        """Claudy counts from 2, so the forms that need care are the
        common ones."""
        together = phrases.DAYS_PHRASES[0]
        expected = {
            "ru": {2: "мы уже 2 дня вместе", 5: "мы уже 5 дней вместе",
                   21: "мы уже 21 день вместе"},
            "en": {1: "we've been together for 1 day",
                   2: "we've been together for 2 days"},
        }

        def check(lang):
            for n, text in expected[lang].items():
                self.assertEqual(phrases.format_phrase(together, n=n), text)
        in_both_languages(check)

    def test_app_count_ordinals(self):
        """Claudy mentions the count from the third launch on."""
        third = phrases.APP_COUNT_PHRASES[0]

        def check(lang):
            said = {n: phrases.format_phrase(third, n=n, app="Spotify")
                    for n in (3, 11, 22)}
            if lang == "en":
                self.assertEqual(said[3], "Spotify for the 3rd time today :)")
                self.assertIn("11th", said[11])
                self.assertIn("22nd", said[22])
            else:
                self.assertEqual(said[3], "Spotify уже 3-й раз за сегодня :)")
        in_both_languages(check)


class NamelessTests(unittest.TestCase):
    """Settings.user_name is empty until the user sets it."""

    def test_translations_ask_for_a_name_when_the_original_does(self):
        # pick() looks at the Russian original to tell which phrases
        # need a name, so the English one must agree
        for ru, en in phrases._EN.items():
            with self.subTest(phrase=ru):
                self.assertEqual("{name}" in ru, "{name}" in en)

    def test_every_pool_can_do_without_a_name(self):
        for pool_name, pool in pools_picked_without_a_name().items():
            with self.subTest(pool=pool_name):
                self.assertTrue([p for p in pool if "{name}" not in p])

    def test_no_name_means_no_phrase_that_needs_one(self):
        offered = []

        def first(pool):
            offered.append(list(pool))
            return pool[0]

        with mock.patch("claudy.content.phrases.random.choice", first):
            for pool in pools_picked_without_a_name().values():
                phrases.pick(pool, name="")
        for pool in offered:
            self.assertFalse([p for p in pool if "{name}" in p], pool)

    def test_a_named_user_still_hears_their_name(self):
        with mock.patch("claudy.content.phrases.random.choice",
                        lambda pool: pool[-1]):
            said = phrases.pick(phrases.WAKE_PHRASES, name="Катя")
        self.assertEqual(said, "а? что? ...о, Катя!")

    def test_every_phrase_fills_in_completely(self):
        def check(lang):
            for pool in phrase_pools().values():
                for phrase in pool:
                    names = ("Катя",) if "{name}" in phrase else ("", "Катя")
                    for name in names:
                        text = phrases.format_phrase(
                            phrase, name=name, n=3, app="Firefox")
                        with self.subTest(lang=lang, phrase=phrase, name=name):
                            self.assertIsNone(PLACEHOLDER.search(text))
        in_both_languages(check)


class GiftStoryTests(unittest.TestCase):

    def stories(self):
        for gift_type in ("fish", "magic", "star", "shell"):
            count = len(gift_stories._get_stories(gift_type))
            for story_id in range(count):
                yield gift_type, story_id

    def test_both_languages_agree_on_naming_the_user(self):
        for stories in gift_stories._STORIES.values():
            for story in stories:
                self.assertEqual("{name}" in story["ru"],
                                 "{name}" in story["en"], story["en"])

    def test_without_a_name_a_story_that_needs_one_is_swapped(self):
        """Cutting the name out left "because i knew would be happy"; in
        Russian it would need rewording, so another story is told."""
        def check(lang):
            for gift_type, story_id in self.stories():
                nameless = {s[lang].strip()
                            for s in gift_stories._get_stories(gift_type)
                            if "{name}" not in s["ru"]}
                text = gift_stories.get_story(gift_type, story_id)
                with self.subTest(gift=gift_type, story=story_id):
                    # a whole story as written, not one with a word cut out
                    self.assertIn(text, nameless)
                    # the same gift keeps its story each time it is shown
                    self.assertEqual(
                        gift_stories.get_story(gift_type, story_id), text)
        in_both_languages(check)

    def test_stories_that_need_no_name_stay_as_they_are(self):
        for gift_type, story_id in self.stories():
            story = gift_stories._get_stories(gift_type)[story_id]
            if "{name}" not in story["ru"]:
                self.assertEqual(
                    gift_stories.get_story(gift_type, story_id),
                    gift_stories.get_story(gift_type, story_id, name="Катя"))

    def test_with_a_name_the_story_uses_it(self):
        named = [(t, i) for t, i in self.stories()
                 if "{name}" in gift_stories._get_stories(t)[i]["ru"]]
        self.assertTrue(named)
        for gift_type, story_id in named:
            self.assertIn("Катя", gift_stories.get_story(
                gift_type, story_id, name="Катя"))

    def test_story_ids_out_of_range_wrap_around(self):
        self.assertTrue(gift_stories.get_story("fish", 1000))
        self.assertTrue(gift_stories.get_story("fish", -1))


if __name__ == "__main__":
    unittest.main()
