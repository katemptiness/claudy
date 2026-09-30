"""Static checks on sprites, activity definitions and phrases."""

import unittest

from claudy.config import GRID, PALETTE, PIXEL_SCALE, WINDOW_WIDTH
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
    for picture, phases in activities.PAINTINGS.items():
        for phase in phases:
            yield f"painting:{picture}", phase
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
                # must fit the crab window
                self.assertGreaterEqual(width, GRID)
                self.assertEqual(width % 2, 0)
                self.assertLessEqual(width * PIXEL_SCALE, WINDOW_WIDTH)
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


class ItemArtTests(unittest.TestCase):

    def test_items_share_claudys_pixel_grid(self):
        """A gift is an object in Claudy's world, so it uses his pixels."""
        from claudy.config import PIXEL_SCALE
        from claudy.content.sprites.items import ITEM_SCALE
        self.assertEqual(ITEM_SCALE, PIXEL_SCALE)

    def test_only_the_star_in_the_sky_leaves_claudys_grid(self):
        """Everything else is an object on the Dock and shares his pixels."""
        from claudy.content.sprites.items import (
            ITEM_SCALE, ITEM_SCALES, SKY_SCALE, STAR_TWINKLE,
        )
        self.assertEqual(set(ITEM_SCALES), {name for name, _ in STAR_TWINKLE})
        self.assertLess(SKY_SCALE, ITEM_SCALE)

    def test_the_star_keeps_its_size_as_it_twinkles(self):
        """Its window centers each picture; a size change would make it jump."""
        from claudy.content.sprites.items import ITEM_ART, STAR_TWINKLE
        sizes = {(len(ITEM_ART[name].split()), len(ITEM_ART[name].split()[0]))
                 for name, _ in STAR_TWINKLE}
        self.assertEqual(len(sizes), 1)

    def test_pictures_have_no_empty_border(self):
        """Pictures are placed by their size: an empty row or column along an
        edge would push them off center and off the ground."""
        from claudy.content.sprites.items import ITEM_ART, STAR_TWINKLE
        framed = {name for name, _ in STAR_TWINKLE}   # sized like the others
        for name, text in ITEM_ART.items():
            if name in framed:
                continue
            with self.subTest(item=name):
                lines = text.split()
                edges = (lines[0], lines[-1], "".join(l[0] for l in lines),
                         "".join(l[-1] for l in lines))
                for edge in edges:
                    self.assertNotEqual(set(edge), {"."})

    def test_item_grids_are_rectangular_and_use_known_colors(self):
        from claudy.content.sprites.items import ITEM_ART, ITEM_COLORS
        for name, text in ITEM_ART.items():
            with self.subTest(item=name):
                lines = [line.strip() for line in text.strip().splitlines()]
                self.assertEqual(len({len(line) for line in lines}), 1,
                                 "rows differ in width")
                symbols = {ch for line in lines for ch in line} - {"."}
                self.assertLessEqual(symbols, set(ITEM_COLORS))

    def test_every_gift_claudy_offers_has_a_picture(self):
        from claudy.content.sprites.items import GIFT_ART, ITEM_ART, PAINTED
        offered = {c["emoji"] for c in activities.CATCHES if c["good"]}
        offered |= {m["gift_emoji"] for m in activities.MAGIC_RESULTS
                    if m["gift_emoji"]}
        offered |= {"\U0001F41A", "\u2B50"}   # the shell found, the star named
        offered |= set(activities.PAINTING_GIFT_EMOJI.values())
        for emoji in offered:
            with self.subTest(gift=emoji):
                self.assertIn(emoji, GIFT_ART)
                self.assertIn(GIFT_ART[emoji], ITEM_ART.keys() | PAINTED.keys())

    def test_no_canvas_uses_the_brush_tip_color(self):
        """`o` is the brush tip, recolored with the paint: flame orange on a
        canvas would come out in the brush's color instead."""
        from claudy.content.sprites.activities import PICTURES
        for picture, stages in PICTURES.items():
            for n, (_, paint, canvas) in enumerate(stages, 1):
                with self.subTest(painting=picture, stage=n):
                    self.assertNotIn("o", canvas)
                    self.assertNotEqual(paint, "o")

    def test_a_painting_given_away_is_the_one_on_the_easel(self):
        """Each painting has an emoji to be given under, and the picture
        left on the Dock for it is the one lifted off that painting."""
        from claudy.content.sprites.activities import PICTURES
        from claudy.content.sprites.items import GIFT_ART, PAINTED
        self.assertEqual(set(activities.PAINTING_GIFT_EMOJI),
                         set(activities.PAINTINGS))
        self.assertEqual(set(PAINTED.values()), set(PICTURES))
        for picture, emoji in activities.PAINTING_GIFT_EMOJI.items():
            with self.subTest(painting=picture):
                self.assertEqual(PAINTED[GIFT_ART[emoji]], picture)


class DreamArtTests(unittest.TestCase):

    def test_every_dream_names_a_real_activity_and_a_real_picture(self):
        from claudy.content.sprites.items import DREAM_ART, ITEM_ART, PAINTED
        for name, pictures in DREAM_ART.items():
            with self.subTest(activity=name):
                self.assertIn(name, activities.ACTIVITIES)
                self.assertTrue(pictures)
                for picture in pictures:
                    self.assertIn(picture, ITEM_ART.keys() | PAINTED.keys())

    def test_claudy_dreams_of_the_pictures_he_paints(self):
        from claudy.content.sprites.items import DREAM_ART, PAINTED
        self.assertEqual(set(DREAM_ART["painting"]), set(PAINTED))


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

    def test_every_activity_is_reachable_somewhere(self):
        """An activity in no period at all would never run, and nothing else
        would complain — the weights only say which names are allowed."""
        scheduled = {name for weights in schedule.ACTIVITY_WEIGHTS.values()
                     for name in weights}
        for name in activities.ACTIVITIES:
            with self.subTest(activity=name):
                self.assertIn(name, scheduled)

    def test_the_sky_is_dark_in_the_evening_and_not_at_noon(self):
        """The star follows the real clock, not a period: owl mode calls
        7:00 deep sleep, long after the stars have gone."""
        for hour in (19, 23, 0, 5):
            self.assertTrue(schedule.is_dark(hour), hour)
        for hour in (6, 12, 18):
            self.assertFalse(schedule.is_dark(hour), hour)

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
            phrases.PAINTING_ANNOUNCE_PHRASES,
            phrases.PAINTING_COLLECT_PHRASES, phrases.SITTER_NAG_PHRASES,
            phrases.SITTER_HOP_NAG_PHRASES,
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
