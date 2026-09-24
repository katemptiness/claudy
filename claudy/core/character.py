"""Character state machine and phased animation engine.

The Character is Claudy's brain. It decides what Claudy does, advances
activity phases, and moves the crab. It knows nothing about windows: each
update() returns what to draw, and everything that should happen outside
(speech, particles, gifts, the friend arriving) is queued as an event for
the controller to pick up with take_events().

Events are (type, data) tuples:
    ("message", text)         say something
    ("particle", kind)        puff one particle
    ("gift", {type, emoji})   Claudy wants to give the user something
    ("gift_star", name)       Claudy named a star after the user
"""

import random
import time
from dataclasses import replace
from datetime import date

from claudy.config import DOCK_EDGE_PADDING, DOCK_WALK_MARGIN, WINDOW_WIDTH
from claudy.content import phrases
from claudy.content.phrases import pick, pick_personal, t
from claudy.core import schedule
from claudy.core.activities import (
    ACTIVITIES, CATCHES, FISH_GIFT_CHANCE, FRIEND_ACTIVITY_POOL,
    FRIEND_ANIMATIONS, FRIEND_FRAME_MS, FRIEND_GOODBYE, MAGIC_GIFT_CHANCE,
    MAGIC_RESULTS, REACTION_HEART_INTERVAL_MS, REACTIONS,
    RECENT_ACTIVITY_BLOCK, SANDCASTLE_SUCCESS_CHANCE, SHELL_GIFT_CHANCE,
    STAR_NAMING_CHANCE, WAKING,
)
from claudy.core.animations import Bounce, Fall, Hop, Shake
from claudy.core.memory import Memory
from claudy.core.settings import Settings

WALK_SPEED = 0.04          # px/ms
WANDER_SPEED = 0.03        # px/ms while looking for shells
HOP_SPEED = 0.05           # px/ms sideways while playing
WALK_FRAME_MS = 200
BLINK_MS = 150
IDLE_MS = (8000, 20000)    # how long to idle before picking something new
BLINK_GAP_MS = (2000, 6000)
HOVER_PHRASE_CHANCE = 0.3  # waving at the pointer only sometimes comes with words


