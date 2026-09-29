"""Platform-independent application logic shared by the backends.

The Controller owns Claudy's brain (Character), particles and the gift
Claudy offers the user. A backend creates windows, forwards user input and
system events here, calls tick() every frame and draws what it returns.
Everything the controller needs from the platform goes through the small
Platform interface below.
"""

import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from claudy.config import MAX_TICK_MS, PIXEL_SCALE, SPRITE_SIZE, WINDOW_WIDTH
from claudy.content import phrases, ui_text
from claudy.content.phrases import pick
from claudy.content.sprites.items import DREAM_ART, GIFT_ART
from claudy.core.activities import ACTIVITIES
from claudy.core.character import Character
from claudy.core.memory import Memory
from claudy.core.particles import ParticleSystem
from claudy.core import schedule
from claudy.core.settings import Settings
from claudy.core.speech import Speech
from claudy.log import log

# Idle chatter never follows another line faster than this
CHATTER_GAP_MS = 3000
# Where particles spawn, as heights above the ground overlay's bottom edge:
# around the top of the sprite, or at Claudy's feet (the sprite's last two
# pixel rows are empty)
PARTICLE_HEAD_Y = SPRITE_SIZE
PARTICLE_FEET_Y = 2 * PIXEL_SCALE
# The developer test gift picks from every gift that has a picture
TEST_GIFT_EMOJIS = tuple(GIFT_ART)

# Claudy dreams while he sleeps, and rarely: minutes apart, so that catching
# one feels like catching it, not like watching a slide show. A dream fades
# in, holds, and fades out again; nothing about it asks anything of the user.
DREAM_GAP_MS = (150000, 300000)
DREAM_FADE_MS = 700
DREAM_HOLD_MS = 2600
# When something else happens (he wakes, or says something) the dream goes
# faster: a cloud lingering behind a speech bubble frames it like a badge
DREAM_LET_GO_MS = 250


class Platform:
    """What the controller asks of a backend."""

    def open_claude(self):
        raise NotImplementedError

    def open_claude_code(self):
        raise NotImplementedError

    def open_settings(self):
        raise NotImplementedError

    def open_gifts(self):
        raise NotImplementedError

    def show_about(self):
        raise NotImplementedError

    def quit(self):
        raise NotImplementedError


@dataclass
class MenuItem:
    """A context menu entry; backends turn these into native menus."""

    label: str = ""
    action: Optional[Callable[[], None]] = None
    enabled: bool = True
    submenu: List["MenuItem"] = field(default_factory=list)
    separator: bool = False


SEPARATOR = MenuItem(separator=True)


def reading_time(text):
    """How long a speech bubble stays up once typed out, in seconds."""
    return max(2.0, min(5.0, len(text) * 0.15))


