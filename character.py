"""Character state machine and phased animation engine."""

import random
import time as _time
from config import WINDOW_WIDTH, SPRITE_SIZE
from schedule import get_weights
from phrases import t, format_phrase



class Phase:
    """A single phase within an activity sequence."""

    def __init__(self, frames, interval_ms=500, duration_ms=2000,
                 duration_max_ms=None,
                 message=None, particle=None, particle_interval_ms=1000,
                 bounce=False, shake=False, special=None):
        self.frames = frames
        self.interval_ms = interval_ms
        self.duration_ms = duration_ms
        self.duration_max_ms = duration_max_ms  # if set, duration is randomized
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
        Phase(["read_a", "read_b"], 600, 60000, duration_max_ms=120000,
              message="читает...", particle="page", particle_interval_ms=3000),
        Phase(["read_react"], 200, 1200, message="о! интересно!",
              particle="exclaim", bounce=True),
        Phase(["read_a", "read_b"], 600, 60000, duration_max_ms=120000,
              message="читает дальше...", particle="page", particle_interval_ms=3000),
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
        Phase(["work_a", "work_b"], 180, 60000, duration_max_ms=100000,
              message="тук-тук-тук...", particle="code", particle_interval_ms=1500),
        Phase(["work_think"], 500, 5000, duration_max_ms=15000,
              message="хмм...", particle="question", particle_interval_ms=2000),
        Phase(["work_a", "work_b"], 150, 60000, duration_max_ms=100000,
              message="ПИШЕТ КОД!!", particle="code", particle_interval_ms=800,
              shake=True),
        Phase(["magic_done"], 500, 3000, message="готово! ✨",
              particle="sparkle", particle_interval_ms=400),
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
              particle="note", particle_interval_ms=500, special="play_jump"),
        Phase(["idle"], 500, 1000),
    ],
    "music": [
        Phase(["music_a", "music_b"], 400, 5000, message="♪♫♬",
              particle="note", particle_interval_ms=800),
        Phase(["idle"], 500, 1000),
    ],
    "painting": [
        Phase(["paint_a"], 500, 1500, message="ставит мольберт..."),
        Phase(["paint_a", "paint_b"], 400, 20000, duration_max_ms=30000,
              message="рисует..."),
        Phase(["paint_c"], 500, 2500, message="хмм... неплохо!"),
        Phase(["idle"], 500, 1000),
    ],
    "telescope": [
        Phase(["telescope_a"], 500, 1000, message="достаёт телескоп..."),
        Phase(["telescope_a", "telescope_b"], 600, 4000, message="космос...",
              particle="star", particle_interval_ms=1500),
        Phase(["idle"], 500, 1000, special="star_gaze"),
    ],
    "meditating": [
        Phase(["meditate_a"], 500, 120000, duration_max_ms=300000,
              message="ом...", particle="sparkle", particle_interval_ms=3000),
        Phase(["idle"], 500, 1000),
    ],
    "juggling": [
        Phase(["juggle_a", "juggle_b", "juggle_c"], 200, 4000,
              message="жонглирует!"),
        Phase(["idle"], 500, 1000),
    ],
    "summoning": [
        Phase(["magic_hold"], 500, 1000, message="достаёт палочку..."),
        Phase(["magic_raise"], 300, 1200, message="кого бы призвать...",
              bounce=True),
        Phase(["magic_cast"], 150, 800, message="✨ ПРИЗЫВ!",
              shake=True, special="summon_friend"),
        # Phases 3+ are dynamically rebuilt by summon_friend special.
        # Defaults below are fallbacks only.
        Phase(["happy"], 500, 3000, special="friend_chat_varied"),
        Phase(["happy"], 500, 2500, special="friend_bye"),
        Phase(["idle"], 500, 2000, special="friend_gone"),
    ],
    "campfire": [
        Phase(["campfire_a", "campfire_b"], 600, 8000,
              message="разжёг костёр!", particle="flame",
              particle_interval_ms=1000),
        Phase(["campfire_a", "campfire_b"], 600, 20000, duration_max_ms=40000,
              message="тепло...", particle="flame", particle_interval_ms=2500),
        Phase(["campfire_a", "campfire_b"], 600, 5000,
              message="люблю смотреть на огонь...", particle="flame",
              particle_interval_ms=2500),
        Phase(["campfire_roast"], 500, 5000, message="жарит зефирку!"),
        Phase(["campfire_done"], 500, 3000, message="вкусно! :3",
              particle="heart", particle_interval_ms=800, bounce=True),
        Phase(["idle"], 500, 1000),
    ],
    "sandcastle": [
        Phase(["sand_a"], 500, 2000, message="строит замок..."),
        Phase(["sand_a", "sand_b"], 500, 4000, duration_max_ms=6000,
              message="лепит..."),
        Phase(["sand_c"], 500, 2500, special="sand_result"),
        Phase(["idle"], 500, 1000),
    ],
    "shell_collecting": [
        Phase(["walk_a", "walk_b"], 250, 4000, duration_max_ms=6000,
              special="shell_search"),
        Phase(["shell_look"], 500, 2000),
        Phase(["shell_find"], 300, 1500, message="о! нашёл!",
              particle="exclaim", bounce=True),
        Phase(["shell_pick"], 500, 1500, message="подбирает..."),
        Phase(["shell_admire"], 500, 3000, message="какая красивая ракушка!",
              particle="sparkle", particle_interval_ms=600,
              special="shell_gift_chance"),
        Phase(["idle"], 500, 1000),
    ],
    "candle": [
        Phase(["lantern_light"], 500, 2000, message="зажигает свечку..."),
        Phase(["lantern_a", "lantern_b"], 800, 15000, duration_max_ms=30000,
              message="огонёк мерцает...", particle="sparkle",
              particle_interval_ms=5000),
        Phase(["lantern_a", "lantern_b"], 800, 15000, duration_max_ms=40000,
              message="так спокойно...", particle="sparkle",
              particle_interval_ms=5000),
        Phase(["lantern_a", "lantern_b"], 800, 5000,
              message="можно так сидеть вечно..."),
        Phase(["idle"], 500, 1000),
    ],
}