class Character:
    """The crab's brain — state machine + animation engine."""

    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.x = screen_width / 2  # crab center x in screen coords
        self.y_offset = 0.0        # height above the resting line
        self.facing_right = True

        # "idle", "walking", "dragging", "reaction_<name>", "waking",
        # or an activity name
        self.state = "idle"
        self.state_timer = 0.0
        self.next_state_change = random.uniform(*IDLE_MS)

        # Horizontal walking bounds (crab-center coords). Default to the full
        # screen minus a window-width margin; the backend narrows these to the
        # Dock via update_walk_bounds() so Claudy only paces across the Dock.
        self.walk_min_x = WINDOW_WIDTH
        self.walk_max_x = screen_width - WINDOW_WIDTH

        # Walking
        self.target_x = self.x
        self.walk_frame_index = 0
        self.walk_frame_timer = 0.0

        # Phased activity: a private copy of the running activity's phases
        self.phases = []
        self.phase_index = 0
        self.phase_timer = 0.0
        self.phase_duration = 0.0
        self.frame_index = 0
        self.frame_timer = 0.0
        self.particle_timer = 0.0

        # Current reaction (see activities.REACTIONS)
        self.reaction = None

        # Idle chatter
        self.idle_phrase_timer = 0.0
        self.idle_phrase_cooldown = self._next_phrase_cooldown()

        # Blink
        self.is_blinking = False
        self.blink_timer = 0.0
        self.next_blink = random.uniform(*BLINK_GAP_MS)

        # Motion effects
        self.bounce = None   # Bounce
        self.shake = None    # Shake
        self.shake_dx = 0.0
        self.hop = None      # Hop, while playing
        self.hop_direction = 1
        self.wander_direction = 0  # nonzero while searching for shells
        self.fall = None     # Fall, after being dropped

        # Gift pause — stops activity transitions while waiting for user
        self.gift_waiting = False

        # User gifts to Claudy (session-only)
        self.has_marshmallow = False
        self.has_toy = False
        self._book_date = None  # the book is read for the rest of that day
        self.last_gift_received_time = 0.0

        # Last few activity names, used to avoid immediate repeats. Idle and
        # walking never get added (they don't go through _start_activity).
        self.recent_activities = []

        # Summoned friend
        self.friend_visible = False
        self.friend_sprite = "idle"
        self.friend_animation = None  # key into FRIEND_ANIMATIONS
        self.friend_frame = 0
        self.friend_frame_timer = 0.0
        self.friend_walk_target = None

        self._events = []

    # ---- Public API ----

    def update(self, dt):
        """Advance the state machine by dt milliseconds; return what to draw."""
        self._update_blink(dt)

        if self.state == "idle":
            self._update_idle(dt)
        elif self.state == "walking":
            self._update_walking(dt)
        elif self.reaction:
            self._update_reaction(dt)
        elif self.state != "dragging":  # position is controlled externally
            self._update_activity(dt)

        self._update_motion(dt)
        return self.view()

    def view(self):
        return {
            "sprite": self.sprite_name(),
            "x": self.x,
            "y_offset": self.y_offset,
            "shake_dx": self.shake_dx,
            "facing_right": self.facing_right,
            "friend_visible": self.friend_visible,
            "friend_sprite": self.friend_sprite,
            "show_toy": self.has_toy and self.state == "sleeping",
        }

    def take_events(self):
        """Return and clear the events queued since the last call."""
        events, self._events = self._events, []
        return events

    @property
    def is_busy(self):
        """True while doing something other than idling or walking."""
        return self.state not in ("idle", "walking")

    @property
    def is_reacting(self):
        return self.reaction is not None

    @property
    def has_book(self):
        return self._book_date == date.today().isoformat()

    def trigger_activity(self, name):
        """Start an activity if Claudy is free (e.g. the user opened an app)."""
        if name in ACTIVITIES and not self.is_busy:
            self._start_activity(name)

    def force_activity(self, name):
        """Start an activity right now, whatever is going on (dev menu)."""
        if name in ACTIVITIES:
            self._stop_current()
            self._start_activity(name)

    def react(self, name):
        """Interrupt whatever is going on to react to the user."""
        self._stop_current()
        reaction = REACTIONS[name]
        self.reaction = reaction
        self.state = f"reaction_{name}"
        self.state_timer = 0.0
        self.particle_timer = 0.0
        if reaction.bounce:
            self.bounce = Bounce()

    def greet(self, attached):
        """The user clicked Claudy."""
        name = Settings.shared().user_name
        if attached:
            self.react("happy_love")
            self._say(pick_personal(phrases.PERSONAL_CLICK_PHRASES,
                                    phrases.PERSONAL_CLICK_PHRASES_NAMELESS,
                                    name))
            self._burst("sparkle", 4)
            self._burst("heart", 3)
        else:
            self.react("happy")
            self._say(pick(phrases.GREETING_PHRASES))
            self._burst("sparkle", 4)

    def hover(self, inside):
        """The pointer entered or left Claudy."""
        if inside:
            if self.state != "dragging" and not self.is_reacting:
                self.react("wave")
                if random.random() < HOVER_PHRASE_CHANCE:
                    self._say(pick(phrases.HOVER_PHRASES))
        elif self.state == "reaction_wave":
            self._enter_idle()

    def start_drag(self):
        self._stop_current()
        self.state = "dragging"
        self.state_timer = 0.0

    def drag_to(self, x):
        self.x = x

    def drop(self, height):
        """Released `height` px above the resting line: fall back down."""
        self.fall = Fall(height)
        self.y_offset = self.fall.height
        self.react("surprise")
        self._burst("exclaim", 1)

    def go_to_sleep(self):
        """The computer is going to sleep."""
        self._stop_current()
        self._start_activity("sleeping")

    def wake_up(self):
        """Launch or the computer woke up: open eyes, stretch, say hi."""
        self._stop_current()
        if Memory.shared().is_attached():
            name = Settings.shared().user_name
            message = pick(phrases.WAKE_PHRASES, name=name)
        else:
            message = t("*зевает*")
        phases = list(WAKING)
        phases[-1] = replace(phases[-1], message=message)
        self._run_phases("waking", phases)

    def wait_for_gift(self, waiting):
        """Stay put next to an offered gift until it's taken (or expires)."""
        self.gift_waiting = waiting
        if waiting:
            self._enter_idle()

    def update_walk_bounds(self, dock_icons, tile_pitch):
        """Confine autonomous walking to the Dock, centered on screen.

        Estimates the Dock width from the icon count, then sets the left/right
        walking edges symmetrically around the screen center. Clamped within
        the full-screen safe range, so a very large count just restores
        roaming the whole screen.
        """
        full_lo = WINDOW_WIDTH
        full_hi = self.screen_width - WINDOW_WIDTH
        dock_width = max(0, dock_icons) * tile_pitch + 2 * DOCK_EDGE_PADDING
        center = self.screen_width / 2
        half = dock_width / 2
        lo = max(full_lo, center - half + DOCK_WALK_MARGIN)
        hi = min(full_hi, center + half - DOCK_WALK_MARGIN)
        if lo >= hi:
            lo = hi = center
        self.walk_min_x = lo
        self.walk_max_x = hi

    # ---- Gifts from the user ----

    def can_receive_gift(self):
        """Check if cooldown has elapsed for receiving gifts."""
        cooldown = Settings.shared().gift_cooldown_seconds()
        return (time.time() - self.last_gift_received_time) >= cooldown

    def can_accept_gift(self, gift_type):
        """Check if a specific gift type can be accepted right now."""
        if not self.can_receive_gift():
            return False
        if gift_type == "toy" and self.has_toy:
            return False
        if gift_type == "book" and self.has_book:
            return False
        return True

    def receive_gift(self, gift_type):
        """Handle user giving a gift to Claudy. Returns True if accepted."""
        if not self.can_accept_gift(gift_type):
            return False

        self.last_gift_received_time = time.time()
        if gift_type == "marshmallow":
            self.has_marshmallow = True
        elif gift_type == "toy":
            self.has_toy = True
        elif gift_type == "book":
            self._book_date = date.today().isoformat()

        # A gift counts as 2 clicks toward attachment
        Memory.shared().record_click()
        Memory.shared().record_click()

        self.react("gift_received")
        self._say(pick(phrases.GIFT_RECEIVE_PHRASES.get(
            gift_type, ["спасибо! :3"])))
        self._burst("sparkle", 5)
        self._burst("heart", 3)
        if gift_type == "song":
            self._burst("note", 4)
        return True

    # ---- Sprites ----

    def sprite_name(self):
        if self.state in ("idle", "walking") and self.is_blinking:
            return "blink"
        if self.state == "idle":
            return "idle"
        if self.state == "walking":
            return ("walk_a", "walk_b")[self.walk_frame_index]
        if self.reaction:
            return self.reaction.sprite_at(self.state_timer)
        if self.state == "dragging":
            return "surprise"
        if self.phases:
            frames = self.phases[self.phase_index].frames
            return frames[self.frame_index % len(frames)]
        return "idle"

    # ---- Events ----

    def _say(self, text):
        self._events.append(("message", text))

    def _burst(self, particle, count):
        self._events.extend([("particle", particle)] * count)

    # ---- Idle & walking ----

    def _next_phrase_cooldown(self):
        return random.uniform(*Settings.shared().speech_cooldown_range())

    def _pick_idle_phrase(self):
        """Pick an idle phrase — may be days-together or claude.ai easter egg."""
        name = Settings.shared().user_name
        mem = Memory.shared()

        # ~20% chance: days-together phrase (once per day)
        if not mem.days_phrase_shown_today() and random.random() < 0.2:
            days = mem.get_total_days()
            if days >= 2:
                mem.mark_days_phrase_shown()
                pool = (phrases.DAYS_MILESTONE_PHRASES if mem.is_milestone_day()
                        else phrases.DAYS_PHRASES)
                return pick(pool, name=name, n=days)

        # ~10% chance: claude.ai easter egg (always English)
        if random.random() < 0.1:
            return pick(phrases.CLAUDE_AI_PHRASES, name=name)

        # ~25% chance: book phrase if Claudy has a book today
        if self.has_book and random.random() < 0.25:
            return pick(phrases.BOOK_IDLE_PHRASES)

        return pick(phrases.IDLE_PHRASES)

    def _update_idle(self, dt):
        self.state_timer += dt

        self.idle_phrase_timer += dt
        if self.idle_phrase_timer >= self.idle_phrase_cooldown:
            self.idle_phrase_timer = 0.0
            self.idle_phrase_cooldown = self._next_phrase_cooldown()
            self._say(self._pick_idle_phrase())

        if self.state_timer > self.next_state_change and not self.gift_waiting:
            self._pick_next_activity()

    def _update_walking(self, dt):
        dx = self.target_x - self.x
        if abs(dx) < 2:
            self._enter_idle()
            return

        direction = 1 if dx > 0 else -1
        self.facing_right = direction > 0
        self.x += direction * min(abs(dx), WALK_SPEED * dt)

        self.walk_frame_timer += dt
        if self.walk_frame_timer >= WALK_FRAME_MS:
            self.walk_frame_timer -= WALK_FRAME_MS
            self.walk_frame_index = 1 - self.walk_frame_index

    def _pick_next_activity(self):
        weights = {name: w for name, w in schedule.get_weights().items()
                   if name in ("idle", "walking") or name in ACTIVITIES}
        if not weights:
            self._enter_idle()
            return

        # Skip recent activities. Idle/walking are never recent, so they stay
        # available as rest fallbacks. If filtering empties the pool (e.g.
        # deep_sleep has only "sleeping" and it just ran), don't filter.
        fresh = {n: w for n, w in weights.items()
                 if n not in self.recent_activities}
        if fresh:
            weights = fresh

        chosen = random.choices(list(weights), weights=list(weights.values()))[0]
        if chosen == "idle":
            self._enter_idle()
        elif chosen == "walking":
            self._start_walking()
        else:
            self._start_activity(chosen)

    def _enter_idle(self, woke_up=False):
        self._stop_current()
        self.state = "idle"
        self.state_timer = 0.0
        self.next_state_change = random.uniform(*IDLE_MS)
        if woke_up and Memory.shared().is_attached():
            name = Settings.shared().user_name
            self._say(pick(phrases.WAKE_PHRASES, name=name))

    def _start_walking(self):
        self._stop_current()
        self.state = "walking"
        self.state_timer = 0.0
        self.target_x = random.uniform(self.walk_min_x, self.walk_max_x)
        self.walk_frame_index = 0
        self.walk_frame_timer = 0.0
        self.facing_right = self.target_x > self.x

    def _stop_current(self):
        """Wind down the current activity or reaction before switching."""
        if self.friend_visible:
            # Interrupted mid-visit: the friend leaves in a puff
            self._friend_leaves()
        self.phases = []
        self.reaction = None
        self.hop = None
        self.wander_direction = 0
        self.bounce = None

    # ---- Reactions ----

    def _update_reaction(self, dt):
        self.state_timer += dt
        if self.reaction.hearts:
            self.particle_timer += dt
            if self.particle_timer > REACTION_HEART_INTERVAL_MS:
                self.particle_timer = 0.0
                self._burst("heart", 1)
        if self.state_timer > self.reaction.duration_ms:
            self._enter_idle()

    # ---- Activities ----

    def _start_activity(self, name):
        self.recent_activities.append(name)
        if len(self.recent_activities) > RECENT_ACTIVITY_BLOCK:
            self.recent_activities.pop(0)

        phases = list(ACTIVITIES[name])
        user_name = Settings.shared().user_name

        if name == "sleeping" and Memory.shared().is_attached():
            self._say(pick(phrases.SLEEP_PHRASES, name=user_name))

        if name == "campfire" and self.has_marshmallow:
            # Roast the user's marshmallow with special phrases
            self.has_marshmallow = False
            phases[3] = replace(phases[3], message=pick_personal(
                phrases.CAMPFIRE_MARSHMALLOW_ROAST_PHRASES,
                phrases.CAMPFIRE_MARSHMALLOW_ROAST_PHRASES_NAMELESS, user_name))
            phases[4] = replace(phases[4], message=pick_personal(
                phrases.CAMPFIRE_MARSHMALLOW_DONE_PHRASES,
                phrases.CAMPFIRE_MARSHMALLOW_DONE_PHRASES_NAMELESS, user_name))

        self._run_phases(name, phases)

    def _run_phases(self, state, phases):
        self.state = state
        self.state_timer = 0.0
        self.phases = phases
        self._enter_phase(0)

    def _enter_phase(self, index):
        self.phase_index = index
        phase = self.phases[index]
        self.phase_timer = 0.0
        self.phase_duration = phase.pick_duration()
        self.frame_index = 0
        self.frame_timer = 0.0
        self.particle_timer = 0.0
        # Per-phase motion ends with the phase; specials re-arm it
        self.friend_animation = None
        self.friend_walk_target = None
        self.wander_direction = 0
        self.hop = None

        if phase.message:
            self._say(t(phase.message))
        if phase.bounce:
            self.bounce = Bounce()
        if phase.shake:
            self.shake = Shake()
        if phase.special:
            getattr(self, "_special_" + phase.special)()

    def _update_activity(self, dt):
        phase = self.phases[self.phase_index]

        if len(phase.frames) > 1:
            self.frame_timer += dt
            if self.frame_timer >= phase.interval_ms:
                self.frame_timer -= phase.interval_ms
                self.frame_index = (self.frame_index + 1) % len(phase.frames)

        if phase.particle:
            self.particle_timer += dt
            if self.particle_timer >= phase.particle_interval_ms:
                self.particle_timer = 0.0
                self._burst(phase.particle, 1)

        self._update_friend(dt)

        self.phase_timer += dt
        if self.phase_timer >= self.phase_duration:
            self._advance_phase()

    def _advance_phase(self):
        index = self.phase_index + 1
        if index >= len(self.phases):
            # Sleeping only loops during deep_sleep hours; otherwise a nap
            if self.state == "sleeping" and schedule.get_period() == "deep_sleep":
                index = len(self.phases) - 1
            else:
                self._enter_idle(woke_up=(self.state == "sleeping"))
                return
        self._enter_phase(index)

    # ---- Motion ----

    def _update_motion(self, dt):
        if self.wander_direction:
            self._wander(dt)

        if self.hop:
            height, landed = self.hop.update(dt)
            self.y_offset = height
            if landed:
                self._turn_hop(-self.hop_direction)
            self.x += self.hop_direction * HOP_SPEED * dt
            if self.x < self.walk_min_x:
                self.x = self.walk_min_x
                self._turn_hop(1)
            elif self.x > self.walk_max_x:
                self.x = self.walk_max_x
                self._turn_hop(-1)
        elif self.fall:
            self.y_offset, done = self.fall.update(dt)
            if done:
                self.fall = None
        elif self.bounce:
            self.y_offset, done = self.bounce.update(dt)
            if done:
                self.bounce = None
        else:
            self.y_offset = 0.0

        if self.shake:
            self.shake_dx, done = self.shake.update(dt)
            if done:
                self.shake = None
        else:
            self.shake_dx = 0.0

    def _wander(self, dt):
        self.x += self.wander_direction * WANDER_SPEED * dt
        if self.x < self.walk_min_x:
            self.x = self.walk_min_x
            self.wander_direction = 1
        elif self.x > self.walk_max_x:
            self.x = self.walk_max_x
            self.wander_direction = -1
        self.facing_right = self.wander_direction > 0

    def _turn_hop(self, direction):
        self.hop_direction = direction
        self.facing_right = direction > 0

    def _update_blink(self, dt):
        if self.state not in ("idle", "walking"):
            self.is_blinking = False
            return
        self.blink_timer += dt
        if self.is_blinking:
            if self.blink_timer >= BLINK_MS:
                self.is_blinking = False
                self.blink_timer = 0.0
                self.next_blink = random.uniform(*BLINK_GAP_MS)
        elif self.blink_timer >= self.next_blink:
            self.is_blinking = True
            self.blink_timer = 0.0

    # ---- Friend ----

    def _update_friend(self, dt):
        if not self.friend_animation:
            return
        frames = FRIEND_ANIMATIONS[self.friend_animation]
        self.friend_frame_timer += dt
        if self.friend_frame_timer >= FRIEND_FRAME_MS:
            self.friend_frame_timer -= FRIEND_FRAME_MS
            self.friend_frame = 1 - self.friend_frame
            self.friend_sprite = frames[self.friend_frame]

        if self.friend_walk_target is not None:
            dx = self.friend_walk_target - self.x
            if abs(dx) > 2:
                direction = 1 if dx > 0 else -1
                self.facing_right = direction > 0
                self.x += direction * min(abs(dx), WALK_SPEED * dt)
            else:
                # Arrived — end the phase so the walk sprites stop
                self.phase_timer = self.phase_duration

    def _animate_friend(self, animation):
        self.friend_animation = animation
        self.friend_frame = 0
        self.friend_frame_timer = 0.0
        self.friend_sprite = FRIEND_ANIMATIONS[animation][0]

    def _friend_leaves(self):
        self.friend_visible = False
        self.friend_sprite = "idle"
        self.friend_animation = None
        self._burst("poof", 6)

    # ---- Phase specials (Phase.special names map to _special_<name>) ----

    def _special_cast_magic(self):
        result = random.choice(MAGIC_RESULTS)
        self._say(t(result["text"]))
        self._burst(result["particles"], 8)
        if (result["gift_emoji"] and random.random() < MAGIC_GIFT_CHANCE
                and Memory.shared().is_attached()):
            self._events.append(
                ("gift", {"type": "magic", "emoji": result["gift_emoji"]}))

    def _special_fish_reveal(self):
        catch = random.choice(CATCHES)
        self._say(f"{catch['emoji']} {t(catch['name'])}")
        self._burst(catch["particles"], 5)
        if (catch["good"] and random.random() < FISH_GIFT_CHANCE
                and Memory.shared().is_attached()):
            self._events.append(
                ("gift", {"type": "fish", "emoji": catch["emoji"]}))
        if not catch["good"]:
            phase = self.phases[self.phase_index]
            self.phases[self.phase_index] = replace(
                phase, frames=("fish_confused",))

    def _special_star_gaze(self):
        # Rarely name a star after the user — at most one per session
        mem = Memory.shared()
        if (random.random() < STAR_NAMING_CHANCE and mem.is_attached()
                and mem.count_session_gifts("star") == 0):
            name = Settings.shared().user_name
            self._say(pick_personal(phrases.STAR_NAMING_PHRASES,
                                    phrases.STAR_NAMING_PHRASES_NAMELESS, name))
            self._events.append(("gift_star", name))
            self._burst("star", 5)

    def _special_sand_result(self):
        if random.random() < SANDCASTLE_SUCCESS_CHANCE:
            self._say(t("какой красивый!"))
            self._burst("sparkle", 5)
        else:
            self._say(t("ой, рассыпался..."))
            self.shake = Shake()
            self._burst("poof", 4)

    def _special_shell_search(self):
        self.wander_direction = random.choice((-1, 1))
        self.facing_right = self.wander_direction > 0
        self._say(pick(phrases.SHELL_SEARCH_PHRASES))

    def _special_shell_gift_chance(self):
        if random.random() < SHELL_GIFT_CHANCE and Memory.shared().is_attached():
            self._events.append(("gift", {"type": "shell", "emoji": "🐚"}))

    def _special_play_jump(self):
        self.hop = Hop()
        self._turn_hop(random.choice((-1, 1)))

    def _special_summon_friend(self):
        self.friend_visible = True
        self.friend_sprite = "idle"
        self.facing_right = False  # face toward the friend
        self._burst("poof", 6)
        self._say(pick(phrases.FRIEND_PHRASES))
        # Plan the visit: 2-3 random together-activities, then goodbye
        chosen = random.sample(list(FRIEND_ACTIVITY_POOL), k=random.randint(2, 3))
        visit = [p for key in chosen for p in FRIEND_ACTIVITY_POOL[key]]
        self.phases = (self.phases[:self.phase_index + 1]
                       + visit + list(FRIEND_GOODBYE))

    def _special_friend_walk_start(self):
        self._animate_friend("walk")
        direction = random.choice((-1, 1))
        self.facing_right = direction > 0
        target = self.x + direction * random.uniform(80, 200)
        self.friend_walk_target = max(self.walk_min_x,
                                      min(self.walk_max_x, target))
        self._say(pick(phrases.FRIEND_WALK_PHRASES))

    def _special_friend_walk_stop(self):
        self.friend_sprite = "happy"
        self._say(pick(phrases.FRIEND_WALK_END_PHRASES))

    def _special_friend_play_bounce(self):
        self._animate_friend("play")
        self._say(pick(phrases.FRIEND_PLAY_PHRASES))
        self._burst("sparkle", 3)

    def _special_friend_sit(self):
        self.friend_sprite = "idle"
        self._say(pick(phrases.FRIEND_SIT_PHRASES))

    def _special_friend_chat(self):
        self.friend_sprite = "happy"
        self._say(pick(phrases.FRIEND_CHAT_PHRASES))

    def _special_friend_chat_reply(self):
        self.friend_sprite = "love"
        self._say(pick(phrases.FRIEND_CHAT_REPLY_PHRASES))
        self._burst("heart", 2)

    def _special_friend_bye(self):
        self.friend_sprite = "wave"
        self._say(t("пока-пока!"))

    def _special_friend_gone(self):
        self._friend_leaves()
        self._say(pick(phrases.FRIEND_AFTER))
