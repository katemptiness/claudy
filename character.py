"""Character state machine and phased animation engine."""

import random
from config import WINDOW_WIDTH, SPRITE_SIZE
from schedule import get_weights


class Phase:
    """A single phase within an activity sequence."""

    def __init__(self, frames, interval_ms=500, duration_ms=2000,
                 message=None, particle=None, particle_interval_ms=1000,
                 bounce=False, shake=False, special=None):
        self.frames = frames
        self.interval_ms = interval_ms
        self.duration_ms = duration_ms
        self.message = message
        self.particle = particle
        self.particle_interval_ms = particle_interval_ms
        self.bounce = bounce
        self.shake = shake
        self.special = special  # e.g. "cast_magic", "fish_reveal"


# Activity definitions: each is a list of Phases
ACTIVITIES = {
    "reading": [
        Phase(["read_a"], 500, 800, message="берёт книжку..."),
        Phase(["read_a", "read_b"], 600, 4000, message="читает...",
              particle="page", particle_interval_ms=2000),
        Phase(["read_react"], 200, 1200, message="о! интересно!",
              particle="exclaim", bounce=True),
        Phase(["read_a", "read_b"], 600, 3000, message="читает дальше..."),
        Phase(["idle"], 500, 1500, message="закрыл книгу"),
    ],
    "sleeping": [
        Phase(["sleep_transition"], 500, 1000),
        Phase(["sleep_a", "sleep_b"], 800, 15000,
              particle="zzz", particle_interval_ms=2000),
    ],
    "magic": [
        Phase(["magic_hold"], 500, 1000, message="достаёт палочку..."),
        Phase(["magic_raise"], 300, 1200, message="замахивается...", bounce=True),
        Phase(["magic_cast"], 150, 800, message="✨ ВЗМАХ!",
              shake=True, special="cast_magic"),
        Phase(["magic_done"], 500, 2500),
        Phase(["idle"], 500, 1000),
    ],
    "working": [
        Phase(["work_a"], 400, 800, message="открывает ноутбук..."),
        Phase(["work_a", "work_b"], 180, 3500, message="тук-тук-тук...",
              particle="code", particle_interval_ms=600),
        Phase(["work_think"], 500, 1500, message="хмм...",
              particle="question", particle_interval_ms=1200),
        Phase(["work_a", "work_b"], 150, 2500, message="ПИШЕТ КОД!!",
              particle="code", particle_interval_ms=300, shake=True),
        Phase(["magic_done"], 500, 1500, message="готово! ✨",
              particle="sparkle", particle_interval_ms=200),
        Phase(["idle"], 500, 1000),
    ],
    "fishing": [
        Phase(["fish_wait"], 500, 800, message="забрасывает удочку..."),
        Phase(["fish_wait", "fish_wait_b"], 800, 3500, message="ждёт...",
              particle="zzz", particle_interval_ms=1500),
        Phase(["fish_bite"], 120, 1000, message="❗ клюёт!!",
              particle="exclaim", particle_interval_ms=600, shake=True),
        Phase(["fish_pull", "fish_bite"], 150, 1200, message="тянет!!!",
              shake=True),
        Phase(["fish_happy"], 500, 2500, special="fish_reveal"),
        Phase(["idle"], 500, 1000),
    ],
    "playing": [
        Phase(["play_a", "play_b"], 200, 4000, message="прыгает!",
              particle="note", particle_interval_ms=500, bounce=True),
        Phase(["idle"], 500, 1000),
    ],
    "music": [
        Phase(["music_a", "music_b"], 400, 5000, message="♪♫♬",
              particle="note", particle_interval_ms=800),
        Phase(["idle"], 500, 1000),
    ],
    "painting": [
        Phase(["paint_a"], 500, 800, message="ставит мольберт..."),
        Phase(["paint_a", "paint_b"], 400, 3000, message="рисует..."),
        Phase(["paint_c"], 500, 1500, message="хмм... неплохо!"),
        Phase(["idle"], 500, 1000),
    ],
    "telescope": [
        Phase(["telescope_a"], 500, 1000, message="достаёт телескоп..."),
        Phase(["telescope_a", "telescope_b"], 600, 4000, message="космос...",
              particle="star", particle_interval_ms=1500),
        Phase(["idle"], 500, 1000),
    ],
    "meditating": [
        Phase(["meditate_a"], 500, 6000, message="ом...",
              particle="sparkle", particle_interval_ms=2000),
        Phase(["idle"], 500, 1000),
    ],
    "juggling": [
        Phase(["juggle_a", "juggle_b", "juggle_c"], 200, 4000,
              message="жонглирует!"),
        Phase(["idle"], 500, 1000),
    ],
}

