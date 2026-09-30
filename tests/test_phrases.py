"""Tests for how phrases and gift stories are filled in."""

import re
import unittest
from unittest import mock

from claudy.content import gift_stories, phrases
from claudy.core import activities

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

    GIFTS = [(gift_type, None) for gift_type in ("fish", "magic", "star",
                                                "shell")]
    GIFTS += [("painting", emoji)
              for emoji in activities.PAINTING_GIFT_EMOJI.values()]

    def stories(self):
        for gift_type, emoji in self.GIFTS:
            for story_id in gift_stories.story_ids(gift_type, emoji):
                yield gift_type, emoji, story_id

    def test_both_languages_agree_on_naming_the_user(self):
        lists = list(gift_stories._STORIES.values())
        lists += list(gift_stories.PAINTING_STORIES.values())
        lists.append(gift_stories.PAINTING_STORIES_ANY)
        for stories in lists:
            for story in stories:
                self.assertEqual("{name}" in story["ru"],
                                 "{name}" in story["en"], story["en"])

    def test_a_painting_is_told_about_by_what_is_on_it(self):
        for picture, emoji in activities.PAINTING_GIFT_EMOJI.items():
            with self.subTest(painting=picture):
                own = gift_stories.PAINTING_STORIES[emoji]
                told = gift_stories._get_stories("painting", emoji)
                self.assertEqual(told[:len(own)], own)
                # ...and shares the ones about painting itself
                self.assertEqual(told[len(own):],
                                 gift_stories.PAINTING_STORIES_ANY)
        others = [s for emoji, stories in gift_stories.PAINTING_STORIES.items()
                  for s in stories]
        self.assertEqual(len(others), len({s["ru"] for s in others}))

    def test_without_a_name_a_story_that_needs_one_is_swapped(self):
        """Cutting the name out left "because i knew would be happy"; in
        Russian it would need rewording, so another story is told."""
        def check(lang):
            for gift_type, emoji, story_id in self.stories():
                nameless = {s[lang].strip()
                            for s in gift_stories._get_stories(gift_type,
                                                               emoji)
                            if "{name}" not in s["ru"]}
                text = gift_stories.get_story(gift_type, story_id,
                                              emoji=emoji)
                with self.subTest(gift=gift_type, emoji=emoji,
                                  story=story_id):
                    # a whole story as written, not one with a word cut out
                    self.assertIn(text, nameless)
                    # the same gift keeps its story each time it is shown
                    self.assertEqual(gift_stories.get_story(
                        gift_type, story_id, emoji=emoji), text)
        in_both_languages(check)

    def test_stories_that_need_no_name_stay_as_they_are(self):
        for gift_type, emoji, story_id in self.stories():
            story = gift_stories._story(gift_type, story_id, emoji)
            if "{name}" not in story["ru"]:
                self.assertEqual(
                    gift_stories.get_story(gift_type, story_id, emoji=emoji),
                    gift_stories.get_story(gift_type, story_id, name="Катя",
                                           emoji=emoji))

    def test_with_a_name_the_story_uses_it(self):
        named = [(t, e, i) for t, e, i in self.stories()
                 if "{name}" in gift_stories._story(t, i, e)["ru"]]
        self.assertTrue(named)
        for gift_type, emoji, story_id in named:
            self.assertIn("Катя", gift_stories.get_story(
                gift_type, story_id, name="Катя", emoji=emoji))

    def test_each_story_has_one_id(self):
        for gift_type, emoji in self.GIFTS:
            with self.subTest(gift=gift_type, emoji=emoji):
                ids = gift_stories.story_ids(gift_type, emoji)
                told = [gift_stories._story(gift_type, i, emoji)["ru"]
                        for i in ids]
                self.assertEqual(sorted(told), sorted(
                    s["ru"] for s in gift_stories._get_stories(gift_type,
                                                               emoji)))
                self.assertIn(gift_stories.random_story_id(gift_type, emoji),
                              ids)

    def test_a_new_story_doesnt_change_the_ones_already_given(self):
        """A painting keeps its story in the gallery for good, so adding a
        story to either list must leave every given id telling the same,
        with the user's name or without it."""
        extra = {"ru": "новая", "en": "new"}
        for emoji in activities.PAINTING_GIFT_EMOJI.values():
            ids = gift_stories.story_ids("painting", emoji)
            before = {(i, name): gift_stories.get_story("painting", i, name,
                                                        emoji=emoji)
                      for i in ids for name in ("", "Катя")}
            for grown in ({"PAINTING_STORIES": {
                              **gift_stories.PAINTING_STORIES,
                              emoji: gift_stories.PAINTING_STORIES[emoji]
                              + [extra]}},
                          {"PAINTING_STORIES_ANY":
                              gift_stories.PAINTING_STORIES_ANY + [extra]}):
                with self.subTest(emoji=emoji, grown=list(grown)), \
                        mock.patch.multiple(gift_stories, **grown):
                    for (i, name), text in before.items():
                        self.assertEqual(gift_stories.get_story(
                            "painting", i, name, emoji=emoji), text)

    def test_story_ids_out_of_range_wrap_around(self):
        self.assertTrue(gift_stories.get_story("fish", 1000))
        self.assertTrue(gift_stories.get_story("fish", -1))


if __name__ == "__main__":
    unittest.main()
