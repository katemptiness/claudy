"""Tests for the shared drawing code (art, scene) with a recording canvas."""

import unittest

from claudy.config import (
    FRIEND_SHADES, OVERLAY_HEIGHT, PALETTE, PIXEL_SCALE, SHADES, SPRITE_SIZE,
)
from claudy.core.controller import Controller
from claudy.render import art
from claudy.render.canvas import Canvas, ImageCache
from claudy.render.scene import BUBBLE_MAX_TEXT_WIDTH, Scene
from tests import support


class RecordingCanvas(Canvas):
    """Measures text as 7 px per character and records every call."""

    def __init__(self):
        self.calls = []

    def image(self, key, x, y, alpha=1.0):
        self.calls.append(("image", key, x, y))

    def rect(self, x, y, w, h, rgba):
        self.calls.append(("rect", x, y, w, h, rgba))

    def text(self, text, x, y, size, rgba, bold=False):
        self.calls.append(("text", text, x, y))

    def measure(self, text, size, bold=False):
        return len(text) * 7, 15

    def of(self, kind):
        return [c for c in self.calls if c[0] == kind]


class ArtTests(unittest.TestCase):

    def test_sprite_image_size_and_colors(self):
        image = art.build(art.sprite_key("idle"))
        self.assertEqual((image.width, image.height), (SPRITE_SIZE, SPRITE_SIZE))
        self.assertIsNone(image.rows[0][0])
        self.assertEqual(image.rows[6][5], PALETTE[1])  # body

    def test_shading_lights_the_crab_from_above(self):
        rows = art.build(art.sprite_key("idle")).rows
        self.assertEqual(rows[5][6], SHADES["highlight"])   # top edge
        self.assertEqual(rows[11][6], SHADES["shadow"])     # bottom row
        self.assertEqual(rows[13][4], SHADES["shadow"])     # a leg
        self.assertEqual(rows[7][5], SHADES["glint"])       # eye, top-left
        self.assertEqual(rows[8][6], PALETTE[2])            # rest of the eye

    def test_squinting_eyes_get_no_glint(self):
        tones = art.shading(art.SPRITES["blink"])
        self.assertNotIn("glint", tones.values())

    def test_friend_uses_its_own_shades(self):
        rows = art.build(art.sprite_key("idle", friend=True)).rows
        self.assertEqual(rows[5][6], FRIEND_SHADES["highlight"])

    def test_flip_mirrors_rows(self):
        plain = art.build(art.sprite_key("wave"))
        flipped = art.build(art.sprite_key("wave", flip=True))
        for a, b in zip(plain.rows, flipped.rows):
            self.assertEqual(a, tuple(reversed(b)))

    def test_friend_is_recolored(self):
        crab = art.build(art.sprite_key("idle"))
        friend = art.build(art.sprite_key("idle", friend=True))
        self.assertNotEqual(crab.rows[6], friend.rows[6])

    def test_unknown_sprite_falls_back_to_idle(self):
        self.assertEqual(art.sprite_key("nope"), art.sprite_key("idle"))

    def test_every_particle_image_builds(self):
        from claudy.content.sprites.particles import PARTICLE_ART
        for name in PARTICLE_ART:
            with self.subTest(particle=name):
                image = art.build(art.particle_key(name))
                widths = {len(row) for row in image.rows}
                self.assertEqual(len(widths), 1, "ragged rows")

    def test_tint_recolors_gold(self):
        plain = art.build(art.particle_key("sparkle"))
        red = art.build(art.particle_key("sparkle", "#FF0000"))
        self.assertEqual(red.rows[0][2], (1.0, 0.0, 0.0, 1.0))
        self.assertNotEqual(plain.rows[0][2], red.rows[0][2])

    def test_image_cache_builds_once(self):
        made = []
        cache = ImageCache(lambda pixels: made.append(pixels) or len(made))
        first = cache.get(art.sprite_key("idle"))
        second = cache.get(art.sprite_key("idle"))
        self.assertEqual(first, second)
        self.assertEqual(len(made), 1)
        self.assertEqual(first[1:], (SPRITE_SIZE, SPRITE_SIZE))


class SceneTestCase(unittest.TestCase):

    def setUp(self):
        support.reset_singletons()
        support.seeded()
        self.period = support.fixed_period("day")
        self.period.start()
        self.addCleanup(self.period.stop)
        self.ctl = Controller(support.FakePlatform(), support.SCREEN_WIDTH, 58)
        self.scene = Scene(self.ctl)
        for _ in range(80):
            self.ctl.tick(50)