SHELL_SEARCH_PHRASES = [
    "ищет ракушки...",
    "где-то тут была...",
    "красивая должна быть рядом...",
    "тут столько ракушек!",
]

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


FRIEND_PHRASES = [
    "о! привет, друг!", "как дела?", "давно не виделись!",
    "что нового?", "привет-привет!",
]

FRIEND_TOGETHER = [
    "*обнимаются*", "вместе веселее!", "ты мой лучший друг!",
    "расскажи что-нибудь!", "а помнишь?...",
]

FRIEND_AFTER = [
    "было весело!", "приходи ещё!", "скучаю уже...",
    "до встречи!", "хороший был день :3",
]

FRIEND_WALK_PHRASES = [
    "погуляем!", "пойдём!", "куда пойдём?",
    "прогулка!", "вперёд!",
]

FRIEND_WALK_END_PHRASES = [
    "хорошая прогулка!", "устал :3", "вернулись!",
]

FRIEND_PLAY_PHRASES = [
    "играем!", "догоняй!", "весело!",
    "ещё! ещё!", "прыг-прыг!",
]

FRIEND_SIT_PHRASES = [
    "тихо тут...", "красиво...", "просто посидим",
    "звёзды...", "*молчит вместе*",
]

FRIEND_CHAT_PHRASES = [
    "а ты знал?...", "слушай!", "расскажу историю!",
    "угадай что!", "а помнишь тот раз?",
]

FRIEND_CHAT_REPLY_PHRASES = [
    "ха-ха! да!", "правда?!", "это здорово!",
    "расскажи ещё!", "ого!",
]