# Random outcomes
CATCHES = [
    {"emoji": "🐟", "name": "рыбка!", "reaction": "happy", "particles": "sparkle"},
    {"emoji": "🐡", "name": "фугу!!", "reaction": "happy", "particles": "sparkle"},
    {"emoji": "👢", "name": "ботинок...", "reaction": "confused", "particles": "sweat"},
    {"emoji": "🌿", "name": "водоросли", "reaction": "confused", "particles": "sweat"},
    {"emoji": "💎", "name": "АЛМАЗ!!", "reaction": "love", "particles": "heart"},
    {"emoji": "📦", "name": "коробка?!", "reaction": "confused", "particles": "question"},
    {"emoji": "⭐", "name": "звезда!!!", "reaction": "love", "particles": "star"},
    {"emoji": "🧦", "name": "носок.", "reaction": "confused", "particles": "sweat"},
]

MAGIC_RESULTS = [
    {"text": "букет! 💐", "particles": "flower"},
    {"text": "радуга! 🌈", "particles": "rainbow"},
    {"text": "звездопад! ⭐", "particles": "star"},
    {"text": "бабочка! 🦋", "particles": "butterfly"},
    {"text": "пуф! 💨", "particles": "poof"},
]


class Character:
    """The crab's brain — state machine + animation engine."""

    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.x = screen_width / 2  # crab center x in screen coords
        self.y_offset = 0  # vertical offset from base (for bounce)

        # State
        self.state = "idle"  # "idle", "walking", or an activity name
        self.state_timer = 0.0
        self.next_state_change = random.uniform(8000, 20000)

        # Walking
        self.target_x = self.x
        self.walk_speed = 0.04  # px/ms
        self.facing_right = True

        # Sprite frame cycling
        self.frame_index = 0
        self.frame_timer = 0.0
        self.walk_frame_index = 0
        self.walk_frame_timer = 0.0

        # Phased activity
        self.phase_index = 0
        self.phase_timer = 0.0
        self.particle_timer = 0.0
        self.current_message = None

        # Blink
        self.is_blinking = False
        self.blink_timer = 0.0
        self.next_blink = random.uniform(2000, 6000)

        # Animation effects
        self.bounce_phase = 0.0
        self.is_bouncing = False
        self.is_shaking = False
        self.shake_timer = 0.0

        # Reaction state
        self.reaction_duration = 0

        # Events emitted this tick
        self.events = []

    def update(self, dt):
        """Advance the state machine by dt milliseconds.
        Returns a dict of what changed."""
        self.events = []

        self._update_blink(dt)

        if self.state == "idle":
            self._update_idle(dt)
        elif self.state == "walking":
            self._update_walking(dt)
        elif self.state.startswith("reaction_"):
            self._update_reaction(dt)
        elif self.state == "dragging":
            pass  # position controlled externally
        else:
            self._update_activity(dt)

        self._update_effects(dt)

        return {
            "sprite": self._get_sprite_name(),
            "x": self.x,
            "y_offset": self.y_offset,
            "facing_right": self.facing_right,
            "events": self.events,
            "message": self.current_message,
        }

    def _update_idle(self, dt):
        self.state_timer += dt
        if self.state_timer > self.next_state_change:
            self._pick_next_activity()

    def _update_walking(self, dt):
        dx = self.target_x - self.x
        if abs(dx) < 2:
            self._enter_idle()
            return

        direction = 1 if dx > 0 else -1
        self.facing_right = direction > 0
        step = min(abs(dx), self.walk_speed * dt)
        self.x += direction * step

        # Alternate walk frames
        self.walk_frame_timer += dt
        if self.walk_frame_timer >= 200:
            self.walk_frame_timer = 0
            self.walk_frame_index = 1 - self.walk_frame_index

    def _update_activity(self, dt):
        activity = ACTIVITIES.get(self.state)
        if not activity:
            self._enter_idle()
            return

        phase = activity[self.phase_index]

        # Advance frame within phase
        self.frame_timer += dt
        if self.frame_timer >= phase.interval_ms and len(phase.frames) > 1:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(phase.frames)

        # Spawn particles
        if phase.particle:
            self.particle_timer += dt
            if self.particle_timer >= phase.particle_interval_ms:
                self.particle_timer = 0
                self.events.append(("particle", phase.particle))

        # Check if phase is done
        self.phase_timer += dt
        if self.phase_timer >= phase.duration_ms:
            self._advance_phase()

    def _advance_phase(self):
        activity = ACTIVITIES.get(self.state)
        if not activity:
            self._enter_idle()
            return

        self.phase_index += 1

        # Special case: sleeping loops its last phase during sleep hours
        if self.state == "sleeping" and self.phase_index >= len(activity):
            self.phase_index = len(activity) - 1  # stay on sleep loop

        if self.phase_index >= len(activity):
            self._enter_idle()
            return

        phase = activity[self.phase_index]
        self.phase_timer = 0
        self.frame_timer = 0
        self.frame_index = 0
        self.particle_timer = 0

        # Set message
        if phase.message:
            self.current_message = phase.message
            self.events.append(("message", phase.message))

        # Trigger effects
        if phase.bounce:
            self.is_bouncing = True
            self.bounce_phase = 0
        if phase.shake:
            self.is_shaking = True
            self.shake_timer = 0

        # Handle specials
        if phase.special == "cast_magic":
            result = random.choice(MAGIC_RESULTS)
            self.current_message = result["text"]
            self.events.append(("message", result["text"]))
            for _ in range(8):
                self.events.append(("particle", result["particles"]))

        elif phase.special == "fish_reveal":
            catch = random.choice(CATCHES)
            msg = f"{catch['emoji']} {catch['name']}"
            self.current_message = msg
            self.events.append(("message", msg))
            for _ in range(5):
                self.events.append(("particle", catch["particles"]))
            # Set reaction sprite
            if catch["reaction"] == "confused":
                # Override phase frames to show confused face
                activity[self.phase_index] = Phase(
                    ["fish_confused"], 500, 2500)

    def _pick_next_activity(self):
        weights = get_weights()

        # Filter to activities we actually have sprites for.
        # For now, only idle/walking + activities defined in ACTIVITIES.
        available = {}
        for name, weight in weights.items():
            if name in ("idle", "walking") or name in ACTIVITIES:
                available[name] = weight

        if not available:
            self._enter_idle()
            return

        names = list(available.keys())
        w = list(available.values())
        chosen = random.choices(names, weights=w, k=1)[0]

        if chosen == "idle":
            self._enter_idle()
        elif chosen == "walking":
            self._start_walking()
        else:
            self._start_activity(chosen)

    def _enter_idle(self):
        self.state = "idle"
        self.state_timer = 0
        self.next_state_change = random.uniform(8000, 20000)
        self.current_message = None

    def _start_walking(self):
        self.state = "walking"
        self.state_timer = 0
        margin = WINDOW_WIDTH
        self.target_x = random.uniform(margin, self.screen_width - margin)
        self.walk_frame_index = 0
        self.walk_frame_timer = 0
        dx = self.target_x - self.x
        self.facing_right = dx > 0

    def _start_activity(self, name):
        self.state = name
        self.phase_index = 0
        self.phase_timer = 0
        self.frame_timer = 0
        self.frame_index = 0
        self.particle_timer = 0
        self.current_message = None

        phase = ACTIVITIES[name][0]
        if phase.message:
            self.current_message = phase.message
            self.events.append(("message", phase.message))
        if phase.bounce:
            self.is_bouncing = True
            self.bounce_phase = 0
        if phase.shake:
            self.is_shaking = True
            self.shake_timer = 0

    def _update_blink(self, dt):
        # Only blink during idle or walking
        if self.state not in ("idle", "walking"):
            self.is_blinking = False
            return

        if self.is_blinking:
            self.blink_timer += dt
            if self.blink_timer >= 150:
                self.is_blinking = False
                self.blink_timer = 0
                self.next_blink = random.uniform(2000, 6000)
        else:
            self.blink_timer += dt
            if self.blink_timer >= self.next_blink:
                self.is_blinking = True
                self.blink_timer = 0

    def _update_effects(self, dt):
        import math

        # Bounce
        if self.is_bouncing:
            self.bounce_phase += dt * 0.012
            self.y_offset = abs(math.sin(self.bounce_phase)) * 10
            if self.bounce_phase > math.pi * 3:
                self.is_bouncing = False
                self.y_offset = 0
        else:
            self.y_offset = 0

        # Shake
        if self.is_shaking:
            self.shake_timer += dt
            if self.shake_timer > 500:
                self.is_shaking = False
            # shake offset is applied in the app via random jitter

    def _get_sprite_name(self):
        if self.is_blinking and self.state in ("idle", "walking"):
            return "blink"

        if self.state == "idle":
            return "idle"

        if self.state == "walking":
            return "walk_a" if self.walk_frame_index == 0 else "walk_b"

        # Reactions
        if self.state == "reaction_happy":
            return "happy"
        if self.state == "reaction_happy_love":
            # Show happy first, then love sprite in second half
            if self.state_timer < self.reaction_duration / 2:
                return "happy"
            return "love"
        if self.state == "reaction_wave":
            return "wave"
        if self.state == "reaction_surprise":
            return "surprise"
        if self.state == "dragging":
            return "surprise"

        # Activity — get current phase's current frame
        activity = ACTIVITIES.get(self.state)
        if activity and self.phase_index < len(activity):
            phase = activity[self.phase_index]
            frame_name = phase.frames[self.frame_index % len(phase.frames)]
            return frame_name

        return "idle"

    def interrupt(self, reaction):
        """Interrupt current activity for a reaction (click, hover, etc.)."""
        if reaction == "happy":
            self.state = "reaction_happy"
            self.state_timer = 0
            self.reaction_duration = 2000
            self.is_bouncing = True
            self.bounce_phase = 0
            self.current_message = random.choice(
                ["привет! :3", "о!", "рада тебя видеть", ":3"]
            )
            self.events.append(("message", self.current_message))
            for _ in range(4):
                self.events.append(("particle", "sparkle"))

        elif reaction == "happy_love":
            # Combined: happy bounce + sparkles, then love hearts
            self.state = "reaction_happy_love"
            self.state_timer = 0
            self.reaction_duration = 3000
            self.is_bouncing = True
            self.bounce_phase = 0
            self.current_message = random.choice(
                ["привет! :3", "о!", "рада тебя видеть", ":3", "♥"]
            )
            self.events.append(("message", self.current_message))
            for _ in range(4):
                self.events.append(("particle", "sparkle"))
            for _ in range(3):
                self.events.append(("particle", "heart"))

        elif reaction == "wave":
            self.state = "reaction_wave"
            self.state_timer = 0
            self.reaction_duration = 1500
            self.current_message = random.choice(["хм?", "*машет*"])
            self.events.append(("message", self.current_message))

        elif reaction == "surprise":
            self.state = "reaction_surprise"
            self.state_timer = 0
            self.reaction_duration = 1000
            self.events.append(("particle", "exclaim"))

        # Dragging is handled externally — just track state
        elif reaction == "dragging":
            self.state = "dragging"
            self.state_timer = 0

    def _update_reaction(self, dt):
        """Update reaction states (happy, love, wave, surprise)."""
        self.state_timer += dt
        if self.state_timer > self.reaction_duration:
            self._enter_idle()

        # Hearts during love/happy_love reactions
        if self.state in ("reaction_love", "reaction_happy_love"):
            self.particle_timer += dt
            if self.particle_timer > 400:
                self.particle_timer = 0
                self.events.append(("particle", "heart"))