class CrabAndGroundTests(SceneTestCase):

    def test_crab_is_drawn_facing_its_direction(self):
        canvas = RecordingCanvas()
        self.ctl.character.facing_right = False
        self.ctl.view = self.ctl.character.view()
        self.scene.paint_crab(canvas)
        (_, key, _, _), = canvas.of("image")
        self.assertEqual(key, art.sprite_key("idle", flip=True))

    def test_friend_drawn_behind_claudy(self):
        self.ctl.character.friend_visible = True
        self.ctl.view = self.ctl.character.view()
        canvas = RecordingCanvas()
        self.scene.paint_crab(canvas)
        keys = [c[1] for c in canvas.of("image")]
        self.assertEqual(keys[0][2], True)   # friend first (behind)
        self.assertEqual(keys[1][2], False)

    def test_juggled_balls_fly_behind_claudy(self):
        self.ctl.character.force_activity("juggling")
        self.ctl.view = self.ctl.character.update(100)
        canvas = RecordingCanvas()
        self.scene.paint_crab(canvas)
        kinds = [c[1][0] for c in canvas.of("image")]
        self.assertEqual(kinds, ["particle"] * 3 + ["sprite"])

    def _shadow_width(self, height):
        self.ctl.view = dict(self.ctl.view, y_offset=height)
        canvas = RecordingCanvas()
        self.scene.paint_ground(canvas)
        middle = max(canvas.of("rect"), key=lambda c: c[3])
        return middle[3], middle[5][3]

    def test_shadow_shrinks_and_fades_in_the_air(self):
        ground_w, ground_a = self._shadow_width(0)
        air_w, air_a = self._shadow_width(40)
        self.assertEqual(ground_w, 10 * PIXEL_SCALE)
        self.assertLess(air_w, ground_w)
        self.assertLess(air_a, ground_a)

    def test_gift_and_particles_on_the_ground(self):
        self.ctl.test_gift()
        self.ctl.particles.add("heart", 100, 80)
        canvas = RecordingCanvas()
        self.scene.paint_ground(canvas)
        (_, emoji, _, _), = canvas.of("text")
        self.assertEqual(emoji, self.ctl.gift_emoji)
        (_, key, x, y), = canvas.of("image")
        self.assertEqual(key, art.particle_key("heart"))
        self.assertLess(y, OVERLAY_HEIGHT - 80)


class BubbleTests(SceneTestCase):

    def say(self, text, ms=5000):
        self.ctl._say(text)
        for _ in range(int(ms / 50)):
            self.ctl.tick(50)

    def test_short_line_fits_one_row(self):
        self.say("привет!")
        layout = self.scene.bubble_layout(RecordingCanvas())
        self.assertEqual(layout.lines, ("привет!",))
        self.assertGreater(layout.height, layout.box_height)  # tail below

    def test_long_line_wraps(self):
        text = "a toy! i'll put it next to my pillow! " * 2
        self.say(text.strip())
        layout = self.scene.bubble_layout(RecordingCanvas())
        self.assertGreater(len(layout.lines), 1)
        for w in layout.line_widths:
            self.assertLessEqual(w, BUBBLE_MAX_TEXT_WIDTH)
        self.assertEqual(" ".join(layout.lines), text.strip())

    def test_text_types_out_in_place(self):
        self.say("hello there friend", ms=100)
        canvas = RecordingCanvas()
        self.scene.paint_bubble(canvas)
        (_, partial, x_partial, _), = canvas.of("text")
        self.assertTrue("hello there friend".startswith(partial))
        self.assertLess(len(partial), len("hello there friend"))

        for _ in range(40):
            self.ctl.tick(50)
        canvas = RecordingCanvas()
        self.scene.paint_bubble(canvas)
        (_, full, x_full, _), = canvas.of("text")
        self.assertEqual(full, "hello there friend")
        self.assertEqual(x_partial, x_full)

    def test_bubble_fits_its_window(self):
        self.say("a fairly long sentence that needs wrapping, surely")
        canvas = RecordingCanvas()
        layout = self.scene.bubble_layout(canvas)
        self.scene.paint_bubble(canvas)
        for _, x, y, w, h, _ in canvas.of("rect"):
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + w, layout.width)
            self.assertLessEqual(y + h, layout.height)


if __name__ == "__main__":
    unittest.main()