class Controller:

    def __init__(self, platform, screen_width, dock_tile_pitch):
        self.platform = platform
        self.settings = Settings.shared()
        self.memory = Memory.shared()
        self.character = Character(screen_width)
        self.particles = ParticleSystem()
        self.dock_tile_pitch = dock_tile_pitch
        self._update_walk_bounds()

        # Time since launch as the controller sees it (ms). Timers below run
        # on this clock, so they pause while the computer sleeps.
        self._clock_ms = 0.0

        # The gift Claudy is offering (emoji shown next to it), if any
        self.gift_emoji = None
        self._gift_expires_ms = 0.0

        # Speech: a pinned bubble (gift announcement) blocks other lines
        self.speech = Speech()
        self._speech_pinned = False
        self._speech_hides_ms = None
        self._last_speech_ms = -CHATTER_GAP_MS
        self._dream = None
        self._dream_age_ms = 0.0
        self._dream_out_ms = DREAM_FADE_MS      # how long its fade-out takes
        self._dream_due_ms = random.uniform(*DREAM_GAP_MS)

        self.character.wake_up()
        self.view = self.character.view()

    # ---- Frame loop ----

    def tick(self, dt):
        """Advance everything by dt ms; returns the character view to draw."""
        dt = min(dt, MAX_TICK_MS)
        self._clock_ms += dt
        self._update_walk_bounds()
        self.view = self.character.update(dt)
        for event in self.character.take_events():
            try:
                self._handle_event(*event)
            except Exception:
                log.exception("failed to handle event %r", event)
        if self.gift_emoji and self._clock_ms >= self._gift_expires_ms:
            self._expire_gift()
        if self._speech_hides_ms is not None and self._clock_ms >= self._speech_hides_ms:
            self._hide_speech()
        self.speech.update(dt)
        self.particles.update(dt)
        self._update_dream(dt)
        return self.view

    # ---- Dreams ----

    def _update_dream(self, dt):
        """Let a picture surface while Claudy is asleep, then let it go."""
        quiet_sleep = (self.character.state == "sleeping"
                       and not self.speech.visible)
        if self._dream is not None:
            if not quiet_sleep:
                self._let_dream_go()
            self._dream_age_ms += dt
            if self._dream_age_ms >= (DREAM_FADE_MS + DREAM_HOLD_MS
                                      + self._dream_out_ms):
                self._dream = None
            return
        if not quiet_sleep:
            return          # the wait only runs while he is quietly asleep
        self._dream_due_ms -= dt
        if self._dream_due_ms <= 0:
            self._dream = self._pick_dream()
            self._dream_age_ms = 0.0
            self._dream_out_ms = DREAM_FADE_MS
            self._dream_due_ms = random.uniform(*DREAM_GAP_MS)

    def _let_dream_go(self):
        """Fade the dream out quickly, from wherever it is: waking up doesn't
        cut it off mid-air, and a dream still fading in doesn't flash to full
        opacity on its way out."""
        if self._dream_out_ms == DREAM_LET_GO_MS:
            return
        alpha = self.dream[1]
        self._dream_out_ms = DREAM_LET_GO_MS
        self._dream_age_ms = (DREAM_FADE_MS + DREAM_HOLD_MS
                              + (1 - alpha) * DREAM_LET_GO_MS)

    def _pick_dream(self):
        """Something Claudy actually did lately, or None if nothing has
        left a picture yet — he doesn't dream of what he hasn't done."""
        done = [name for name in self.memory.recent_activities()
                if name in DREAM_ART]
        if not done:
            return None
        return random.choice(DREAM_ART[random.choice(done)])

    @property
    def dream(self):
        """(picture, opacity) while Claudy is dreaming, else None."""
        if self._dream is None:
            return None
        age, fade = self._dream_age_ms, DREAM_FADE_MS
        ending = age - fade - DREAM_HOLD_MS
        if age < fade:
            alpha = age / fade
        elif ending <= 0:
            alpha = 1.0
        else:
            alpha = max(0.0, 1 - ending / self._dream_out_ms)
        return self._dream, alpha

    @property
    def clock_ms(self):
        """Milliseconds since launch — what the scene twinkles the star by."""
        return self._clock_ms

    @property
    def star(self):
        """The named star to hang in the sky, or None.

        None both when Claudy hasn't named one and while it is daylight, so
        a backend can simply hide the star's window whenever it is None.
        """
        star = self.memory.get_star()
        return star if star and schedule.is_dark() else None

    @property
    def is_dragging(self):
        return self.character.state == "dragging"

    def set_screen_width(self, width):
        """The screen changed size: another monitor, a new resolution."""
        ch = self.character
        ch.screen_width = width
        self._update_walk_bounds()
        # Inside the screen he walks back to the Dock by himself; off it he
        # would do that out of sight, so he is put back on the Dock at once
        if not 0 <= ch.x <= width:
            ch.x = min(max(ch.x, ch.walk_min_x), ch.walk_max_x)

    def _update_walk_bounds(self):
        # Applied every frame so the Dock-icons setting takes effect live
        self.character.update_walk_bounds(
            self.settings.dock_icons, self.dock_tile_pitch)

    def _handle_event(self, kind, data):
        if kind == "message":
            self._say(data, chatter=not self.character.is_busy)
        elif kind == "particle":
            if data == "zzz" and self._dream is not None:
                return      # the dream shows he's asleep; zzz would cross it
            height = self.view["y_offset"]
            self.particles.add(data, WINDOW_WIDTH / 2, PARTICLE_HEAD_Y + height,
                               PARTICLE_FEET_Y + height, self.view["facing_right"])
        elif kind == "gift":
            self._offer_gift(data)
        elif kind == "gift_star":
            self.memory.add_gift("star", "⭐", name=data, collected=True)
            self.memory.name_star(data)

    # ---- Speech ----

    def _say(self, text, chatter=False):
        """Show a line. Idle chatter never talks over a line still on
        screen, nor comes within CHATTER_GAP_MS of the last one starting."""
        if self._speech_pinned:
            return
        if chatter and (self._speech_hides_ms is not None
                        or self._clock_ms - self._last_speech_ms < CHATTER_GAP_MS):
            return
        self._show_speech(text, reading_time(text))

    def _pin_speech(self, text, duration_s):
        """Show a line that nothing else may replace until it's unpinned."""
        self._show_speech(text, duration_s)
        self._speech_pinned = True

    def _unpin_speech(self):
        if self._speech_pinned:
            self._hide_speech()

    def _show_speech(self, text, duration_s):
        self._last_speech_ms = self._clock_ms
        self._speech_hides_ms = (self._clock_ms + Speech.typing_ms(text)
                                 + duration_s * 1000)
        self.speech.say(text)

    def _hide_speech(self):
        self._speech_pinned = False
        self._speech_hides_ms = None
        self.speech.hide()

    # ---- Gifts from Claudy ----

    def _offer_gift(self, gift):
        if self.gift_emoji or self.memory.get_pending_gift():
            return
        limit = self.settings.gift_limit
        if limit > 0 and self.memory.count_gifts_today() >= limit:
            return

        self.memory.add_gift(gift["type"], gift["emoji"])
        self.gift_emoji = str(gift["emoji"])
        self.character.wait_for_gift(True)

        duration = self.settings.gift_duration_seconds()
        self._gift_expires_ms = self._clock_ms + duration * 1000
        self._pin_speech(pick(phrases.GIFT_ANNOUNCE_PHRASES,
                              name=self.settings.user_name), duration)

    def _collect_gift(self):
        if not self.memory.collect_gift():
            return
        self._clear_gift()
        self._say(pick(phrases.GIFT_COLLECT_PHRASES))

    def _expire_gift(self):
        self.memory.discard_pending_gift()
        self._clear_gift()
        self._say(pick(phrases.GIFT_EXPIRED_PHRASES))

    def _clear_gift(self):
        self.gift_emoji = None
        self.character.wait_for_gift(False)
        self._unpin_speech()

    # ---- User input ----

    def on_click(self):
        self.memory.record_click()
        if self.gift_emoji:
            self._collect_gift()
            self.character.react("happy")
        else:
            self.character.greet(self.memory.is_attached())

    def on_double_click(self):
        self.platform.open_claude()

    def on_hover(self, inside):
        self.character.hover(inside)

    def on_drag_start(self):
        self.character.start_drag()

    def on_drag_move(self, x, height=0.0):
        """The pointer holds Claudy at `x`, `height` px above his resting
        line. The backend moves his window itself; the height only sizes
        his shadow on the Dock, which without it is drawn as if he were
        standing there."""
        self.character.drag_to(x, height)

    def on_drop(self, height):
        """Released `height` px above Claudy's resting line."""
        self.character.drop(height)

    # ---- System events ----

    def on_system_sleep(self):
        self.character.go_to_sleep()

    def on_system_wake(self):
        self.character.wake_up()

    def on_app_launched(self, app_id, app=None, display_name=""):
        """The user opened an app. `app` is its app_reactions.App, if known."""
        count = self.memory.record_app_launch(app_id)
        phrase = None
        if count >= 3 and display_name and random.random() < 0.5:
            phrase = pick(phrases.APP_COUNT_PHRASES, app=display_name, n=count)
        elif app:
            phrase = pick(app.phrases)
        # When Claudy joins in, the phrase is the activity's opening line:
        # said on its own, the activity's first line would replace it a
        # frame later.
        if app and app.activity and self.character.trigger_activity(
                app.activity, opening=phrase):
            return
        if phrase and not self.character.is_reacting:
            self._say(phrase)

    # ---- Context menu ----

    def give_gift(self, gift_type):
        self.character.receive_gift(gift_type)

    def play_activity(self, name):
        self.character.force_activity(name)

    def test_gift(self):
        self._offer_gift({"type": "test", "emoji": random.choice(TEST_GIFT_EMOJIS)})

    def menu(self):
        """The context menu, rebuilt each time it opens."""
        p = self.platform
        label = ui_text.label
        items = [
            MenuItem(label("open_claude"), p.open_claude),
            MenuItem(label("open_claude_code"), p.open_claude_code),
            SEPARATOR,
            MenuItem(label("give_gift"), submenu=self._gift_menu()),
            SEPARATOR,
        ]
        if self.settings.dev_mode:
            activities = [
                MenuItem(name.capitalize(),
                         lambda name=name: self.play_activity(name))
                for name in sorted(ACTIVITIES)
            ]
            activities += [SEPARATOR, MenuItem(label("test_gift"), self.test_gift)]
            items += [MenuItem(label("activities"), submenu=activities), SEPARATOR]
        items += [
            MenuItem(label("gifts"), p.open_gifts),
            MenuItem(label("settings"), p.open_settings),
            MenuItem(label("about"), p.show_about),
            SEPARATOR,
            MenuItem(label("quit"), p.quit),
        ]
        return items

    def _gift_menu(self):
        ch = self.character
        items = []
        for gift_type, title in ui_text.localized(ui_text.GIFT_MENU):
            owned =((gift_type == "toy" and ch.has_toy)
                     or (gift_type == "book" and ch.has_book))
            if owned:
                title += " ✓"
            items.append(MenuItem(
                title, lambda g=gift_type: self.give_gift(g),
                enabled=ch.can_accept_gift(gift_type)))
        if not ch.can_receive_gift():
            items += [SEPARATOR, MenuItem(ui_text.label("wait_a_bit"),
                                          enabled=False)]
        return items
