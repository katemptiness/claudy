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

from claudy.config import MAX_TICK_MS, SPRITE_SIZE, WINDOW_WIDTH
from claudy.content import phrases, ui_text
from claudy.content.phrases import pick
from claudy.core.activities import ACTIVITIES
from claudy.core.character import Character
from claudy.core.memory import Memory
from claudy.core.particles import ParticleSystem
from claudy.core.settings import Settings
from claudy.core.speech import Speech
from claudy.log import log

# Idle chatter never follows another line faster than this
CHATTER_GAP_MS = 3000
# Particles spawn around the top of the sprite. Particle coordinates are
# overlay x and height above the overlay's bottom edge.
PARTICLE_ORIGIN = (WINDOW_WIDTH / 2, SPRITE_SIZE)
TEST_GIFT_EMOJIS = ["🐟", "🐡", "💎", "⭐", "🌸", "🦋"]


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
        return self.view

    @property
    def is_dragging(self):
        return self.character.state == "dragging"

    def _update_walk_bounds(self):
        # Applied every frame so the Dock-icons setting takes effect live
        self.character.update_walk_bounds(
            self.settings.dock_icons, self.dock_tile_pitch)

    def _handle_event(self, kind, data):
        if kind == "message":
            self._say(data, chatter=not self.character.is_busy)
        elif kind == "particle":
            x, y = PARTICLE_ORIGIN
            self.particles.add(data, x, y + self.view["y_offset"])
        elif kind == "gift":
            self._offer_gift(data)
        elif kind == "gift_star":
            self.memory.add_gift("star", "⭐", name=data, collected=True)

    # ---- Speech ----

    def _say(self, text, chatter=False):
        """Show a line. Idle chatter is dropped if Claudy just spoke."""
        if self._speech_pinned:
            return
        if chatter and self._clock_ms - self._last_speech_ms < CHATTER_GAP_MS:
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

    def on_drag_move(self, x):
        self.character.drag_to(x)

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
        if phrase and not self.character.is_reacting:
            self._say(phrase)
        if app and app.activity:
            self.character.trigger_activity(app.activity)

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
