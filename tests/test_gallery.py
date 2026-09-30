"""Tests for the gallery of paintings Claudy has given (core.gallery)."""

import unittest

from claudy.content import gift_stories, phrases, ui_text
from claudy.content.sprites.activities import PICTURES
from claudy.content.sprites.items import PAINTED
from claudy.core import gallery
from claudy.core.activities import PAINTING_GIFT_EMOJI
from tests import support


def entry(picture, day, story=0):
    return {"picture": picture, "date": f"2026-09-{day:02d}", "story": story}


class GalleryTests(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()      # Russian, like the other tests

    def test_the_most_recently_given_hangs_first(self):
        shown = gallery.paintings([entry("boat", 20), entry("stars", 22),
                                   entry("self", 21)])
        self.assertEqual([p.picture for p in shown], ["stars", "self", "boat"])

    def test_a_repeat_hangs_once_with_every_copy(self):
        shown = gallery.paintings([entry("boat", 20, 1), entry("stars", 21),
                                   entry("boat", 23, 2)])
        self.assertEqual([p.picture for p in shown], ["boat", "stars"])
        boat = shown[0]
        self.assertEqual(boat.count, 2)
        emoji = PAINTING_GIFT_EMOJI["boat"]
        self.assertEqual([c.story for c in boat.copies],
                         [gift_stories.get_story("painting", 2, emoji=emoji),
                          gift_stories.get_story("painting", 1, emoji=emoji)])
        self.assertEqual([c.date for c in boat.copies],
                         [ui_text.format_date("2026-09-23"),
                          ui_text.format_date("2026-09-20")])

    def test_given_the_same_day_the_later_one_counts_as_newer(self):
        shown = gallery.paintings([entry("boat", 20), entry("stars", 20)])
        self.assertEqual([p.picture for p in shown], ["stars", "boat"])

    def test_a_picture_claudy_no_longer_paints_is_left_out(self):
        entries = [entry("boat", 20), entry("gone", 21)]
        self.assertEqual([p.picture for p in gallery.paintings(entries)],
                         ["boat"])
        self.assertEqual(gallery.copies_given(entries), 1)

    def test_each_painting_can_be_drawn(self):
        for picture in PICTURES:
            with self.subTest(painting=picture):
                shown, = gallery.paintings([entry(picture, 20)])
                self.assertEqual(PAINTED[shown.item], picture)

    def test_a_story_that_needs_a_name_is_told_with_it(self):
        emoji = PAINTING_GIFT_EMOJI["boat"]
        named = [i for i in gift_stories.story_ids("painting", emoji)
                 if "{name}" in gift_stories._story("painting", i, emoji)["ru"]]
        shown, = gallery.paintings([entry("boat", 20, named[0])], name="Катя")
        self.assertIn("Катя", shown.copies[0].story)


class TitleTests(unittest.TestCase):

    def test_every_painting_has_a_title_in_both_languages(self):
        for picture in PICTURES:
            with self.subTest(painting=picture):
                titles = set()
                for lang in ("en", "ru"):
                    phrases.set_language(lang)
                    titles.add(ui_text.painting_title(picture))
                self.assertEqual(len(titles), 2)
        phrases.set_language("ru")

    def test_the_header_counts_paintings_in_russian_and_english(self):
        phrases.set_language("ru")
        self.assertEqual(
            [ui_text.gallery_header(n) for n in (1, 3, 5, 21)],
            ["1 картина", "3 картины", "5 картин", "21 картина"])
        phrases.set_language("en")
        self.assertEqual([ui_text.gallery_header(n) for n in (1, 2)],
                         ["1 painting", "2 paintings"])
        phrases.set_language("ru")


if __name__ == "__main__":
    unittest.main()