# Pool of together-activities for randomized summoning hangouts.
# Each entry is a callable returning fresh Phase lists.
FRIEND_ACTIVITY_POOL = {
    "walk": lambda: [
        Phase(["walk_a", "walk_b"], 200, 6000, duration_max_ms=10000,
              special="friend_walk_start"),
        Phase(["idle"], 500, 2000, special="friend_walk_stop"),
    ],
    "play": lambda: [
        Phase(["play_a", "play_b"], 200, 4000, bounce=True,
              special="friend_play_bounce",
              particle="note", particle_interval_ms=600),
    ],
    "sit": lambda: [
        Phase(["idle"], 500, 5000, duration_max_ms=8000,
              special="friend_sit",
              particle="star", particle_interval_ms=2500),
    ],
    "chat": lambda: [
        Phase(["happy"], 500, 3000, special="friend_chat_varied"),
        Phase(["idle"], 500, 2000, special="friend_chat_reply"),
    ],
}

IDLE_PHRASES = [
    "скучно...", "хм...", ":3", "думаю о рыбке...",
    "тут красиво", "*зевает*", "...", "когда же рыбалка?",
    "а что если...", "мне нравится тут", "интересно...",
    "ля-ля-ля", "*смотрит вдаль*", "о чём бы подумать...",
    "а облака красивые...", "*тихо напевает*", "где мой телескоп?",
    "надо бы порыбачить...", "*считает звёзды*", "хочу алмаз...",
    "*потягивается*", "какой хороший день", "моя клешня!",
    "а что там в интернете?",
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
        self.current_phase_duration = 0.0
        self.current_message = None

        # Idle phrases
        self.idle_phrase_timer = 0.0
        self.idle_phrase_cooldown = 0.0
        self._update_phrase_cooldown()

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

        # Play jump (side-to-side arcs)
        self.is_playing_jump = False
        self.play_jump_timer = 0.0
        self.play_jump_direction = 1

        # Shell search (slow wandering)
        self.is_shell_searching = False
        self.shell_search_direction = 1

        # Gift pause — stops activity transitions while waiting for user
        self.gift_waiting = False

        # User gifts to Claudy (session-only)
        self.has_marshmallow = False
        self.has_toy = False
        self.last_gift_received_time = 0

        # Friend summoning
        self.friend_visible = False
        self.friend_sprite = "idle"
        self.friend_walking = False
        self.friend_walk_timer = 0.0
        self.friend_walk_frame = 0
        self.friend_playing = False

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
            "friend_visible": self.friend_visible,
            "friend_sprite": self.friend_sprite,
            "show_toy": self.has_toy and self.state == "sleeping",
        }

    def _update_phrase_cooldown(self):
        from settings import Settings, SPEECH_COOLDOWNS
        interval = Settings.shared().speech_interval
        lo, hi = SPEECH_COOLDOWNS.get(interval, (45000, 75000))
        self.idle_phrase_cooldown = random.uniform(lo, hi)

    def _pick_idle_phrase(self):
        """Pick an idle phrase — may be days-together or claude.ai easter egg."""
        from memory import Memory
        from settings import Settings
        from phrases import (DAYS_PHRASES, DAYS_MILESTONE_PHRASES,
                             CLAUDE_AI_PHRASES)
        name = Settings.shared().user_name
        mem = Memory.shared()

        # ~20% chance: days-together phrase (once per day)
        if not mem.days_phrase_shown_today() and random.random() < 0.2:
            days = mem.get_total_days()
            if days >= 2:
                mem.mark_days_phrase_shown()
                if mem.is_milestone_day():
                    pool = DAYS_MILESTONE_PHRASES
                else:
                    pool = DAYS_PHRASES
                return format_phrase(random.choice(pool), name=name, n=days)

        # ~10% chance: claude.ai easter egg (always English)
        if random.random() < 0.1:
            phrase = random.choice(CLAUDE_AI_PHRASES)
            if name:
                return phrase.replace("{name}", name)
            return phrase.replace("{name} ", "").replace(", {name}", "").replace("{name}", "")

        # Normal idle phrase
        return t(random.choice(IDLE_PHRASES))

    def _update_idle(self, dt):
        self.state_timer += dt

        # Random idle phrases
        self.idle_phrase_timer += dt
        if self.idle_phrase_timer >= self.idle_phrase_cooldown:
            self.idle_phrase_timer = 0
            self._update_phrase_cooldown()
            phrase = self._pick_idle_phrase()
            self.current_message = phrase
            self.events.append(("message", phrase))

        if self.state_timer > self.next_state_change and not self.gift_waiting:
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

        # Friend walk animation and movement
        if self.friend_walking:
            self.friend_walk_timer += dt
            if self.friend_walk_timer >= 200:
                self.friend_walk_timer = 0
                self.friend_walk_frame = 1 - self.friend_walk_frame
                self.friend_sprite = ["walk_a", "walk_b"][self.friend_walk_frame]
            if hasattr(self, '_friend_walk_target'):
                dx = self._friend_walk_target - self.x
                if abs(dx) > 2:
                    direction = 1 if dx > 0 else -1
                    self.facing_right = direction > 0
                    step = min(abs(dx), self.walk_speed * dt)
                    self.x += direction * step
                else:
                    # Arrived — skip to next phase so walk sprites stop
                    self.phase_timer = self.current_phase_duration

        # Friend play animation (cycle play_a/play_b)
        if self.friend_playing:
            self.friend_walk_timer += dt
            if self.friend_walk_timer >= 200:
                self.friend_walk_timer = 0
                self.friend_walk_frame = 1 - self.friend_walk_frame
                self.friend_sprite = ["play_a", "play_b"][self.friend_walk_frame]

        # Check if phase is done
        self.phase_timer += dt
        if self.phase_timer >= self.current_phase_duration:
            self._advance_phase()

    def _advance_phase(self):
        activity = ACTIVITIES.get(self.state)
        if not activity:
            self._enter_idle()
            return

        self.phase_index += 1

        # Sleeping only loops during deep_sleep hours; otherwise it's a short nap
        if self.state == "sleeping" and self.phase_index >= len(activity):
            from schedule import get_period
            if get_period() == "deep_sleep":
                self.phase_index = len(activity) - 1  # stay on sleep loop

        if self.phase_index >= len(activity):
            self._enter_idle(from_sleeping=(self.state == "sleeping"))
            return

        phase = activity[self.phase_index]
        self.phase_timer = 0
        self.frame_timer = 0
        self.frame_index = 0
        # Clear animation flags — specials will re-set if needed
        self.friend_walking = False
        self.friend_playing = False
        self.is_shell_searching = False
        self.particle_timer = 0
        if phase.duration_max_ms:
            self.current_phase_duration = random.uniform(
                phase.duration_ms, phase.duration_max_ms)
        else:
            self.current_phase_duration = phase.duration_ms

        # Set message
        if phase.message:
            msg = t(phase.message)
            self.current_message = msg
            self.events.append(("message", msg))

        # Trigger effects
        if phase.bounce:
            self.is_bouncing = True
            self.bounce_phase = 0
        if phase.shake:
            self.is_shaking = True
            self.shake_timer = 0

        # Handle specials
        from memory import Memory
        if phase.special == "cast_magic":
            result = random.choice(MAGIC_RESULTS)
            msg = t(result["text"])
            self.current_message = msg
            self.events.append(("message", msg))
            for _ in range(8):
                self.events.append(("particle", result["particles"]))
            # Gift chance (~20%) for non-poof results (attachment required)
            if (result["particles"] != "poof" and random.random() < 0.2
                    and Memory.shared().is_attached()):
                emoji_map = {"flower": "🌸", "butterfly": "🦋", "rainbow": "🌈",
                             "star": "⭐"}
                gift_emoji = emoji_map.get(result["particles"], "✨")
                self.events.append(("gift", {
                    "type": "magic", "emoji": gift_emoji}))

        elif phase.special == "fish_reveal":
            catch = random.choice(CATCHES)
            msg = f"{catch['emoji']} {t(catch['name'])}"
            self.current_message = msg
            self.events.append(("message", msg))
            for _ in range(5):
                self.events.append(("particle", catch["particles"]))
            # Gift chance (~30%) for good catches (attachment required)
            if (catch["reaction"] in ("happy", "love") and random.random() < 0.3
                    and Memory.shared().is_attached()):
                self.events.append(("gift", {
                    "type": "fish", "emoji": catch["emoji"]}))
            # Set reaction sprite (always preserve fish_reveal special for next run)
            if catch["reaction"] == "confused":
                activity[self.phase_index] = Phase(
                    ["fish_confused"], 500, 2500, special="fish_reveal")
            else:
                activity[self.phase_index] = Phase(
                    ["fish_happy"], 500, 2500, special="fish_reveal")

        elif phase.special == "star_gaze":
            # ~10% chance to name a star after the user (attachment required)
            if random.random() < 0.1 and Memory.shared().is_attached():
                from settings import Settings
                from phrases import STAR_NAMING_PHRASES, STAR_NAMING_PHRASES_NAMELESS
                name = Settings.shared().user_name
                if name:
                    msg = format_phrase(random.choice(STAR_NAMING_PHRASES), name=name)
                else:
                    msg = format_phrase(random.choice(STAR_NAMING_PHRASES_NAMELESS))
                self.current_message = msg
                self.events.append(("message", msg))
                self.events.append(("gift_star", name or ""))
                for _ in range(5):
                    self.events.append(("particle", "star"))

        elif phase.special == "sand_result":
            if random.random() < 0.7:  # 70% success
                msg = t("какой красивый!")
                self.current_message = msg
                self.events.append(("message", msg))
                for _ in range(5):
                    self.events.append(("particle", "sparkle"))
            else:  # 30% collapse
                msg = t("ой, рассыпался...")
                self.current_message = msg
                self.events.append(("message", msg))
                self.is_shaking = True
                self.shake_timer = 0
                for _ in range(4):
                    self.events.append(("particle", "poof"))

        elif phase.special == "shell_search":
            self.is_shell_searching = True
            self.shell_search_direction = 1 if random.random() > 0.5 else -1
            self.facing_right = self.shell_search_direction > 0
            msg = t(random.choice(SHELL_SEARCH_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))

        elif phase.special == "shell_gift_chance":
            # ~10% chance to gift the shell to the user (attachment required)
            if random.random() < 0.1 and Memory.shared().is_attached():
                self.events.append(("gift", {
                    "type": "shell", "emoji": "🐚"}))

        elif phase.special == "play_jump":
            self.is_playing_jump = True
            self.play_jump_timer = 0
            self.play_jump_direction = 1 if random.random() > 0.5 else -1
            self.facing_right = self.play_jump_direction > 0

        elif phase.special == "summon_friend":
            self.friend_visible = True
            self.friend_sprite = "idle"
            self.facing_right = False  # face toward friend
            for _ in range(6):
                self.events.append(("particle", "poof"))
            self.events.append(("friend_appear", None))
            # Greeting
            msg = t(random.choice(FRIEND_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))
            # Rebuild activity with random together-activities
            pool_keys = list(FRIEND_ACTIVITY_POOL.keys())
            chosen = random.sample(pool_keys, k=random.randint(2, 3))
            intro = ACTIVITIES["summoning"][:3]
            middle = []
            for key in chosen:
                middle.extend(FRIEND_ACTIVITY_POOL[key]())
            outro = [
                Phase(["happy"], 500, 2500, special="friend_bye"),
                Phase(["idle"], 500, 2000, special="friend_gone"),
            ]
            ACTIVITIES["summoning"] = intro + middle + outro

        elif phase.special == "friend_walk_start":
            self.friend_walking = True
            self.friend_walk_timer = 0.0
            self.friend_walk_frame = 0
            self.friend_sprite = "walk_a"
            margin = WINDOW_WIDTH
            walk_dist = random.uniform(80, 200)
            direction = 1 if random.random() > 0.5 else -1
            self.facing_right = direction > 0
            self._friend_walk_target = self.x + direction * walk_dist
            self._friend_walk_target = max(margin, min(
                self.screen_width - margin, self._friend_walk_target))
            msg = t(random.choice(FRIEND_WALK_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))

        elif phase.special == "friend_walk_stop":
            self.friend_walking = False
            self.friend_sprite = "happy"
            msg = t(random.choice(FRIEND_WALK_END_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))

        elif phase.special == "friend_play_bounce":
            self.friend_playing = True
            self.friend_walk_timer = 0.0
            self.friend_walk_frame = 0
            self.friend_sprite = "play_a"
            msg = t(random.choice(FRIEND_PLAY_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))
            for _ in range(3):
                self.events.append(("particle", "sparkle"))

        elif phase.special == "friend_sit":
            self.friend_sprite = "idle"
            msg = t(random.choice(FRIEND_SIT_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))

        elif phase.special == "friend_chat_varied":
            self.friend_sprite = "happy"
            msg = t(random.choice(FRIEND_CHAT_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))

        elif phase.special == "friend_chat_reply":
            self.friend_sprite = "love"
            msg = t(random.choice(FRIEND_CHAT_REPLY_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))
            for _ in range(2):
                self.events.append(("particle", "heart"))

        elif phase.special == "friend_bye":
            self.friend_sprite = "wave"
            self.friend_walking = False
            self.friend_playing = False
            msg = t("пока-пока!")
            self.current_message = msg
            self.events.append(("message", msg))

        elif phase.special == "friend_gone":
            self.friend_visible = False
            self.friend_sprite = "idle"
            self.friend_walking = False
            for _ in range(6):
                self.events.append(("particle", "poof"))
            self.events.append(("friend_leave", None))
            msg = t(random.choice(FRIEND_AFTER))
            self.current_message = msg
            self.events.append(("message", msg))

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

    def _enter_idle(self, from_sleeping=False):
        # Wake greeting when coming out of sleep
        if from_sleeping:
            from memory import Memory
            from settings import Settings
            from phrases import WAKE_PHRASES
            if Memory.shared().is_attached():
                n = Settings.shared().user_name
                msg = format_phrase(random.choice(WAKE_PHRASES), name=n)
                self.current_message = msg
                self.events.append(("message", msg))

        self.state = "idle"
        self.state_timer = 0
        self.next_state_change = random.uniform(8000, 20000)
        if not from_sleeping:
            self.current_message = None
        self.is_playing_jump = False
        self.friend_walking = False
        self.friend_playing = False

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

        # Sleep greeting when attached + toy integration
        if name == "sleeping":
            from memory import Memory
            from settings import Settings
            from phrases import SLEEP_PHRASES
            if Memory.shared().is_attached():
                n = Settings.shared().user_name
                msg = format_phrase(random.choice(SLEEP_PHRASES), name=n)
                self.current_message = msg
                self.events.append(("message", msg))

        # Campfire marshmallow integration
        if name == "campfire":
            activity = ACTIVITIES["campfire"]
            if self.has_marshmallow:
                from settings import Settings
                from phrases import (CAMPFIRE_MARSHMALLOW_ROAST_PHRASES,
                                     CAMPFIRE_MARSHMALLOW_ROAST_PHRASES_NAMELESS,
                                     CAMPFIRE_MARSHMALLOW_DONE_PHRASES,
                                     CAMPFIRE_MARSHMALLOW_DONE_PHRASES_NAMELESS)
                n = Settings.shared().user_name
                if n:
                    roast_msg = format_phrase(
                        random.choice(CAMPFIRE_MARSHMALLOW_ROAST_PHRASES), name=n)
                    done_msg = format_phrase(
                        random.choice(CAMPFIRE_MARSHMALLOW_DONE_PHRASES), name=n)
                else:
                    roast_msg = format_phrase(
                        random.choice(CAMPFIRE_MARSHMALLOW_ROAST_PHRASES_NAMELESS))
                    done_msg = format_phrase(
                        random.choice(CAMPFIRE_MARSHMALLOW_DONE_PHRASES_NAMELESS))
                activity[3] = Phase(
                    ["campfire_roast"], 500, 5000, message=roast_msg)
                activity[4] = Phase(
                    ["campfire_done"], 500, 3000, message=done_msg,
                    particle="heart", particle_interval_ms=800, bounce=True)
            else:
                # Restore defaults (avoid stale mutation)
                activity[3] = Phase(
                    ["campfire_roast"], 500, 5000, message="жарит зефирку!")
                activity[4] = Phase(
                    ["campfire_done"], 500, 3000, message="вкусно! :3",
                    particle="heart", particle_interval_ms=800, bounce=True)

        phase = ACTIVITIES[name][0]
        if phase.duration_max_ms:
            self.current_phase_duration = random.uniform(
                phase.duration_ms, phase.duration_max_ms)
        else:
            self.current_phase_duration = phase.duration_ms
        if phase.message:
            msg = t(phase.message)
            self.current_message = msg
            self.events.append(("message", msg))
        if phase.bounce:
            self.is_bouncing = True
            self.bounce_phase = 0
        if phase.shake:
            self.is_shaking = True
            self.shake_timer = 0
        if phase.special == "play_jump":
            self.is_playing_jump = True
            self.play_jump_timer = 0
            self.play_jump_direction = 1 if random.random() > 0.5 else -1
            self.facing_right = self.play_jump_direction > 0
        elif phase.special == "shell_search":
            self.is_shell_searching = True
            self.shell_search_direction = 1 if random.random() > 0.5 else -1
            self.facing_right = self.shell_search_direction > 0
            msg = t(random.choice(SHELL_SEARCH_PHRASES))
            self.current_message = msg
            self.events.append(("message", msg))

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

        # Shell search (slow wandering side to side)
        if self.is_shell_searching:
            self.x += self.shell_search_direction * 0.03 * dt
            margin = WINDOW_WIDTH
            if self.x < margin:
                self.x = margin
                self.shell_search_direction = 1
                self.facing_right = True
            elif self.x > self.screen_width - margin:
                self.x = self.screen_width - margin
                self.shell_search_direction = -1
                self.facing_right = False

        # Play jump (parabolic arcs side to side)
        elif self.is_playing_jump:
            self.play_jump_timer += dt
            jump_duration = 600
            t = min(self.play_jump_timer / jump_duration, 1.0)
            self.y_offset = 4 * 12 * t * (1 - t)
            self.x += self.play_jump_direction * 0.05 * dt
            if t >= 1.0:
                self.play_jump_timer = 0
                self.play_jump_direction *= -1
                self.facing_right = self.play_jump_direction > 0
            margin = WINDOW_WIDTH
            if self.x < margin:
                self.x = margin
                self.play_jump_direction = 1
            elif self.x > self.screen_width - margin:
                self.x = self.screen_width - margin
                self.play_jump_direction = -1
        # Bounce
        elif self.is_bouncing:
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
        if self.state == "reaction_gift_received":
            if self.state_timer < 500:
                return "surprise"
            elif self.state_timer < 1500:
                return "happy"
            return "love"
        if self.state == "dragging":
            return "surprise"

        # Activity — get current phase's current frame
        activity = ACTIVITIES.get(self.state)
        if activity and self.phase_index < len(activity):
            phase = activity[self.phase_index]
            frame_name = phase.frames[self.frame_index % len(phase.frames)]
            return frame_name

        return "idle"

    def can_receive_gift(self):
        """Check if cooldown has elapsed for receiving gifts."""
        from settings import Settings, GIFT_COOLDOWNS
        cooldown = GIFT_COOLDOWNS.get(Settings.shared().gift_cooldown, 600)
        return (_time.time() - self.last_gift_received_time) >= cooldown

    def receive_gift(self, gift_type):
        """Handle user giving a gift to Claudy. Returns True if accepted."""
        if not self.can_receive_gift():
            return False

        self.last_gift_received_time = _time.time()

        # Set persistent session flags
        if gift_type == "marshmallow":
            self.has_marshmallow = True
        elif gift_type == "toy":
            self.has_toy = True

        # Count as 2 clicks toward attachment
        from memory import Memory
        Memory.shared().record_click()
        Memory.shared().record_click()

        # Pick gift-specific phrase
        from phrases import GIFT_RECEIVE_PHRASES
        phrases = GIFT_RECEIVE_PHRASES.get(gift_type, ["спасибо! :3"])
        phrase = t(random.choice(phrases))

        # Enter gift-received reaction
        self.state = "reaction_gift_received"
        self.state_timer = 0
        self.reaction_duration = 3000
        self.is_bouncing = True
        self.bounce_phase = 0
        self.current_message = phrase
        self.events.append(("message", phrase))
        for _ in range(5):
            self.events.append(("particle", "sparkle"))
        for _ in range(3):
            self.events.append(("particle", "heart"))
        if gift_type == "song":
            for _ in range(4):
                self.events.append(("particle", "note"))
        return True

    def trigger_activity(self, name):
        """Start a specific activity (e.g. triggered by user opening an app)."""
        if name not in ACTIVITIES:
            return
        # Only interrupt idle or walking, don't break ongoing activities
        if self.state not in ("idle", "walking"):
            return
        self._start_activity(name)

    def interrupt(self, reaction):
        """Interrupt current activity for a reaction (click, hover, etc.)."""
        if reaction == "happy":
            self.state = "reaction_happy"
            self.state_timer = 0
            self.reaction_duration = 2000
            self.is_bouncing = True
            self.bounce_phase = 0
            self.current_message = t(random.choice(
                ["привет! :3", "о!", "рада тебя видеть", ":3"]
            ))
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
            # Personal phrases when attached
            from memory import Memory
            from settings import Settings
            from phrases import (PERSONAL_CLICK_PHRASES,
                                 PERSONAL_CLICK_PHRASES_NAMELESS)
            base_phrases = ["привет! :3", "о!", "рада тебя видеть", ":3", "♥"]
            name = Settings.shared().user_name
            if Memory.shared().is_attached():
                if name:
                    personal = random.choice(PERSONAL_CLICK_PHRASES)
                else:
                    personal = random.choice(PERSONAL_CLICK_PHRASES_NAMELESS)
                phrase = format_phrase(personal, name=name)
            else:
                phrase = t(random.choice(base_phrases))
            self.current_message = phrase
            self.events.append(("message", self.current_message))
            for _ in range(4):
                self.events.append(("particle", "sparkle"))
            for _ in range(3):
                self.events.append(("particle", "heart"))

        elif reaction == "wave":
            self.state = "reaction_wave"
            self.state_timer = 0
            self.reaction_duration = 1500
            self.current_message = t(random.choice(["хм?", "*машет*"]))
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
        if self.state in ("reaction_love", "reaction_happy_love",
                         "reaction_gift_received"):
            self.particle_timer += dt
            if self.particle_timer > 400:
                self.particle_timer = 0
                self.events.append(("particle", "heart"))
